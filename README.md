

# SICOP – Cotizador inteligente de propiedades

### *Versión Dockerizable (no requiere instalar Python)*

Proyecto de Data Science para estimar el precio de propiedades, mostrar similares y segmentar el mercado inmobiliario usando:

* **Backend:** FastAPI (Python)
* **Frontend:** HTML + Bootstrap + JS
* **Contenedores:** Docker + Docker Compose


---

## 1. Requisitos

* **Docker Desktop** instalado

## 2. Estructura del proyecto

```text
.
├── app/
│   └── main.py                 # API FastAPI
├── data/
│   ├── inmobiliario_limpio_v6_con_links.xlsx
│   └── segmento_por_comuna.xlsx
├── models/
│   └── modelo_inmobiliario.joblib
├── frontend/
│   ├── index.html              # Frontend
│   ├── main.js
│   └── styles.css
├── Dockerfile                  # Backend
├── docker-compose.yml          # Backend + Frontend
└── requirements.txt
```

---

## 3. Levantar todo con Docker

Desde la **raíz del proyecto** ejecutar:

```bash
docker compose up --build
```

Docker hará:

* Construir la imagen del **backend** (FastAPI + modelo + datos)
* Levantar un contenedor de **frontend** (Nginx sirviendo la web)
* Crear la red interna entre ambos contenedores

Si todo está bien, verás:

```
Application startup complete.
Uvicorn running on http://0.0.0.0:8000
nginx/1.x.x ... ready for start up
```

---

## 4. Acceder al sistema

### **Frontend:**

Abrir en el navegador:

```
http://localhost:5500
```

### **Backend / API:**

Probar salud del servidor:

```
http://localhost:8000/health
```

Debe responder:

```json
{"status": "ok"}
```

---

## 5. Cómo usar la aplicación

1. Abrir **[http://localhost:5500](http://localhost:5500)**
2. Ingresar los datos de la propiedad
3. Presionar **“Calcular”**
4. La aplicación mostrará:

* Precio estimado en UF
* Segmento global (K-Means, mercado completo)
* Segmento por comuna (ranking de comunas)
* Tabla de propiedades similares con links a la publicación original

Todo funcionando desde Docker, sin dependencias adicionales.

---

## 6. Detener los contenedores

Ejecuta:

```bash
docker compose down
```

Esto apaga el backend y el frontend.

---

## 7. Notas útiles

* Si el frontend muestra error 500 o CORS, probablemente el backend se cayó.
  Revisa el log del contenedor:

  ```bash
  docker logs sicop-backend
  ```

* Si realizas cambios en el backend (código de FastAPI), necesitas reconstruir:

  ```bash
  docker compose up --build
  ```

* Si se cambia solo HTML/JS del frontend, basta con refrescar la página (Nginx usa volumen).

