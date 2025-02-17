# app.py
import os
import numpy as np
import pandas as pd
import warnings
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, roc_auc_score
from sklearn.utils import resample
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.tree import DecisionTreeClassifier
import xgboost as xgb
import lightgbm as lgb
from flask import Flask, request, jsonify, render_template

warnings.filterwarnings("ignore")

###############################
# FUNCIONES UTILITARIAS
###############################
def limpiar_nombre_columna(columna):
    import unicodedata
    columna = unicodedata.normalize('NFKD', columna).encode('ASCII', 'ignore').decode('utf-8')
    columna = columna.replace(' ', '_').replace('-', '_')
    return columna

def cargar_preprocesar_datos(ruta_csv):
    try:
        df = pd.read_csv(ruta_csv, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(ruta_csv, encoding='latin1')
    df.columns = [limpiar_nombre_columna(col) for col in df.columns]
    if 'Porcentaje_Fino' not in df.columns:
        np.random.seed(42)
        df['Porcentaje_Fino'] = np.random.uniform(0, 100, size=len(df))
    if df.isnull().sum().any():
        df = df.fillna(df.mean())
    return df

def balancear_dataset(df, columna_objetivo='Mantenimiento'):
    if df is None:
        return None
    mantenimiento_counts = df[columna_objetivo].value_counts(normalize=True)
    if mantenimiento_counts.get(1, 0) < 0.1:
        df_majority = df[df[columna_objetivo] == 0]
        df_minority = df[df[columna_objetivo] == 1]
        df_minority_upsampled = resample(df_minority, replace=True, n_samples=len(df_majority), random_state=42)
        df_balanced = pd.concat([df_majority, df_minority_upsampled])
    else:
        df_balanced = df.copy()
    return df_balanced

def entrenar_modelos_clasificacion(X_train, y_train):
    modelos = {
        "Regresión Logística": LogisticRegression(random_state=42, max_iter=1000),
        "Árbol de Decisión": DecisionTreeClassifier(random_state=42),
        "Random Forest": RandomForestClassifier(random_state=42),
        "Gradient Boosting": GradientBoostingClassifier(random_state=42),
        "XGBoost": xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42),
        "LightGBM": lgb.LGBMClassifier(random_state=42)
    }
    modelos_entrenados = {}
    for nombre, modelo in modelos.items():
        modelo.fit(X_train, y_train)
        modelos_entrenados[nombre] = modelo
    return modelos_entrenados

def entrenar_red_neuronal_clasificacion(X_train, y_train):
    modelo = Sequential([
        Dense(128, activation='relu', input_shape=(X_train.shape[1],)),
        Dropout(0.3),
        Dense(64, activation='relu'),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dense(1, activation='sigmoid')
    ])
    modelo.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    modelo.fit(X_train, y_train, epochs=60, batch_size=64, validation_split=0.2, callbacks=[early_stopping], verbose=0)
    return modelo

def entrenar_modelos_regresion(X_train, y_train):
    modelos = {
        "Regresión Lineal": LinearRegression(),
        "Random Forest Regressor": RandomForestRegressor(random_state=42),
        "Gradient Boosting Regressor": GradientBoostingRegressor(random_state=42),
        "XGBoost Regressor": xgb.XGBRegressor(random_state=42),
        "LightGBM Regressor": lgb.LGBMRegressor(random_state=42)
    }
    modelos_entrenados = {}
    for nombre, modelo in modelos.items():
        modelo.fit(X_train, y_train)
        modelos_entrenados[nombre] = modelo
    return modelos_entrenados

def evaluar_modelos_regresion(modelos, X_test, y_test):
    resultados = []
    for nombre, modelo in modelos.items():
        y_pred = modelo.predict(X_test)
        resultados.append({
            "Modelo": nombre,
            "R2 Score": r2_score(y_test, y_pred)
        })
    resultados_df = pd.DataFrame(resultados)
    resultados_df = resultados_df.sort_values(by="R2 Score", ascending=False)
    return resultados_df

###############################
# MODELO Y ESCALADORES GLOBALES: se entrenan al iniciar el servidor
###############################
# Orden esperado del estado:
# [p80, sag_water, sag_speed, sag_pressure, stockpile_level, sump_level,
#  hardness, solids_feeding, pebble, gran_gt_100, gran_lt_30,
#  porcentaje_fino, consumo_energia_pct, edad_liner]
def evaluar_estado(state):
    (p80, sag_water, sag_speed, sag_pressure, stockpile_level, sump_level,
     hardness, solids_feeding, pebble, gran_gt_100, gran_lt_30,
     porcentaje_fino, consumo_energia_pct, edad_liner) = state

    input_reg_energy = np.array([sag_pressure, stockpile_level, solids_feeding,
                                 sump_level, sag_water, pebble, gran_gt_100,
                                 gran_lt_30, sag_speed, hardness, edad_liner,
                                 porcentaje_fino, p80]).reshape(1, -1)
    input_reg_energy_scaled = MODEL_DATA['scaler_reg_energy'].transform(input_reg_energy)
    consumo_energia_pred = MODEL_DATA['mejor_modelo_reg_energy_obj'].predict(input_reg_energy_scaled)[0]
    consumo_energia_adjusted = consumo_energia_pred * (consumo_energia_pct / 100)

    input_clas = np.array([sag_pressure, stockpile_level, solids_feeding,
                           sump_level, sag_water, pebble, gran_gt_100,
                           gran_lt_30, sag_speed, hardness, edad_liner,
                           porcentaje_fino, p80, consumo_energia_adjusted]).reshape(1, -1)
    input_clas_scaled = MODEL_DATA['scaler_class'].transform(input_clas)
    if isinstance(MODEL_DATA['mejor_modelo_clas_obj'], tf.keras.Model):
        mantenimiento_prob = MODEL_DATA['mejor_modelo_clas_obj'].predict(input_clas_scaled)[0][0]
    else:
        mantenimiento_prob = MODEL_DATA['mejor_modelo_clas_obj'].predict_proba(input_clas_scaled)[0][1]
    mantenimiento_required = int(mantenimiento_prob > 0.5)
    return consumo_energia_adjusted, mantenimiento_prob, mantenimiento_required

