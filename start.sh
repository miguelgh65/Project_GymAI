#!/bin/bash
# Archivo: start.sh (Corregido para montaje .:/app y working_dir /app)

echo "Iniciando servicios..."

# --- Iniciar Bot Telegram ---
# La ruta ahora es relativa a /app donde está el código montado
echo "Iniciando Bot de Telegram..."
# El comando 'cd' es relativo al working_dir actual (/app)
(cd ./telegram/gym && python main.py >> /proc/1/fd/1 2>> /proc/1/fd/2 &)
TELEGRAM_PID=$!
# No necesitamos volver con 'cd /app' ya que estamos en el working_dir correcto

# --- Configuración SSL ---
# Lee variables de entorno (que ahora apuntan a /app/certs/...)
# Estos paths son DENTRO del contenedor
KEYFILE_PATH=${SSL_KEY_PATH:-/app/certs/localhost+2-key.pem} # Usa variable o default
CERTFILE_PATH=${SSL_CERT_PATH:-/app/certs/localhost+2.pem} # Usa variable o default
echo "Keyfile Path (para Uvicorn): ${KEYFILE_PATH}"
echo "Certfile Path (para Uvicorn): ${CERTFILE_PATH}"

# --- Iniciar FastAPI ---
echo "Iniciando aplicación FastAPI con Uvicorn (HTTPS)..."
# Como el working_dir es /app, usamos la ruta completa del módulo Python
# desde esa raíz. PYTHONPATH=/app también ayuda a encontrar 'back_end'.
uvicorn back_end.gym.app_fastapi:app \
    --host 0.0.0.0 \
    --port 5050 \
    --reload \
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # --ssl-keyfile "${KEYFILE_PATH}" \
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # --ssl-certfile "${CERTFILE_PATH}" &
FASTAPI_PID=$!

# --- Manejo de Señales y Espera ---
cleanup() {
    echo "Recibida señal de parada, deteniendo procesos..."
    # Intentar detener por PID, si falla, intentar por nombre de comando
    kill -s TERM $TELEGRAM_PID $FASTAPI_PID 2>/dev/null || pkill -TERM -f "python main.py" || pkill -TERM -f "uvicorn back_end.gym.app_fastapi:app"
    wait $TELEGRAM_PID $FASTAPI_PID 2>/dev/null # Esperar un poco
    echo "Procesos detenidos."
    exit 0
}
trap cleanup SIGINT SIGTERM

echo "Ambos servicios iniciados (FastAPI en HTTPS). Esperando..."
# Esperar a que cualquier proceso hijo termine
wait
EXIT_STATUS=$?
echo "Todos los procesos hijos terminaron. Saliendo con estado: $EXIT_STATUS."
exit $EXIT_STATUS