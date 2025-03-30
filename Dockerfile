FROM python:3.11

# Establecer el directorio de trabajo en la imagen
WORKDIR /app

# Copiar primero el archivo de dependencias para aprovechar la cache de Docker
COPY requirements.txt /app/

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar archivos de la aplicación Flask
COPY workflows/gym/ /app/workflows/gym/

# Copiar archivos del bot de Telegram
COPY telegram/ /app/telegram/

# Copiar archivos del módulo fitness_agent
COPY fitness_agent/ /app/fitness_agent/

# Copiar .env al directorio raíz
COPY .env /app/

# Copiar el script de inicio
COPY start.sh /app/
COPY front_end/ /app/front_end/
RUN chmod +x /app/start.sh

# Exponer el puerto que usará la aplicación Flask
EXPOSE 5050

# Usar el script para iniciar ambos servicios
CMD ["/app/start.sh"]