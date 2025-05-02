from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import io
import os
import logging
import importlib.metadata
from markitdown import MarkItDown
import uvicorn
from pydantic import BaseModel

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Verificar versão da biblioteca MarkItDown
try:
    markitdown_version = importlib.metadata.version("markitdown")
    logger.info(f"Usando MarkItDown versão: {markitdown_version}")
except Exception as e:
    logger.warning(f"Não foi possível determinar a versão do MarkItDown: {str(e)}")
    markitdown_version = "desconhecida"

app = FastAPI(
    title="MarkItDown API",
    description="API for converting various document formats to Markdown",
    version="0.1.0",
)

# Expor a versão da biblioteca na API
@app.get("/version")
async def get_version():
    """Retorna a versão da API e da biblioteca MarkItDown."""
    return {
        "api_version": "0.1.0",
        "markitdown_version": markitdown_version
    }

# Initialize global MarkItDown instance with default settings
default_md = MarkItDown(enable_plugins=False)

class ConversionOptions(BaseModel):
    enable_plugins: bool = False
    use_docintel: bool = False
    docintel_endpoint: Optional[str] = None
    llm_description: bool = False

def get_markitdown(options: Optional[ConversionOptions] = None):
    """
    Factory function to create a MarkItDown instance with the specified options.
    """
    if options is None:
        return default_md
    
    # Create a new instance with the specified options
    md = MarkItDown(
        enable_plugins=options.enable_plugins,
        docintel_endpoint=options.docintel_endpoint if options.use_docintel else None,
        # Add more options as needed
    )
    return md

@app.get("/")
async def root():
    return {"message": "Welcome to MarkItDown API. Use /convert to convert documents."}

@app.post("/convert")
async def convert_document(
    file: UploadFile = File(...),
    enable_plugins: bool = Form(False),
    use_docintel: bool = Form(False),
    docintel_endpoint: Optional[str] = Form(None),
    llm_description: bool = Form(False),
):
    """
    Converte um documento enviado para formato Markdown.
    Suporta vários formatos, incluindo PDF, DOCX, PPTX, XLSX, imagens e outros.
    
    - **file**: O documento a ser convertido
    - **enable_plugins**: Se deve habilitar plugins (padrão: False)
    - **use_docintel**: Se deve usar Azure Document Intelligence (padrão: False)
    - **docintel_endpoint**: Endpoint do Azure Document Intelligence (obrigatório se use_docintel for True)
    - **llm_description**: Se deve usar LLM para descrições de imagens (não implementado nesta versão básica)
    
    Nota: A detecção do tipo de arquivo é baseada no conteúdo do arquivo. O nome do arquivo 
    é usado como metadado quando possível, mas pode não ser considerado para todos os formatos.
    """
    temp_path = None
    
    try:
        # Create options
        options = ConversionOptions(
            enable_plugins=enable_plugins,
            use_docintel=use_docintel,
            docintel_endpoint=docintel_endpoint,
            llm_description=llm_description
        )
        
        # Validate options
        if use_docintel and not docintel_endpoint:
            raise HTTPException(status_code=400, detail="docintel_endpoint is required when use_docintel is True")
        
        # Get MarkItDown instance
        md = get_markitdown(options)
        
        # Read the file content
        contents = await file.read()
        file_obj = io.BytesIO(contents)
        
        # Get the original filename (just for metadata)
        filename = file.filename
        
        # Log information
        logger.info(f"Processando arquivo: {filename}, tamanho: {len(contents)} bytes")
        logger.info(f"Versão do MarkItDown: {markitdown_version}")
        
        # Tenta cada método de conversão em ordem
        methods = [
            # 1. Tentativa: convert_stream diretamente
            lambda: try_convert_stream(md, file_obj, filename),
            
            # 2. Tentativa: Usar um arquivo temporário com convert
            lambda: try_with_temp_file(md, file_obj, filename),
            
            # 3. Tentativa: Tentar importar o método interno que convert usa
            lambda: try_advanced_method(md, file_obj, filename)
        ]
        
        result = None
        for method_number, method in enumerate(methods, 1):
            try:
                logger.info(f"Tentando método de conversão #{method_number}")
                result = method()
                if result:
                    logger.info(f"Método #{method_number} bem-sucedido!")
                    break
            except Exception as e:
                logger.warning(f"Método #{method_number} falhou: {str(e)}")
                if method_number == len(methods):
                    # Se for o último método, reraise
                    raise
        
        if result:
            # Inspecionar o objeto de resultado para documentação
            result_type = type(result).__name__
            available_attrs = dir(result)
            
            logger.info(f"Tipo do objeto de resultado: {result_type}")
            logger.info(f"Atributos disponíveis: {available_attrs}")
            
            # Return the markdown content
            # Garantimos que o objeto tenha text_content ou tentamos alternativas
            if hasattr(result, "text_content"):
                content = result.text_content
            elif hasattr(result, "text"):
                content = result.text
            elif hasattr(result, "content"):
                content = result.content
            elif hasattr(result, "markdown"):
                content = result.markdown
            else:
                # Último recurso: tentar converter o próprio resultado para string
                content = str(result)
                
            logger.info(f"Convertido com sucesso. Tamanho do conteúdo: {len(content)} caracteres")
            
            # Construir resposta com os atributos encontrados
            response_data = {
                "filename": filename,
                "markdown_content": content
            }
            
            # Adiciona todos os atributos extras que possam existir para metadados
            metadata = {}
            for attr in available_attrs:
                # Ignora atributos mágicos, métodos e atributos já incluídos
                if (not attr.startswith('__') and 
                    not callable(getattr(result, attr)) and 
                    attr != "text_content" and
                    attr != "text" and
                    attr != "content" and
                    attr != "markdown"):
                    try:
                        # Tenta obter o valor e verificar se é serializável
                        value = getattr(result, attr)
                        # Tenta converter para string se não for um tipo básico
                        if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                            value = str(value)
                        metadata[attr] = value
                    except:
                        # Ignora atributos que não podem ser acessados
                        pass
            
            response_data["metadata"] = metadata            
            return JSONResponse(content=response_data)
        else:
            raise Exception("Nenhum método de conversão foi bem-sucedido")
    
    except Exception as e:
        # Log detalhado do erro para diagnóstico
        logger.error(f"Erro ao converter documento: {str(e)}", exc_info=True)
        
        # Mensagens de erro personalizadas para diferentes situações
        if isinstance(e, TypeError) and "convert_stream() takes" in str(e):
            detail = "A API do MarkItDown mudou em relação ao esperado. Verifique se está usando a versão suportada."
        elif "No converter found" in str(e):
            detail = f"Formato de arquivo não suportado ou não reconhecido: {filename}"
        elif "Permission denied" in str(e):
            detail = "Erro de permissão ao acessar o arquivo"
        else:
            detail = f"Erro ao converter o documento: {str(e)}"
            
        # Adiciona versão para diagnóstico
        detail += f" (MarkItDown v{markitdown_version})"
        
        # Retorna o erro HTTP
        raise HTTPException(status_code=500, detail=detail)
    finally:
        # Garantir que qualquer arquivo temporário seja excluído
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.info(f"Arquivo temporário removido: {temp_path}")
            except Exception as e:
                logger.warning(f"Erro ao remover arquivo temporário: {str(e)}")

