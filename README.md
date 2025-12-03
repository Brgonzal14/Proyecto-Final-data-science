# SICOP – Cotizador inteligente de propiedades

Proyecto de Data Science para estimar el precio de departamentos y casas,
mostrar propiedades similares y segmentar el mercado inmobiliario.

- **Backend:** FastAPI (Python)
- **Frontend:** HTML + Bootstrap + JS
- **Modelo:** `models/modelo_inmobiliario.joblib`
- **Datos:** `data/inmobiliario_limpio_v6_con_links.xlsx` + `data/segmento_por_comuna.xlsx`

---

## 1. Requisitos

- Python 3.9 o superior
- `pip` instalado

Librerías principales:

```bash
pip install fastapi uvicorn pandas joblib scikit-learn openpyxl
````

O usar `pip install -r requirements.txt` 

---

## 2. Estructura del proyecto

```text
.
├── app
│   └── main.py              # API FastAPI
├── data
│   ├── inmobiliario_limpio_v6_con_links.xlsx
│   └── segmento_por_comuna.xlsx
├── models
│   └── modelo_inmobiliario.joblib
│   └── segmento_por_comuna.xlsx
├── frontend
│    ├── index.html           # Frontend
│    ├── main.js
│    └── styles.css 
├── requirements.txt
```

> Importante: las rutas de `main.py` asumen que `data/` y `models/` están
> en la carpeta raíz del proyecto.

---

## 3. Levantar la API (backend)

Desde la raíz del proyecto:

```bash
uvicorn app.main:app --reload --port 8000
```

Si todo está bien, deberías ver algo como:

* `Application startup complete.`
* API disponible en: `http://127.0.0.1:8000`

Endpoints principales:

* `GET /health` → estado de la API
* `POST /predict` → precio estimado
* `POST /similar` → propiedades similares
* `POST /segmento` → segmentos de mercado

Ejemplo de payload (JSON):

```json
{
  "sup_total": 75,
  "sup_construida": 70,
  "dormitorios": 2,
  "banos": 2,
  "estacionamientos": 1,
  "antiguedad": 10,
  "comuna": "Maipú",
  "bodegas": 0,
  "pisos": 1,
  "terraza": true,
  "piscina": false,
  "aire_acondicionado": false,
  "closets_empotrados": true
}
```

---

## 4. Levantar el frontend

Desde la carpeta `frontend/`:

```bash
cd static
python -m http.server 5500
```

Luego abrir en el navegador:

```text
http://127.0.0.1:5500/index.html
```

El frontend llama a la API en `http://127.0.0.1:8000`, así que:

* **Backend** debe estar corriendo en el puerto 8000.
* **Frontend** se sirve desde el puerto 5500 (o el que uses).

---

## 5. Cómo usarlo

1. Abrir `http://127.0.0.1:5500/index.html`.
2. Ingresar datos de la propiedad (sup. total, sup. construida, dormitorios, etc.).
3. Presionar **“Calcular”**.
4. Verás:

   * Precio estimado en UF.
   * Segmento global (K-Means, mercado completo).
   * Segmento por comuna (ranking de comunas).
   * Tabla de propiedades similares con link a la ficha original.

---

## 6. Notas

* Si algún endpoint devuelve error 500, revisar la consola donde corre `uvicorn`
  para ver el traceback.
* Si el navegador muestra errores de CORS, normalmente es porque la API se cayó.
  Revisar primero que `/health` responda `{"status": "ok"}`.

