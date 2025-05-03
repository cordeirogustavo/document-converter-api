FROM python:3.10-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive
ENV EXIFTOOL_PATH=/usr/bin/exiftool
ENV FFMPEG_PATH=/usr/bin/ffmpeg

# Runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    exiftool \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy API code
COPY . /app

# Instalar dependências específicas para transcrição do YouTube
RUN pip --no-cache-dir install youtube-transcript-api

# Install dependencies
RUN pip --no-cache-dir install \
    fastapi \
    uvicorn \
    python-multipart \
    pydantic \
    markitdown[all,youtube-transcription]

# Default port
ENV PORT=8000

# Expose the port
EXPOSE ${PORT}

# Create a non-root user to run the application
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Run API
CMD ["python", "main.py"] 