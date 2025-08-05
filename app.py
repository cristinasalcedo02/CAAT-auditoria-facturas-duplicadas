# CAAT – Análisis de Facturas Duplicadas

import pandas as pd
import streamlit as st
import hashlib
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# CONFIGURACIÓN GENERAL
st.set_page_config(page_title="CAAT – Análisis de Facturas Duplicadas", layout="wide")
st.title("🧾 CAAT – Análisis de Facturas Duplicadas")

st.markdown("""
Esta aplicación es una herramienta de Auditoría Asistida por Computadora (CAAT) diseñada para analizar grandes volúmenes de datos contenidos en hojas de cálculo. Su objetivo principal es detectar **facturas duplicadas** mediante técnicas automatizadas de comparación, validación e integridad.

Puedes subir un archivo Excel con múltiples hojas desde el panel lateral izquierdo y seleccionar libremente cuáles analizar. La herramienta te permitirá:

- Identificar coincidencias por número de factura, fecha, proveedor y monto.
- Verificar la integridad de archivos mediante hash criptográfico.
- Obtener resúmenes visuales de hallazgos clave.
- Consultar un historial de ejecuciones como evidencia del proceso.

💡 Utiliza esta herramienta para mejorar la eficiencia, trazabilidad y confiabilidad en tus auditorías.
""")

st.warning("Las hojas seleccionadas deben contener las siguientes columnas: numero_factura, fecha, proveedor, monto, usuario_registro")

# SUBIR ARCHIVO EXCEL
archivo = st.sidebar.file_uploader("📂 Sube tu archivo .xlsx con los datos", type="xlsx")

if archivo:
    excel = pd.ExcelFile(archivo)
    hojas = excel.sheet_names
    hoja_a = st.sidebar.selectbox("Selecciona la hoja para Archivo A:", hojas)
    hoja_b = st.sidebar.selectbox("Selecciona la hoja para Archivo B:", hojas, index=1 if len(hojas) > 1 else 0)

    df_a = excel.parse(hoja_a)
    df_b = excel.parse(hoja_b)

    columnas_requeridas = {"numero_factura", "fecha", "proveedor", "monto", "usuario_registro"}
    if not columnas_requeridas.issubset(set(df_a.columns)) or not columnas_requeridas.issubset(set(df_b.columns)):
        st.error("❌ Las hojas seleccionadas no contienen todas las columnas requeridas.")
    else:
        # HASH DE INTEGRIDAD
        def calcular_hash(df):
            return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values).hexdigest()

        st.subheader("🔍 Verificación de integridad de archivos:")
        st.code(f"SHA-256 {hoja_a}: {calcular_hash(df_a)}")
        st.code(f"SHA-256 {hoja_b}: {calcular_hash(df_b)}")

        # ANÁLISIS DE DUPLICADOS
        duplicados_factura = df_a[df_a.duplicated(subset=["numero_factura"], keep=False)]
        duplicados_fpm = df_a[df_a.duplicated(subset=["fecha", "proveedor", "monto"], keep=False)]
        duplicados_campos_clave = df_a[df_a.duplicated(subset=["numero_factura", "fecha", "proveedor", "monto"], keep=False)]
        duplicados_entre_archivos = pd.merge(df_a, df_b, on=["numero_factura", "fecha", "proveedor", "monto"])
        validas = df_a[~df_a.index.isin(duplicados_factura.index)]

        st.subheader("📊 Resumen de hallazgos:")
        st.markdown(f"""
- **Duplicados por número de factura:** {len(duplicados_factura)} registros  
- **Duplicados por fecha-proveedor-monto:** {len(duplicados_fpm)} registros  
- **Duplicados por campos clave:** {len(duplicados_campos_clave)} registros  
- **Duplicados entre archivos:** {len(duplicados_entre_archivos)} registros  
- **Facturas válidas (no anuladas):** {len(validas)} registros
        """)

        # RANKING DE USUARIOS
        sospechosas = pd.concat([duplicados_factura, duplicados_fpm, duplicados_campos_clave])
        ranking = sospechosas.groupby("usuario_registro").size().reset_index(name="cantidad_duplicados")
        ranking = ranking.sort_values("cantidad_duplicados", ascending=False)

        st.subheader("🏁 Ranking de usuarios con más facturas sospechosas:")
        st.dataframe(ranking)

        st.subheader("📉 Visualización del ranking:")
        fig, ax = plt.subplots()
        sns.barplot(data=ranking, y="usuario_registro", x="cantidad_duplicados", ax=ax)
        ax.set_title("Ranking de usuarios con más facturas sospechosas")
        st.pyplot(fig)

        # HISTORIAL DE EJECUCIONES
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log = pd.DataFrame([{
            "usuario": "auditor_streamlit",
            "fecha_ejecucion": fecha,
            "Duplicados por número de factura": len(duplicados_factura),
            "Duplicados por fecha-proveedor-monto": len(duplicados_fpm),
            "Duplicados por campos clave": len(duplicados_campos_clave),
            "Duplicados entre archivos": len(duplicados_entre_archivos),
            "Facturas válidas": len(validas)
        }])
        st.subheader("📈 Historial de ejecuciones:")
        st.dataframe(log)

        # DESCARGA DE RESULTADO
        csv = sospechosas.to_csv(index=False).encode('utf-8')
        st.download_button("📤 Exportar resultados en CSV", data=csv, file_name="facturas_sospechosas.csv", mime="text/csv")
else:
    st.info("📥 Por favor, sube un archivo .xlsx desde el panel lateral izquierdo.")
