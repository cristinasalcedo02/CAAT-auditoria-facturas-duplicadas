import streamlit as st
import pandas as pd
import hashlib
import io
from datetime import datetime
import matplotlib.pyplot as plt

# =====================
# 1. Título e introducción
# =====================
st.set_page_config(page_title="CAAT - Análisis de Facturas Duplicadas", layout="wide")
st.title("🧾 CAAT – Análisis de Facturas Duplicadas")

st.markdown(
    """
    Esta aplicación es una herramienta de Auditoría Asistida por Computadora (CAAT) diseñada para analizar grandes volúmenes de datos contenidos en hojas de cálculo. 
    Su objetivo principal es detectar **facturas duplicadas** mediante técnicas automatizadas de comparación, validación e integridad.

    Puedes subir un archivo Excel con múltiples hojas desde el panel lateral izquierdo y seleccionar libremente cuáles analizar. 
    La herramienta te permitirá:

    - Identificar coincidencias por número de factura, fecha, proveedor y monto.
    - Verificar la integridad de archivos mediante hash criptográfico.
    - Obtener resúmenes visuales de hallazgos clave.
    - Consultar un historial de ejecuciones como evidencia del proceso.

    ---
    💡 Utiliza esta herramienta para mejorar la eficiencia, trazabilidad y confiabilidad en tus auditorías.
    """
)

# =====================
# 2. Subida de archivo Excel
# =====================
archivo_excel = st.sidebar.file_uploader("Sube tu archivo .xlsx con los datos", type=["xlsx"])

if archivo_excel:
    xls = pd.ExcelFile(archivo_excel)
    hojas = xls.sheet_names

    hoja_a = st.sidebar.selectbox("Selecciona la hoja para Archivo A:", hojas)
    hoja_b = st.sidebar.selectbox("Selecciona la hoja para Archivo B:", hojas, index=1 if len(hojas) > 1 else 0)

    df_a = xls.parse(hoja_a)
    df_b = xls.parse(hoja_b)

    # =====================
    # 3. Validación de columnas clave
    # =====================
    columnas_clave = ["numero_factura", "fecha", "proveedor", "monto", "usuario_registro"]
    if not all(col in df_a.columns and col in df_b.columns for col in columnas_clave):
        st.error("Las hojas seleccionadas deben contener las siguientes columnas: " + ", ".join(columnas_clave))
        st.stop()

    # =====================
    # 4. Verificación de integridad (hash)
    # =====================
    def calcular_hash(df):
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        return hashlib.sha256(csv_bytes).hexdigest()

    hash_a = calcular_hash(df_a)
    hash_b = calcular_hash(df_b)

    st.markdown("### 🔎 Verificación de integridad de archivos:")
    st.code(f"SHA-256 {hoja_a}: {hash_a}")
    st.code(f"SHA-256 {hoja_b}: {hash_b}")

    # =====================
    # 5. Detección de duplicados
    # =====================
    duplicados_num = df_a[df_a.duplicated("numero_factura")]
    duplicados_fecha_prov_monto = df_a[df_a.duplicated(["fecha", "proveedor", "monto"])]
    duplicados_campos_clave = df_a[df_a.duplicated(columnas_clave[:-1])]
    cruces = pd.merge(df_a, df_b, on=columnas_clave[:-1], how="inner")

    validas = df_a.drop_duplicates(subset=columnas_clave[:-1])

    # =====================
    # 6. Ranking de usuarios con más duplicados
    # =====================
    sospechosas = pd.concat([duplicados_num, duplicados_fecha_prov_monto, duplicados_campos_clave])
    ranking = sospechosas.groupby("usuario_registro").size().reset_index(name="cantidad_duplicados")
    ranking = ranking.sort_values(by="cantidad_duplicados", ascending=False)

    st.markdown("## 🏁 Ranking de usuarios con más facturas sospechosas:")
    st.dataframe(ranking)

    # =====================
    # 7. Gráfico de barras de hallazgos
    # =====================
    resumen = {
        "Duplicados por número de factura": len(duplicados_num),
        "Duplicados por fecha-proveedor-monto": len(duplicados_fecha_prov_monto),
        "Duplicados por campos clave": len(duplicados_campos_clave),
        "Duplicados entre archivos": len(cruces),
        "Facturas válidas (no anuladas)": len(validas)
    }

    st.markdown("## 📈 Resumen de hallazgos:")
    for clave, valor in resumen.items():
        st.markdown(f"- **{clave}**: {valor} registros")

    # =====================
    # 8. Histórico de ejecuciones (log)
    # =====================
    log_data = {
        "usuario": ["auditor_streamlit"],
        "fecha_ejecucion": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        **{clave: [valor] for clave, valor in resumen.items()}
    }

    log_df = pd.DataFrame(log_data)
    log_df.to_csv("log_ejecuciones.csv", index=False)

    st.markdown("## 📊 Historial de ejecuciones:")
    st.dataframe(log_df)

else:
    st.info("Por favor, sube un archivo .xlsx desde el panel lateral izquierdo para iniciar el análisis.")
