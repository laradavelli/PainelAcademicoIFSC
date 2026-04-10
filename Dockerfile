# ── Estágio 1: imagem base com dependências ──
FROM python:3.12-slim AS base

# Evita prompts interativos e buffers no stdout
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências do sistema (necessárias para compilação de pacotes)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python primeiro (cache de camadas Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Estágio 2: copia código da aplicação ──
FROM base AS app

WORKDIR /app

# Copia todo o projeto
COPY . .

# Porta padrão do Streamlit
EXPOSE 8501

# Healthcheck para verificar se o Streamlit está respondendo
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

# Comando de inicialização
ENTRYPOINT ["streamlit", "run", "app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--browser.gatherUsageStats=false"]
