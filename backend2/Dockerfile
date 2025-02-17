# Usa una imagen oficial de Python 3.9-slim como imagen base
FROM python:3.9-slim

# Evita que Python escriba archivos .pyc y habilita el log sin búfer
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instala dependencias a nivel de sistema, incluyendo libgomp1 que requiere LightGBM 
RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo de requerimientos primero y luego instala las dependencias
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia el resto del código de la aplicación en el contenedor
COPY . .

# Expone el puerto 5000 (el puerto en el que se ejecuta la aplicación Flask)
EXPOSE 5000

# Comando para ejecutar la aplicación Flask
CMD ["python", "app.py"]
