# MarkItDown API

Esta é uma API RESTful para o MarkItDown, uma ferramenta para converter vários formatos de documentos para Markdown. Esta API permite que você converta documentos através de requisições HTTP.

## Recursos

- Converte vários formatos de documentos para Markdown através de uma API simples
- Suporta todos os formatos suportados pelo MarkItDown (PDF, DOCX, PPTX, XLSX, imagens, etc.)
- Retorna tanto o conteúdo Markdown quanto metadados extraídos
- Opções configuráveis para plugins e Azure Document Intelligence

## Como Executar

### Usando Docker Compose

A maneira mais fácil de executar a API é usando Docker Compose:

```bash
# Clone o repositório (se ainda não tiver feito)
git clone https://github.com/microsoft/markitdown.git
cd markitdown

# Inicie os serviços
docker-compose up -d
```

A API estará disponível em http://localhost:8000

### Verificando o Status

Para verificar se a API está funcionando corretamente:

```bash
curl http://localhost:8000/health
```

Deve retornar:

```json
{ "status": "healthy" }
```

### Verificando a Versão

Para verificar a versão da API e da biblioteca MarkItDown:

```bash
curl http://localhost:8000/version
```

Exemplo de resposta:

```json
{
  "api_version": "0.1.0",
  "markitdown_version": "0.1.1"
}
```

## Como Usar

### Convertendo um Documento

Você pode converter um documento usando o seguinte comando cURL:

```bash
curl -X POST "http://localhost:8000/convert" -F "file=@/caminho/para/documento.pdf"
```

### Opções Avançadas

A API suporta várias opções para controlar o processo de conversão:

```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@/caminho/para/documento.pdf" \
  -F "enable_plugins=true" \
  -F "use_docintel=true" \
  -F "docintel_endpoint=https://seu-endpoint.cognitiveservices.azure.com/"
```

### Cliente Python

Para facilitar o uso da API, incluímos um cliente Python de exemplo:

```bash
# No diretório do projeto
python api/test_client.py /caminho/para/documento.pdf --output resultado.md
```

Isso converterá o documento e salvará o resultado no arquivo `resultado.md`.

Para ver todas as opções disponíveis:

```bash
python api/test_client.py --help
```

## Tratamento de Erros

A API implementa estratégias robustas de tratamento de erros:

1. **Múltiplos métodos de conversão**: Tenta diferentes abordagens para converter documentos caso um método falhe.
2. **Logging detalhado**: Registra informações detalhadas sobre erros para facilitar o diagnóstico.
3. **Mensagens de erro claras**: Fornece mensagens de erro específicas e úteis.
4. **Códigos de status HTTP apropriados**: Usa códigos de status HTTP adequados para diferentes tipos de erro.

Exemplo de resposta de erro:

```json
{
  "detail": "Erro na conversão: o formato do arquivo não é suportado"
}
```

## Documentação da API

A API inclui documentação interativa, disponível em:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testando a API

Você pode executar os testes da API com:

```bash
# Certifique-se de que a API esteja rodando
docker-compose up -d

# Execute os testes
cd api
python -m pip install requests
python test_api.py
```

## Desenvolvimento

Para executar a API localmente sem Docker:

```bash
pip install fastapi uvicorn python-multipart pydantic markitdown[all]
cd api
python main.py
```

A API estará disponível em http://localhost:8000

## Integrações

Esta API pode ser facilmente integrada com outros sistemas que precisam converter documentos para Markdown, como:

- Sistemas de gerenciamento de conteúdo
- Ferramentas de processamento de documentos
- Aplicações de análise de texto
- Chatbots e assistentes baseados em IA
- Automação de documentação
