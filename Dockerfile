FROM python:3.11

# Establecer el directorio de trabajo en la imagen
WORKDIR /app

# Copiar primero el archivo de dependencias para aprovechar la cache de Docker
COPY requirements.txt /app/

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar archivos de la aplicación
COPY workflows/gym/ /app/workflows/gym/

# Copiar .env al directorio raíz
COPY .env /app/

# Exponer el puerto que usará la aplicación Flask
EXPOSE 5050

# Cambiar al directorio de la aplicación
WORKDIR /app/workflows/gym

# Comando para ejecutar la aplicación
CMD ["python", "-u", "app.py"]