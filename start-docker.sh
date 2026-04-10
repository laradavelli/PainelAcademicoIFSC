#!/bin/bash
# ── Script de inicialização via Docker (macOS/Linux) ──

set -e

echo "============================================"
echo "  Painel Acadêmico - Iniciando..."
echo "============================================"
echo ""

# Verifica se Docker está disponível
if ! command -v docker &> /dev/null; then
    echo "ERRO: Docker não encontrado."
    echo "Instale em: https://docs.docker.com/get-docker/"
    exit 1
fi

docker compose up --build -d

echo ""
echo "Aplicação iniciada com sucesso!"
echo "Acesse: http://localhost:8501"
echo ""
echo "Para parar: docker compose down"
