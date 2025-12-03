# app/main.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import joblib
import os
import numpy as np
import unicodedata
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans


# =========================
# NORMALIZACIÓN DE COMUNAS
# =========================
def normalizar_comuna(s: str) -> str:
    """Pasa a minúsculas, quita espacios y acentos."""
    s = str(s).strip().lower()
    s = "".join(
        c for c in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(c)
    )
    return s


# =========================
# RUTAS DE ARCHIVOS
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MODEL_PATH = os.path.join("models", "modelo_inmobiliario.joblib")

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "inmobiliario_limpio_v6_con_links.xlsx",   # aquí tienes sup_total, link, amenities, etc.
)

SEGMENTO_COMUNA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "segmento_por_comuna.xlsx",      # excel que creaste con segmento_codigo / segmento_nombre
)


# =========================
# CARGAR MODELO Y DATA
# =========================
modelo = joblib.load(MODEL_PATH)

df_original = (
    pd.read_excel(DATA_PATH)
    .reset_index()
    .rename(columns={"index": "id_propiedad"})
)

# normalizar comunas
df_original["comuna_norm"] = df_original["comuna"].apply(normalizar_comuna)

# rango de precios del dataset (para acotar la predicción)
MIN_PRECIO = float(df_original["precio_en_uf"].min())
MAX_PRECIO = float(df_original["precio_en_uf"].max())

COLUMNA_TARGET = "precio_en_uf"
COLUMNA_CATEGORICA = "comuna"

COLUMNAS_NUMERICAS = [
    c
    for c in df_original.columns
    if c not in [COLUMNA_TARGET, COLUMNA_CATEGORICA, "id_propiedad"]
]


# =========================
# SEGMENTO POR COMUNA (MANUAL)
# =========================
df_segmento_comuna = pd.read_excel(SEGMENTO_COMUNA_PATH)
df_segmento_comuna["comuna_norm"] = df_segmento_comuna["comuna"].apply(
    normalizar_comuna
)

# hacemos un merge para que cada propiedad tenga código/nombre de segmento de su comuna
df_original = df_original.merge(
    df_segmento_comuna[["comuna_norm", "segmento_codigo", "segmento_nombre"]],
    on="comuna_norm",
    how="left",
)


# =========================
# FEATURES PARA SIMILITUD Y K-MEANS
# =========================
FEATURES_SIMILITUD = [
    "sup_total",
    "sup_construida",
    "dormitorios",
    "banos",
    "estacionamientos",
    "antiguedad",
    "pisos",
    "amb_terraza",
    "amb_piscina",
    "srv_aire_acondicionado",
    "amb_closets",
]

df_sim = df_original[FEATURES_SIMILITUD].copy()
df_sim = df_sim.fillna(df_sim.median(numeric_only=True))

scaler_sim = StandardScaler()
X_sim = scaler_sim.fit_transform(df_sim)


# =========================
# K-MEANS (SEGMENTO GLOBAL)
# =========================
N_CLUSTERS = 4

kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
kmeans.fit(X_sim)

df_clusters = df_original.copy()
df_clusters["cluster"] = kmeans.labels_

cluster_summary = (
    df_clusters.groupby("cluster")
    .agg(
        n_propiedades=("id_propiedad", "count"),
        promedio_uf=("precio_en_uf", "mean"),
        promedio_sup_total=("sup_total", "mean"),
        promedio_dormitorios=("dormitorios", "mean"),
    )
    .reset_index()
)

# Mapeo de clusters K-Means a segmentos de negocio ordenados por precio promedio.
# Ordenamos los clusters de menor a mayor precio y les asignamos etiquetas
# cercanas a los segmentos definidos en segmento_por_comuna.xlsx
# (económico, medio_bajo, medio_alto, alto).
cluster_summary = cluster_summary.sort_values("promedio_uf").reset_index(drop=True)
ordered_clusters = cluster_summary["cluster"].tolist()

BUSINESS_SEGMENT_NAMES = [
    "Segmento Económico",
    "Segmento Medio-bajo",
    "Segmento Medio-alto",
    "Segmento Alto",
]

SEGMENT_GLOBAL_NAMES = {
    cl: BUSINESS_SEGMENT_NAMES[i] if i < len(BUSINESS_SEGMENT_NAMES) else f"Segmento {cl}"
    for i, cl in enumerate(ordered_clusters)
}


