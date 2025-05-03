from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict
import io
import os
import logging
import importlib.metadata
from markitdown import MarkItDown
import uvicorn
from pydantic import BaseModel, HttpUrl
import re

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Lista de idiomas suportados para transcrição do YouTube
SUPPORTED_LANGUAGES: Dict[str, str] = {
    "ab": "Abkhazian",
    "aa": "Afar",
    "af": "Afrikaans",
    "ak": "Akan",
    "sq": "Albanian",
    "am": "Amharic",
    "ar": "Arabic",
    "hy": "Armenian",
    "as": "Assamese",
    "ay": "Aymara",
    "az": "Azerbaijani",
    "bn": "Bangla",
    "ba": "Bashkir",
    "eu": "Basque",
    "be": "Belarusian",
    "bho": "Bhojpuri",
    "bs": "Bosnian",
    "br": "Breton",
    "bg": "Bulgarian",
    "my": "Burmese",
    "ca": "Catalan",
    "ceb": "Cebuano",
    "zh-Hans": "Chinese (Simplified)",
    "zh-Hant": "Chinese (Traditional)",
    "co": "Corsican",
    "hr": "Croatian",
    "cs": "Czech",
    "da": "Danish",
    "dv": "Divehi",
    "nl": "Dutch",
    "dz": "Dzongkha",
    "en": "English",
    "eo": "Esperanto",
    "et": "Estonian",
    "ee": "Ewe",
    "fo": "Faroese",
    "fj": "Fijian",
    "fil": "Filipino",
    "fi": "Finnish",
    "fr": "French",
    "gaa": "Ga",
    "gl": "Galician",
    "lg": "Ganda",
    "ka": "Georgian",
    "de": "German",
    "el": "Greek",
    "gn": "Guarani",
    "gu": "Gujarati",
    "ht": "Haitian Creole",
    "ha": "Hausa",
    "haw": "Hawaiian",
    "iw": "Hebrew",
    "hi": "Hindi",
    "hmn": "Hmong",
    "hu": "Hungarian",
    "is": "Icelandic",
    "ig": "Igbo",
    "id": "Indonesian",
    "iu": "Inuktitut",
    "ga": "Irish",
    "it": "Italian",
    "ja": "Japanese",
    "jv": "Javanese",
    "kl": "Kalaallisut",
    "kn": "Kannada",
    "kk": "Kazakh",
    "kha": "Khasi",
    "km": "Khmer",
    "rw": "Kinyarwanda",
    "ko": "Korean",
    "kri": "Krio",
    "ku": "Kurdish",
    "ky": "Kyrgyz",
    "lo": "Lao",
    "la": "Latin",
    "lv": "Latvian",
    "ln": "Lingala",
    "lt": "Lithuanian",
    "lua": "Luba-Lulua",
    "luo": "Luo",
    "lb": "Luxembourgish",
    "mk": "Macedonian",
    "mg": "Malagasy",
    "ms": "Malay",
    "ml": "Malayalam",
    "mt": "Maltese",
    "gv": "Manx",
    "mi": "Māori",
    "mr": "Marathi",
    "mn": "Mongolian",
    "mfe": "Morisyen",
    "ne": "Nepali",
    "new": "Newari",
    "nso": "Northern Sotho",
    "no": "Norwegian",
    "ny": "Nyanja",
    "oc": "Occitan",
    "or": "Odia",
    "om": "Oromo",
    "os": "Ossetic",
    "pam": "Pampanga",
    "ps": "Pashto",
    "fa": "Persian",
    "pl": "Polish",
    "pt": "Portuguese",
    "pt-PT": "Portuguese (Portugal)",
    "pa": "Punjabi",
    "qu": "Quechua",
    "ro": "Romanian",
    "rn": "Rundi",
    "ru": "Russian",
    "sm": "Samoan",
    "sg": "Sango",
    "sa": "Sanskrit",
    "gd": "Scottish Gaelic",
    "sr": "Serbian",
    "crs": "Seselwa Creole French",
    "sn": "Shona",
    "sd": "Sindhi",
    "si": "Sinhala",
    "sk": "Slovak",
    "sl": "Slovenian",
    "so": "Somali",
    "st": "Southern Sotho",
    "es": "Spanish",
    "su": "Sundanese",
    "sw": "Swahili",
    "ss": "Swati",
    "sv": "Swedish",
    "tg": "Tajik",
    "ta": "Tamil",
    "tt": "Tatar",
    "te": "Telugu",
    "th": "Thai",
    "bo": "Tibetan",
    "ti": "Tigrinya",
    "to": "Tongan",
    "ts": "Tsonga",
    "tn": "Tswana",
    "tum": "Tumbuka",
    "tr": "Turkish",
    "tk": "Turkmen",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "ug": "Uyghur",
    "uz": "Uzbek",
    "ve": "Venda",
    "vi": "Vietnamese",
    "war": "Waray",
    "cy": "Welsh",
    "fy": "Western Frisian",
    "wo": "Wolof",
    "xh": "Xhosa",
    "yi": "Yiddish",
    "yo": "Yoruba",
    "zu": "Zulu"
}

