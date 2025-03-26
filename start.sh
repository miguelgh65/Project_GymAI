#!/bin/bash
# start.sh

echo "Iniciando servicios..."

# Iniciar el bot de Telegram en segundo plano
echo "Iniciando Bot de Telegram..."
cd /app/telegram/gym
python main.py &
TELEGRAM_PID=$!

# Iniciar la aplicación Flask
echo "Iniciando aplicación Flask..."
cd /app/workflows/gym
python app.py &
FLASK_PID=$!

# Manejar señales para apagar graciosamente
trap "kill $TELEGRAM_PID $FLASK_PID; exit" SIGINT SIGTERM

# Mantener el script en ejecución
echo "Ambos servicios iniciados. Esperando..."
wait