# Usar una versión específica es mejor
FROM python:3.11-slim

# Establecer el directorio de trabajo en la imagen
WORKDIR /app

# Instalar dependencias del sistema si fueran necesarias
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Copiar primero el archivo de dependencias para aprovechar la cache de Docker
COPY requirements.txt /app/
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Instalar las dependencias
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
# Añadir esta línea en tu Dockerfile

# Copiar el resto del código de la aplicación
# Copia las carpetas que realmente necesita el backend
COPY back_end/gym/ /app/back_end/gym/
COPY telegram/ /app/telegram/
COPY fitness_agent/ /app/fitness_agent/
COPY start.sh /app/
# COPY .env /app/ # No es ideal copiar .env a la imagen, se carga con env_file en docker-compose

# Asegurar que el script sea ejecutable
RUN chmod +x /app/start.sh

# Exponer el puerto INTERNO que usará la aplicación (¡Ahora 5051!)
EXPOSE 5051

# Usar el script para iniciar la aplicación
# Asegúrate que start.sh inicie Uvicorn en el puerto 5051
# Ejemplo: uvicorn workflows.gym.main:app --host 0.0.0.0 --port 5051 --reload (el --reload es para desarrollo)
CMD ["/app/start.sh"]