# Gerados automaticamente
AUTO_GENERATED_LANGUAGES: Dict[str, str] = {
    "pt": "Portuguese (auto-generated)"
}

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
    version="0.1.2",
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

class YouTubeConversionRequest(BaseModel):
    url: HttpUrl
    enable_plugins: bool = False
    language: Optional[str] = None
    language_list: Optional[List[str]] = None

class YouTubeTranscriptRequest(BaseModel):
    url: HttpUrl
    language: Optional[str] = None
    language_list: Optional[List[str]] = None

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

@app.post("/convert-youtube")
async def convert_youtube_url(request: YouTubeConversionRequest):
    """
    Converte uma URL do YouTube para Markdown extraindo sua transcrição.
    
    - **url**: URL do vídeo do YouTube a ser convertido
    - **enable_plugins**: Se deve habilitar plugins (padrão: False)
    - **language**: Idioma específico para a transcrição (ex: 'pt', 'en', 'es')
    - **language_list**: Lista ordenada de idiomas preferidos (ex: ['pt-BR', 'pt', 'en'])
    
    Se tanto language quanto language_list forem fornecidos, language tem prioridade.
    Se nenhum for fornecido, será usado o idioma padrão do vídeo.
    
    Retorna a transcrição do vídeo em formato Markdown.
    """
    try:
        # Log da solicitação
        logger.info(f"Processando URL do YouTube: {request.url}")
        
        # Validar idioma solicitado
        all_languages = {**SUPPORTED_LANGUAGES, **AUTO_GENERATED_LANGUAGES}
        
        # Verificar se o idioma solicitado é válido
        if request.language and request.language not in all_languages:
            idiomas_similares = [code for code in all_languages.keys() 
                                if request.language.lower() in code.lower() or 
                                request.language.lower() in all_languages[code].lower()]
            if idiomas_similares:
                sugestoes = ", ".join(f"'{code}' ({all_languages[code]})" for code in idiomas_similares[:5])
                raise HTTPException(
                    status_code=400,
                    detail=f"Idioma '{request.language}' não é suportado. Talvez você quis dizer: {sugestoes}"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Idioma '{request.language}' não é suportado. Use /youtube-languages para ver os idiomas disponíveis."
                )
        
        # Verificar se os idiomas na lista são válidos
        if request.language_list:
            invalid_langs = [lang for lang in request.language_list if lang not in all_languages]
            if invalid_langs:
                raise HTTPException(
                    status_code=400,
                    detail=f"Os seguintes idiomas não são suportados: {', '.join(invalid_langs)}. Use /youtube-languages para ver os idiomas disponíveis."
                )
        
        # Log dos idiomas solicitados
        if request.language:
            idioma_nome = all_languages.get(request.language, request.language)
            logger.info(f"Idioma solicitado: {request.language} ({idioma_nome})")
        elif request.language_list:
            idiomas_nomes = [f"{lang} ({all_languages.get(lang, lang)})" for lang in request.language_list]
            logger.info(f"Lista de idiomas: {', '.join(idiomas_nomes)}")
        else:
            logger.info(f"Usando idioma padrão do vídeo")
        
        # Criar instância do MarkItDown com as opções especificadas
        md = MarkItDown(enable_plugins=request.enable_plugins)
        
        # Preparar kwargs extras para a conversão
        convert_kwargs = {}
        
        # Adicionar configurações de idioma se fornecidas
        if request.language:
            convert_kwargs['language'] = request.language
        elif request.language_list:
            convert_kwargs['language_list'] = request.language_list
            
        logger.info(f"Parâmetros adicionais para conversão: {convert_kwargs}")
        
        # Converter a URL do YouTube usando o MarkItDown com os parâmetros específicos
        result = md.convert(str(request.url), **convert_kwargs)
        
        # Verificar se a conversão foi bem-sucedida
        if not result or not hasattr(result, 'text_content'):
            raise HTTPException(
                status_code=500, 
                detail="Não foi possível extrair conteúdo da URL do YouTube"
            )
        
        # Log do sucesso
        content_length = len(result.text_content) if hasattr(result, 'text_content') else 0
        logger.info(f"URL do YouTube convertida com sucesso. Tamanho do conteúdo: {content_length} caracteres")
        
        # Determinar o idioma utilizado (se disponível)
        idioma_utilizado = None
        if hasattr(result, 'language'):
            idioma_utilizado = result.language
            logger.info(f"Idioma utilizado na transcrição: {idioma_utilizado}")
        
        # Construir resposta
        # Tentar extrair metadados disponíveis
        metadata = {}
        for attr in dir(result):
            if (not attr.startswith('__') and 
                not callable(getattr(result, attr)) and 
                attr != "text_content"):
                try:
                    value = getattr(result, attr)
                    if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        value = str(value)
                    metadata[attr] = value
                except:
                    pass
        
        # Adicionar idioma utilizado nos metadados se não estiver já incluído
        if idioma_utilizado and 'language' not in metadata:
            metadata['language'] = idioma_utilizado
            if idioma_utilizado in all_languages:
                metadata['language_name'] = all_languages[idioma_utilizado]
        
        # Retornar o conteúdo markdown
        return JSONResponse(content={
            "url": str(request.url),
            "markdown_content": result.text_content,
            "metadata": metadata
        })
        
    except Exception as e:
        # Log detalhado do erro
        logger.error(f"Erro ao converter URL do YouTube: {str(e)}", exc_info=True)
        
        # Não reenviar exceção HTTP
        if isinstance(e, HTTPException):
            raise e
        
        # Personalizar mensagem de erro com base no tipo
        if "youtube_dl" in str(e).lower() or "pytube" in str(e).lower():
            detail = f"Erro ao extrair informações do YouTube: {str(e)}. Verifique se todas as dependências estão instaladas com 'pip install markitdown[youtube-transcription]'"
        elif "language" in str(e).lower():
            detail = f"Erro relacionado ao idioma: {str(e)}. Use /youtube-languages para ver os idiomas disponíveis."
        else:
            detail = f"Erro ao processar URL do YouTube: {str(e)}"
            
        # Adicionar versão para diagnóstico
        detail += f" (MarkItDown v{markitdown_version})"
        
        # Retornar erro
        raise HTTPException(status_code=500, detail=detail)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/youtube-languages")
