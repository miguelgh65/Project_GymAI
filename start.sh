#!/bin/bash
echo "Iniciando servicios..."

# Iniciar el bot de Telegram en segundo plano
echo "Iniciando Bot de Telegram..."
cd /app/telegram/gym
python main.py &
TELEGRAM_PID=$!

# Iniciar la aplicación FastAPI con uvicorn
echo "Iniciando aplicación FastAPI..."
cd /app/workflows/gym
uvicorn app_fastapi:app --host 0.0.0.0 --port 5050 &
FASTAPI_PID=$!

# Manejar señales para apagar graciosamente
trap "kill $TELEGRAM_PID $FASTAPI_PID; exit" SIGINT SIGTERM

echo "Ambos servicios iniciados. Esperando..."
wait
