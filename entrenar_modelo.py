# entrenar_modelo.py

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_squared_error

# =========================
# 1. CARGAR DATOS DESDE EXCEL
# =========================

# Ajusta el nombre del archivo si es distinto
RUTA_EXCEL = "inmobiliario_limpio_v6.xlsx"

df = pd.read_excel("data/inmobiliario_limpio_v6.xlsx")

print("Columnas del DataFrame:")
print(df.columns.tolist())

# =========================
# 2. DEFINIR TARGET Y FEATURES
# =========================

# Columna objetivo (precio en UF)
columna_target = "precio_en_uf"

# Columna categórica
columnas_categoricas = ["comuna"]

# Todas las demás columnas (excepto comuna y target) serán numéricas
columnas_numericas = [
    c for c in df.columns
    if c not in columnas_categoricas + [columna_target]
]

print("Columnas numéricas:", columnas_numericas)
print("Columnas categóricas:", columnas_categoricas)

X = df[columnas_numericas + columnas_categoricas]
y = df[columna_target]


# =========================
# 3. TRAIN / TEST SPLIT
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42
)

# =========================
# 4. PREPROCESAMIENTO
# =========================
preprocesador = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), columnas_numericas),
        ("cat", OneHotEncoder(handle_unknown="ignore"), columnas_categoricas),
    ]
)

# =========================
# 5. MODELO: GRADIENT BOOSTING
# =========================
modelo = GradientBoostingRegressor(random_state=42)

pipeline_gb = Pipeline(steps=[
    ("preprocessor", preprocesador),
    ("model", modelo),
])

# =========================
# 6. ENTRENAR
# =========================
pipeline_gb.fit(X_train, y_train)

# =========================
# 7. EVALUAR RÁPIDO
# =========================
y_pred = pipeline_gb.predict(X_test)
r2 = r2_score(y_test, y_pred)

mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)

print(f"R2 en test:  {r2:.4f}")
print(f"RMSE en test: {rmse:.4f}")

# =========================
# 8. GUARDAR MODELO
# =========================
os.makedirs("models", exist_ok=True)
RUTA_MODELO = os.path.join("models", "modelo_inmobiliario.joblib")

joblib.dump(pipeline_gb, RUTA_MODELO)

print(f"Modelo guardado en: {RUTA_MODELO}")