# =========================
# FASTAPI
# =========================
app = FastAPI(
    title="SICOP - API Inmobiliaria",
    description="API para cotizar propiedades, buscar similares y segmentar mercado",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local/demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# ESQUEMA DE ENTRADA
# =========================
class PropiedadInput(BaseModel):
    sup_total: float
    sup_construida: float
    dormitorios: int
    banos: int
    estacionamientos: int
    antiguedad: int
    comuna: str

    bodegas: int | None = 0
    pisos: int | None = 1

    terraza: bool | None = False
    piscina: bool | None = False
    aire_acondicionado: bool | None = False
    closets_empotrados: bool | None = False


# =========================
# FUNCIONES AUXILIARES
# =========================
def predecir_precio_modelo(df_modelo: pd.DataFrame) -> float:
    raw = modelo.predict(df_modelo)[0]
    pred = max(MIN_PRECIO, min(raw, MAX_PRECIO))
    return float(pred)


def construir_fila(propiedad: PropiedadInput) -> pd.DataFrame:
    """
    Crea un DataFrame con TODAS las columnas numéricas + 'comuna'
    para usar tanto en predicción como en similitud/segmentación.
    """
    fila = {col: 0 for col in COLUMNAS_NUMERICAS}
    data_dict = propiedad.dict()

    # mapear amenities
    amenity_map = {
        "terraza": "amb_terraza",
        "piscina": "amb_piscina",
        "aire_acondicionado": "srv_aire_acondicionado",
        "closets_empotrados": "amb_closets",
    }

    for campo, valor in data_dict.items():
        if campo in COLUMNAS_NUMERICAS and valor is not None:
            fila[campo] = valor

    # amenities (bool -> 0/1)
    for campo_form, col_df in amenity_map.items():
        if col_df in COLUMNAS_NUMERICAS:
            fila[col_df] = 1 if data_dict.get(campo_form) else 0

    df_modelo = pd.DataFrame([fila])
    df_modelo[COLUMNA_CATEGORICA] = propiedad.comuna
    df_modelo["comuna_norm"] = df_modelo["comuna"].apply(normalizar_comuna)
    return df_modelo


def obtener_segmentos(df_propiedad: pd.DataFrame):
    """
    Devuelve:
    - segmento_global: K-Means (dataset completo)
    - segmento_local: segmento manual por comuna (económico / medio_bajo / etc.)
    """
    # ------ GLOBAL (K-MEANS) ------
    x_input = scaler_sim.transform(df_propiedad[FEATURES_SIMILITUD])
    cluster = int(kmeans.predict(x_input)[0])

    row_global = cluster_summary[cluster_summary["cluster"] == cluster].iloc[0]

    segmento_global = {
        "cluster": cluster,
        "nombre_segmento": SEGMENT_GLOBAL_NAMES.get(cluster, f"Segmento {cluster}"),
        "n_propiedades": int(row_global["n_propiedades"]),
        "promedio_uf": float(row_global["promedio_uf"]),
        "promedio_sup_total": float(row_global["promedio_sup_total"]),
        "promedio_dormitorios": float(row_global["promedio_dormitorios"]),
    }

    # ------ LOCAL (POR COMUNA) ------
    comuna_norm = df_propiedad["comuna_norm"].iloc[0]

    # info manual del excel segmento_por_comuna.xlsx
    row_seg = df_segmento_comuna[
        df_segmento_comuna["comuna_norm"] == comuna_norm
    ]

    if len(row_seg) > 0:
        row_seg = row_seg.iloc[0]
        seg_codigo = int(row_seg["segmento_codigo"])
        seg_nombre = str(row_seg["segmento_nombre"])
        comuna_nombre = str(row_seg["comuna"])
    else:
        seg_codigo = None
        seg_nombre = "No definido"
        comuna_nombre = df_propiedad["comuna"].iloc[0]

    # estadísticas solo de esa comuna (datos reales sobre el dataset original)
    # usamos df_original para que los promedios coincidan exactamente con el Excel
    df_comuna = df_original[df_original["comuna_norm"] == comuna_norm]

    if len(df_comuna) > 0:
        segmento_local = {
            "comuna": comuna_nombre,
            "segmento_codigo": seg_codigo,
            "segmento_nombre": seg_nombre,
            "n_propiedades_comuna": int(len(df_comuna)),
            "precio_promedio_comuna": float(df_comuna["precio_en_uf"].mean()),
            "sup_promedio_comuna": float(df_comuna["sup_total"].mean()),
            "dormitorios_promedio_comuna": float(df_comuna["dormitorios"].mean()),
        }
    else:
        segmento_local = {
            "comuna": comuna_nombre,
            "segmento_codigo": seg_codigo,
            "segmento_nombre": seg_nombre,
            "n_propiedades_comuna": 0,
            "precio_promedio_comuna": None,
            "sup_promedio_comuna": None,
            "dormitorios_promedio_comuna": None,
        }

    return segmento_global, segmento_local


def calcular_precio_y_similares(propiedad: PropiedadInput, k: int = 5) -> dict:
    """
    - Construye df_modelo
    - Predice precio con el modelo
    - Busca propiedades similares dentro de la misma comuna (si hay)
    - Ajusta el precio usando el promedio de los similares.
    """
    df_modelo = construir_fila(propiedad)

    # 1) Predicción base
    precio_pred = predecir_precio_modelo(df_modelo)

    # 2) Filtrar por misma comuna
    comuna_norm = df_modelo["comuna_norm"].iloc[0]
    mask = df_original["comuna_norm"] == comuna_norm
    indices = np.where(mask)[0]

    # si no hay propiedades de esa comuna, usar todo el dataset
    if len(indices) == 0:
        indices = np.arange(len(df_original))

    # 3) subconjunto y distancias
    X_sim_subset = X_sim[indices]
    x_input = scaler_sim.transform(df_modelo[FEATURES_SIMILITUD])
    dists_subset = np.linalg.norm(X_sim_subset - x_input, axis=1)

    top_k_local = np.argsort(dists_subset)[:k]
    idx_sorted = indices[top_k_local]

    similares = []
    for idx_df, dist_local in zip(idx_sorted, dists_subset[top_k_local]):
        fila = df_original.iloc[idx_df]
        url = fila.get("link", "")
        if pd.isna(url):
            url = ""

        similares.append(
            {
                "id_propiedad": int(fila["id_propiedad"]),
                "sup_total": float(fila["sup_total"]),
                "sup_construida": float(fila["sup_construida"]),
                "dormitorios": int(fila["dormitorios"]),
                "banos": int(fila["banos"]),
                "estacionamientos": int(fila["estacionamientos"]),
                "comuna": str(fila["comuna"]),
                "precio_en_uf": float(fila["precio_en_uf"]),
                "distancia": float(dist_local),
                "url_portal": str(url),
            }
        )

    # 4) Ajuste de precio
    if similares:
        precios_similares = [p["precio_en_uf"] for p in similares]
        prom_similares = float(sum(precios_similares) / len(precios_similares))
        precio_ajustado = 0.3 * precio_pred + 0.7 * prom_similares
    else:
        prom_similares = None
        precio_ajustado = precio_pred

    return {
        "df_modelo": df_modelo,
        "precio_modelo": float(precio_pred),
        "precio_ajustado": float(precio_ajustado),
        "promedio_similares": prom_similares,
        "similares": similares,
        "k": k,
    }


# =========================
# ENDPOINTS
# =========================
@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/predict")
def predecir_precio(propiedad: PropiedadInput):
    resultado = calcular_precio_y_similares(propiedad, k=5)
    return {
        "precio_estimado_uf": resultado["precio_ajustado"],
        "precio_modelo_uf": resultado["precio_modelo"],
        "k_usado_para_ajuste": resultado["k"],
        "propiedad_entrada": propiedad.dict(),
    }


@app.post("/similar")
def propiedades_similares(propiedad: PropiedadInput, k: int = 5):
    resultado = calcular_precio_y_similares(propiedad, k=k)
    return {
        "precio_estimado_uf": resultado["precio_ajustado"],
        "precio_modelo_uf": resultado["precio_modelo"],
        "k": resultado["k"],
        "propiedad_entrada": propiedad.dict(),
        "similares": resultado["similares"],
    }


@app.post("/segmento")
def segmentar_propiedad(propiedad: PropiedadInput):
    """
    Devuelve DOS niveles de segmento:
    - segmento_global: clusters K-Means del mercado completo
    - segmento_local: segmento manual de la comuna + estadísticas de esa comuna
    """
    df_modelo = construir_fila(propiedad)
    precio_pred = predecir_precio_modelo(df_modelo)

    segmento_global, segmento_local = obtener_segmentos(df_modelo)

    return {
        "precio_estimado_uf": float(precio_pred),
        "segmento_global": segmento_global,
        "segmento_local": segmento_local,
        "propiedad_entrada": propiedad.dict(),
    }