def try_convert_stream(md, file_obj, filename):
    """Tenta usar convert_stream diretamente."""
    # Certifique-se de que o ponteiro está no início do arquivo
    file_obj.seek(0)
    
    # Adiciona o nome do arquivo como metadado do stream
    try:
        file_obj.name = filename
    except:
        pass
        
    # Usa o método convert_stream
    logger.info("Tentando convert_stream com apenas o objeto BytesIO")
    return md.convert_stream(file_obj)

def try_with_temp_file(md, file_obj, filename):
    """Cria um arquivo temporário e usa convert."""
    import tempfile
    import os
    
    logger.info("Criando arquivo temporário para conversão alternativa")
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
        temp_path = temp_file.name
        # Copia o conteúdo para o arquivo temporário
        file_obj.seek(0)
        temp_file.write(file_obj.read())
    
    try:
        # Usa md.convert com o arquivo temporário
        logger.info(f"Tentando converter usando arquivo temporário: {temp_path}")
        return md.convert(temp_path)
    finally:
        # Limpa o arquivo temporário independentemente do resultado
        try:
            os.unlink(temp_path)
        except Exception as e:
            logger.warning(f"Erro ao remover arquivo temporário: {str(e)}")

def try_advanced_method(md, file_obj, filename):
    """Tenta usar uma terceira abordagem para conversão."""
    logger.info("Tentando abordagem avançada")
    
    try:
        # Inspecionar o objeto MarkItDown
        logger.info(f"Métodos disponíveis no objeto MarkItDown: {dir(md)}")
        
        # Examinar a assinatura dos métodos
        import inspect
        try:
            logger.info(f"Assinatura de convert_stream: {inspect.signature(md.convert_stream)}")
        except:
            logger.info("Não foi possível obter a assinatura de convert_stream")
            
        try:
            logger.info(f"Assinatura de convert: {inspect.signature(md.convert)}")
        except:
            logger.info("Não foi possível obter a assinatura de convert")
        
        # Tenta usar a forma como a linha de comando do MarkItDown usa
        file_obj.seek(0)
        file_extension = os.path.splitext(filename)[1].lower()
        logger.info(f"Tentando conversão para extensão: {file_extension}")
        
        # Tenta usar diretamente o método convert para arquivos binários
        try:
            result = md.convert(file_obj)
            logger.info("Conversão direta com md.convert(file_obj) bem-sucedida")
            return result
        except Exception as e1:
            logger.warning(f"Falha ao converter diretamente com file_obj: {str(e1)}")
            
            # Tenta outra abordagem se disponível
            if hasattr(md, "_convert_file_like"):
                logger.info("Tentando método _convert_file_like")
                file_obj.seek(0)
                return md._convert_file_like(file_obj)
                
    except Exception as e:
        logger.warning(f"Abordagem avançada falhou: {str(e)}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False) 