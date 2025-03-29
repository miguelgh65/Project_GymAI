#!/bin/bash
echo "Iniciando servicios..."

# Asegurarnos que el archivo es ejecutable
chmod +x /app/start.sh

# Iniciar el bot de Telegram en segundo plano
echo "Iniciando Bot de Telegram..."
cd /app/telegram/gym
python main.py &
TELEGRAM_PID=$!

# Iniciar la aplicación FastAPI con uvicorn
# IMPORTANTE: Ejecutar desde el directorio raíz para mantener las rutas de importación
echo "Iniciando aplicación FastAPI..."
cd /app
uvicorn workflows.gym.app_fastapi:app --host 0.0.0.0 --port 5050 &
FASTAPI_PID=$!

# Manejar señales para apagar graciosamente
trap "kill $TELEGRAM_PID $FASTAPI_PID; exit" SIGINT SIGTERM

echo "Ambos servicios iniciados. Esperando..."
wait