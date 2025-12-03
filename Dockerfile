FROM python:3.11-slim

# Carpeta de trabajo dentro del contenedor
WORKDIR /app

# Copiamos dependencias e instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código y los datos
COPY app ./app
COPY data ./data
COPY models ./models

# Opcional: evitar buffering en logs
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Levantar la API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
