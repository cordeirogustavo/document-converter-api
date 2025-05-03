# MarkItDown API

Esta é uma API RESTful para o MarkItDown, uma ferramenta para converter vários formatos de documentos para Markdown. Esta API permite que você converta documentos através de requisições HTTP.

## Recursos

- Converte vários formatos de documentos para Markdown através de uma API simples
- Suporta todos os formatos suportados pelo MarkItDown (PDF, DOCX, PPTX, XLSX, imagens, etc.)
- Suporta conversão de URLs do YouTube para Markdown com transcrição do vídeo
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

### Convertendo um Vídeo do YouTube

Você pode extrair e converter a transcrição de um vídeo do YouTube usando o endpoint `/convert-youtube`:

```bash
curl -X POST "http://localhost:8000/convert-youtube" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "enable_plugins": false}'
```

#### Selecionando idiomas específicos

Para selecionar um idioma específico para a transcrição:

```bash
curl -X POST "http://localhost:8000/convert-youtube" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "language": "pt"}'
```

Você também pode fornecer uma lista ordenada de idiomas preferidos:

```bash
curl -X POST "http://localhost:8000/convert-youtube" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "language_list": ["pt-PT", "pt", "en"]}'
```

Para obter a lista completa de idiomas suportados:

```bash
curl "http://localhost:8000/youtube-languages"
```

A API validará os códigos de idioma solicitados e retornará sugestões caso o código fornecido não seja encontrado.

Exemplo de resposta bem-sucedida:

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "markdown_content": "# Rick Astley - Never Gonna Give You Up\n\nNever gonna give you up\nNever gonna let you down\nNever gonna run around and desert you...",
  "metadata": {
    "title": "Rick Astley - Never Gonna Give You Up (Official Music Video)",
    "language": "en",
    "language_name": "English",
    "duration": "3:33",
    "author": "Rick Astley"
  }
}
```

### Obtendo Transcrições Diretamente do YouTube

Se você precisa apenas da transcrição do vídeo (e não da conversão completa do MarkItDown), você pode usar o endpoint especializado `/youtube-transcript`:

```bash
curl -X POST "http://localhost:8000/youtube-transcript" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

Este endpoint utiliza diretamente a biblioteca `youtube-transcript-api` para extrair as legendas, formatando-as em Markdown de forma otimizada para leitura. O endpoint agora detecta automaticamente o idioma original do vídeo e o utiliza por padrão, a menos que você especifique um idioma diferente.

Você também pode solicitar um idioma específico:

```bash
curl -X POST "http://localhost:8000/youtube-transcript" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "language": "pt"}'
```

Se o idioma solicitado não estiver disponível, você receberá uma mensagem de erro informativa com sugestões dos idiomas disponíveis para esse vídeo.

O resultado inclui metadados detalhados sobre o vídeo e as legendas disponíveis:

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "video_id": "dQw4w9WgXcQ",
  "markdown_content": "# Transcrição do YouTube\n\n## Rick Astley - Never Gonna Give You Up\n\n*Official Video - 4K - Listen On Spotify...*\n\n- **Canal:** Rick Astley\n- **Duração:** 3:33\n- **Idioma da transcrição:** en (English)\n- **Idioma original do vídeo:** en (English)\n\n### Conteúdo\n\nWe're no strangers to love You know the rules and so do I...",
  "metadata": {
    "available_languages": [
      {
        "code": "en",
        "name": "English",
        "is_generated": false,
        "is_translatable": true
      },
      {
        "code": "pt",
        "name": "Portuguese",
        "is_generated": true,
        "is_translatable": false
      }
    ],
    "language_used": "en",
    "language_name": "English",
    "original_language": "en",
    "original_language_name": "English",
    "original_language_is_manual": true,
    "title": "Rick Astley - Never Gonna Give You Up (Official Music Video)",
    "author": "Rick Astley",
    "length_seconds": 212
  }
}
```

O sistema diferencia entre legendas manuais (criadas por humanos) e legendas geradas automaticamente pelo YouTube, priorizando sempre as legendas manuais quando disponíveis.

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
pip install fastapi uvicorn python-multipart pydantic "markitdown[all,youtube-transcription]" youtube-transcript-api
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