async def get_youtube_languages():
    """
    Retorna a lista de idiomas suportados para transcrição de vídeos do YouTube.
    
    O resultado contém duas categorias:
    - translation_languages: Idiomas disponíveis para tradução
    - auto_generated: Idiomas disponíveis com transcrição gerada automaticamente
    """
    return {
        "translation_languages": SUPPORTED_LANGUAGES,
        "auto_generated": AUTO_GENERATED_LANGUAGES
    }

def extract_video_id(url: str) -> str:
    """Extrai o ID do vídeo do YouTube a partir da URL."""
    # Padrões comuns de URLs do YouTube
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',  # URLs normais e incorporadas
        r'(?:embed\/|v\/|youtu.be\/)([0-9A-Za-z_-]{11}).*'  # URLs encurtadas
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    raise ValueError(f"Não foi possível extrair o ID do vídeo da URL: {url}")

@app.post("/youtube-transcript")
async def get_youtube_transcript(request: YouTubeTranscriptRequest):
    """
    Obtém a transcrição de um vídeo do YouTube diretamente.
    
    Este endpoint usa a biblioteca youtube_transcript_api para extrair a transcrição,
    sem depender do processamento do MarkItDown.
    
    - **url**: URL do vídeo do YouTube
    - **language**: Idioma específico para a transcrição (ex: 'pt', 'en', 'es')
    - **language_list**: Lista ordenada de idiomas preferidos (ex: ['pt-PT', 'pt', 'en'])
    
    Se tanto language quanto language_list forem fornecidos, language tem prioridade.
    Se nenhum for fornecido, será usado o idioma original do vídeo.
    
    Retorna a transcrição do vídeo em formato Markdown.
    """
    try:
        # Importação de biblioteca aqui para não quebrar se não estiver instalada
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="Biblioteca 'youtube_transcript_api' não está instalada. Execute 'pip install youtube-transcript-api'."
            )
        
        # Log da solicitação
        logger.info(f"Processando transcrição direta da URL do YouTube: {request.url}")
        
        # Validar idioma solicitado
        all_languages = {**SUPPORTED_LANGUAGES, **AUTO_GENERATED_LANGUAGES}
        
        # Verificar se o idioma solicitado é válido
        if request.language and request.language not in all_languages:
            idiomas_similares = [code for code in all_languages.keys() 
                                if request.language.lower() in code.lower() or 
                                request.language.lower() in all_languages[code].lower()]
            if idiomas_similares:
                sugestoes = ", ".join(f"'{code}' ({all_languages[code]})" for code in idiomas_similares[:5])
                raise HTTPException(
                    status_code=400,
                    detail=f"Idioma '{request.language}' não é suportado. Talvez você quis dizer: {sugestoes}"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Idioma '{request.language}' não é suportado. Use /youtube-languages para ver os idiomas disponíveis."
                )
        
        # Verificar se os idiomas na lista são válidos
        if request.language_list:
            invalid_langs = [lang for lang in request.language_list if lang not in all_languages]
            if invalid_langs:
                raise HTTPException(
                    status_code=400,
                    detail=f"Os seguintes idiomas não são suportados: {', '.join(invalid_langs)}. Use /youtube-languages para ver os idiomas disponíveis."
                )
        
        # Extrair ID do vídeo
        video_id = extract_video_id(str(request.url))
        logger.info(f"ID do vídeo extraído: {video_id}")
        
        # Identificar o idioma original do vídeo
        original_language = None
        original_language_is_manual = False
        available_languages = []
        
        try:
            # Listar todas as transcrições disponíveis
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Armazenar informações sobre todas as legendas disponíveis
            manual_transcripts = []  # Legendas manuais (não geradas automaticamente)
            generated_transcripts = []  # Legendas geradas automaticamente
            
            for transcript in transcript_list:
                lang_code = transcript.language_code
                is_generated = transcript.is_generated
                is_translatable = transcript.is_translatable
                
                lang_info = {
                    "code": lang_code,
                    "name": all_languages.get(lang_code, "Desconhecido"),
                    "is_generated": is_generated,
                    "is_translatable": is_translatable
                }
                
                available_languages.append(lang_info)
                
                # Separar entre legendas manuais e geradas automaticamente
                if is_generated:
                    generated_transcripts.append(lang_info)
                else:
                    manual_transcripts.append(lang_info)
                    
                # Detectar se esta é a legendagem original
                if hasattr(transcript, 'is_original') and transcript.is_original:
                    original_language = lang_code
                    original_language_is_manual = not is_generated
                
            # Se não conseguiu detectar a original pela propriedade, identificar por heurística
            if not original_language:
                # Preferir legendas manuais primeiro
                if manual_transcripts:
                    # Se houver legenda manual, considerar a primeira como original
                    original_language = manual_transcripts[0]["code"]
                    original_language_is_manual = True
                elif generated_transcripts:
                    # Se só houver legendas geradas automaticamente, usar a primeira
                    original_language = generated_transcripts[0]["code"]
                    original_language_is_manual = False
                    
            logger.info(f"Idioma original identificado: {original_language} (manual: {original_language_is_manual})")
            logger.info(f"Legendas disponíveis: {len(available_languages)}")
            
        except Exception as e:
            logger.warning(f"Erro ao listar legendas disponíveis: {str(e)}")
        
        # Log dos idiomas solicitados
        if request.language:
            idioma_nome = all_languages.get(request.language, request.language)
            logger.info(f"Idioma solicitado pelo usuário: {request.language} ({idioma_nome})")
        elif request.language_list:
            idiomas_nomes = [f"{lang} ({all_languages.get(lang, lang)})" for lang in request.language_list]
            logger.info(f"Lista de idiomas solicitada pelo usuário: {', '.join(idiomas_nomes)}")
        elif original_language:
            logger.info(f"Usando idioma original do vídeo: {original_language} ({all_languages.get(original_language, 'Desconhecido')})")
        else:
            logger.info(f"Nenhum idioma específico identificado, usando padrão do sistema")
        
        # Tentar obter a transcrição no idioma solicitado ou original
        try:
            language_used = None
            
            if request.language:
                # Usar o idioma especificado pelo usuário
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[request.language])
                language_used = request.language
                logger.info(f"Usando idioma solicitado: {language_used}")
                
            elif request.language_list:
                # Tentar cada idioma da lista na ordem
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=request.language_list)
                
                # Determinar qual idioma foi realmente usado
                for lang in request.language_list:
                    try:
                        test = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                        if test:
                            language_used = lang
                            logger.info(f"Encontrado idioma da lista: {language_used}")
                            break
                    except:
                        continue
                
                if not language_used:
                    language_used = "desconhecido"
                    logger.warning(f"Não foi possível determinar qual idioma da lista foi usado")
                    
            elif original_language:
                # Usar o idioma original do vídeo
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[original_language])
                language_used = original_language
                logger.info(f"Usando idioma original do vídeo: {language_used}")
                
            else:
                # Último recurso: deixar a API escolher o idioma padrão
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                
                # Tentar descobrir qual idioma foi usado
                try:
                    # Tentar obter uma amostra da transcrição e identificar o idioma
                    sample_transcript = transcript[0]['text'] if transcript else ""
                    logger.info(f"Amostra de texto: {sample_transcript[:100]}")
                    
                    # Verificar se corresponde a alguma transcrição que conhecemos
                    for lang_info in available_languages:
                        try:
                            test_trans = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang_info['code']])
                            if test_trans and test_trans[0]['text'] == sample_transcript:
                                language_used = lang_info['code']
                                logger.info(f"Idioma identificado pela amostra: {language_used}")
                                break
                        except:
                            continue
                except:
                    pass
                
                if not language_used:
                    language_used = "desconhecido"
                    logger.warning(f"Não foi possível determinar o idioma usado")
        
        except Exception as e:
            logger.error(f"Erro ao obter transcrição: {str(e)}")
            
            # Mensagem de erro mais informativa
            detail = f"Não foi possível obter a transcrição para este vídeo."
            
            if original_language:
                detail += f" Idioma original do vídeo: {original_language}"
                if available_languages:
                    langs_disponiveis = ", ".join([f"{l['code']} ({l['name']})" for l in available_languages[:5]])
                    detail += f". Idiomas disponíveis: {langs_disponiveis}"
                    if len(available_languages) > 5:
                        detail += f" e mais {len(available_languages)-5}."
            
            detail += f" Erro: {str(e)}"
            
            raise HTTPException(
                status_code=404,
                detail=detail
            )
        
        # Converter para markdown
        markdown_content = "# Transcrição do YouTube\n\n"
        
        # Adicionar metadados
        try:
            from pytube import YouTube
            yt = YouTube(str(request.url))
            markdown_content += f"## {yt.title}\n\n"
            
            if yt.description:
                short_description = yt.description.split('\n')[0]  # Pegar só a primeira linha
                markdown_content += f"*{short_description}*\n\n"
                
            markdown_content += f"- **Canal:** {yt.author}\n"
            if yt.length:
                minutes = yt.length // 60
                seconds = yt.length % 60
                markdown_content += f"- **Duração:** {minutes}:{seconds:02d}\n"
                
            markdown_content += f"- **Idioma da transcrição:** {language_used}"
            if language_used in all_languages:
                markdown_content += f" ({all_languages[language_used]})"
            markdown_content += "\n\n"
            
            if original_language and original_language != language_used:
                markdown_content += f"- **Idioma original do vídeo:** {original_language}"
                if original_language in all_languages:
                    markdown_content += f" ({all_languages[original_language]})"
                markdown_content += "\n\n"
                
        except Exception as e:
            logger.warning(f"Erro ao obter metadados do vídeo: {str(e)}")
            markdown_content += "## Transcrição\n\n"
        
        # Adicionar o conteúdo da transcrição
        markdown_content += "### Conteúdo\n\n"
        
        current_time = 0
        paragraph_text = ""
        
        # Agrupar textos próximos em parágrafos (dentro de 2 segundos)
        for item in transcript:
            text = item['text']
            start = item['start']
            
            # Se o tempo for muito distante do anterior, iniciar novo parágrafo
            if start - current_time > 2.0 and paragraph_text:
                markdown_content += paragraph_text.strip() + "\n\n"
                paragraph_text = ""
            
            # Adicionar o texto atual
            paragraph_text += text + " "
            current_time = start
        
        # Adicionar o último parágrafo
        if paragraph_text:
            markdown_content += paragraph_text.strip()
        
        # Preparar resposta
        response_data = {
            "url": str(request.url),
            "video_id": video_id,
            "markdown_content": markdown_content,
            "metadata": {
                "available_languages": available_languages,
                "language_used": language_used,
                "language_name": all_languages.get(language_used, "Desconhecido") if language_used else "Desconhecido",
                "original_language": original_language,
                "original_language_name": all_languages.get(original_language, "Desconhecido") if original_language else "Desconhecido",
                "original_language_is_manual": original_language_is_manual
            }
        }
        
        # Se temos metadados do pytube, incluir
        try:
            response_data["metadata"]["title"] = yt.title
            response_data["metadata"]["author"] = yt.author
            response_data["metadata"]["length_seconds"] = yt.length
        except:
            pass
            
        return JSONResponse(content=response_data)
        
    except Exception as e:
        # Log detalhado do erro
        logger.error(f"Erro ao processar transcrição do YouTube: {str(e)}", exc_info=True)
        
        # Não reenviar exceção HTTP
        if isinstance(e, HTTPException):
            raise e
        
        # Personalizar mensagem de erro
        if "Could not retrieve a transcript" in str(e):
            raise HTTPException(
                status_code=404,
                detail="Não foi possível encontrar legendas para este vídeo. É possível que o vídeo não tenha legendas disponíveis."
            )
        
        detail = f"Erro ao processar transcrição do YouTube: {str(e)}"
        raise HTTPException(status_code=500, detail=detail)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False) 