def entrenar_modelos():
    ruta_csv = os.path.join("data", "SAG_Operacion_Mantenimiento.csv")
    df = cargar_preprocesar_datos(ruta_csv)
    if df is None:
        raise Exception("Error al cargar CSV.")
    df_balanced = balancear_dataset(df, columna_objetivo='Mantenimiento')

    features_reg_energy = ['Presion_SAG','Nivel_Stockpile','Solidos_en_alimentacion_mineral',
                           'Nivel_Sump','Alimentacion_agua_SAG','Pebble',
                           'Granulometria_gt_100mm','Granulometria_lt_30mm','Velocidad_rotacion_SAG',
                           'Dureza','Edad_Liner','Porcentaje_Fino','P80']
    features_class = ['Presion_SAG','Nivel_Stockpile','Solidos_en_alimentacion_mineral',
                      'Nivel_Sump','Alimentacion_agua_SAG','Pebble',
                      'Granulometria_gt_100mm','Granulometria_lt_30mm','Velocidad_rotacion_SAG',
                      'Dureza','Edad_Liner','Porcentaje_Fino','P80','Consumo_energia_SAG']
    missing_reg = [feat for feat in features_reg_energy if feat not in df_balanced.columns]
    if missing_reg:
        raise Exception("Faltan características para regresión: " + ", ".join(missing_reg))
    missing_class = [feat for feat in features_class if feat not in df_balanced.columns]
    if missing_class:
        raise Exception("Faltan características para clasificación: " + ", ".join(missing_class))
    
    X_reg_energy = df_balanced[features_reg_energy]
    y_reg_energy = df_balanced["Consumo_energia_SAG"]
    X_class = df_balanced[features_class]
    y_class = df_balanced["Mantenimiento"]

    scaler_class = StandardScaler()
    X_class_scaled = scaler_class.fit_transform(X_class)
    scaler_reg_energy = StandardScaler()
    X_reg_energy_scaled = scaler_reg_energy.fit_transform(X_reg_energy)

    from sklearn.model_selection import train_test_split
    X_train_class, X_test_class, y_train_class, y_test_class = train_test_split(
        X_class_scaled, y_class, test_size=0.2, random_state=42, stratify=y_class
    )
    X_train_reg_energy, X_test_reg_energy, y_train_reg_energy, y_test_reg_energy = train_test_split(
        X_reg_energy_scaled, y_reg_energy, test_size=0.2, random_state=42
    )

    modelos_clasificacion = entrenar_modelos_clasificacion(X_train_class, y_train_class)
    modelo_nn_clas = entrenar_red_neuronal_clasificacion(X_train_class, y_train_class)
    modelos_regresion_energy = entrenar_modelos_regresion(X_train_reg_energy, y_train_reg_energy)
    resultados_reg_energy = evaluar_modelos_regresion(modelos_regresion_energy, X_test_reg_energy, y_test_reg_energy)
    mejor_modelo_reg_energy = resultados_reg_energy.loc[resultados_reg_energy['R2 Score'].idxmax()]['Modelo']
    mejor_modelo_reg_energy_obj = modelos_regresion_energy[mejor_modelo_reg_energy]

    # Se selecciona la red neuronal para clasificación
    mejor_modelo_clas_obj = modelo_nn_clas

    return {
        "scaler_class": scaler_class,
        "scaler_reg_energy": scaler_reg_energy,
        "mejor_modelo_reg_energy_obj": mejor_modelo_reg_energy_obj,
        "mejor_modelo_clas_obj": mejor_modelo_clas_obj
    }

MODEL_DATA = entrenar_modelos()

###############################
# APLICACIÓN FLASK
###############################
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/simulate", methods=["POST"])
def simulate():
    try:
        data = request.get_json()
        # Imprime los datos recibidos para depuración
        print("Datos recibidos en /simulate:", data)
        state = [
            float(data.get("p80", 100)),
            float(data.get("sag_water", 1350)),
            float(data.get("sag_speed", 9)),
            float(data.get("sag_pressure", 7700)),
            float(data.get("stockpile_level", 25)),
            float(data.get("sump_level", 90)),
            float(data.get("hardness", 35)),
            float(data.get("solids_feeding", 70)),
            float(data.get("pebble", 400)),
            float(data.get("gran_gt_100", 20)),
            float(data.get("gran_lt_30", 40)),
            float(data.get("porcentaje_fino", 70)),
            float(data.get("consumo_energia_pct", 100)),
            float(data.get("edad_liner", 3))
        ]
        energy_consumption, mantenimiento_prob, mantenimiento_required = evaluar_estado(state)
        # Convertir a tipos nativos de Python
        response = {
            "energy_consumption": float(energy_consumption),
            "mantenimiento_prob": float(mantenimiento_prob),
            "mantenimiento_required": int(mantenimiento_required)
        }
        print("Respuesta de /simulate:", response)
        return jsonify(response)
    except Exception as e:
        print("Error en /simulate:", str(e))
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
