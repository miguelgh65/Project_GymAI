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

# Asegurarse de que la estructura de directorios para LangGraph exista
RUN mkdir -p /app/workflows/gym/services/langgraph_agent

# Copiar .env al directorio raíz
COPY .env /app/

# Copiar el script de inicio
COPY start.sh /app/
RUN chmod +x /app/start.sh

# Exponer el puerto que usará la aplicación Flask
EXPOSE 5050

# Usar el script para iniciar ambos servicios
CMD ["/app/start.sh"]