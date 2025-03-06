# Usar una imagen de Python 3
FROM python:3.11

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar archivos de la aplicación
COPY . /app

# Instalar dependencias
RUN pip install --no-cache-dir flask psycopg2-binary langchain_deepseek requests

# Exponer el puerto 5050 para Flask
EXPOSE 5050

# Comando para ejecutar la app automáticamente
CMD ["python", "-u", "gym.py"]

