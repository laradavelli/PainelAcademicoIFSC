@echo off
REM ── Script de inicialização para Windows ──
REM Requer Docker Desktop instalado

echo ============================================
echo   Painel Academico - Iniciando...
echo ============================================
echo.

docker compose up --build -d

echo.
echo Aplicacao iniciada com sucesso!
echo Acesse: http://localhost:8501
echo.
echo Para parar: docker compose down
pause
