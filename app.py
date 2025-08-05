import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import hashlib
from datetime import datetime
import io

# ------------------------
# CONFIGURACIÓN DE LA APP
# ------------------------
st.set_page_config(page_title="CAAT – Análisis de Facturas Duplicadas", layout="wide")
st.title("🧾 CAAT – Análisis de Facturas Duplicadas")

# Introducción breve
st.markdown("""
> Esta herramienta de Auditoría Asistida por Computadora (CAAT) permite detectar **facturas duplicadas** mediante técnicas de comparación automatizada.
> Puedes subir los archivos de compras y contabilidad para iniciar el análisis. El sistema detecta duplicaciones, valida integridad, genera ranking de usuarios y guarda el historial de ejecución.
""")

# ------------------------
# CARGA DE ARCHIVOS .CSV
# ------------------------
st.sidebar.header("📂 Subir archivos")
compras_file = st.sidebar.file_uploader("Sube el archivo de facturas de COMPRAS (.csv)", type="csv")
conta_file = st.sidebar.file_uploader("Sube el archivo de facturas de CONTABILIDAD (.csv)", type="csv")

if compras_file and conta_file:
    compras = pd.read_csv(compras_file)
    contabilidad = pd.read_csv(conta_file)

    # Guardar archivos subidos (opcional, para mantener historial en disco)
    with open("facturas_compras.csv", "wb") as f:
        f.write(compras_file.getbuffer())
    with open("facturas_contabilidad.csv", "wb") as f:
        f.write(conta_file.getbuffer())

    # ------------------------
    # PROCESAMIENTO DE DATOS
    # ------------------------
    compras["estado_factura"] = compras["estado_factura"].str.lower().str.strip()
    compras["valida_estado"] = compras["estado_factura"] != "anulada"
    compras["duplicado_numero"] = compras.duplicated(subset=["numero_factura"], keep=False)
    compras["duplicado_fecha_prov_monto"] = compras.duplicated(subset=["fecha_emision", "proveedor_id", "monto_total"], keep=False)
    compras["duplicado_campos_clave"] = compras.duplicated(subset=["numero_factura", "monto_total", "proveedor_id"], keep=False)

    # Comparación entre archivos
    duplicados_entre_archivos = pd.merge(
        compras, contabilidad, on="clave_unica_interna", how="inner"
    )

    # Registro de la ejecución
    usuario = "auditor_streamlit"
    hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    resumen = {
        "Duplicados por número de factura": compras["duplicado_numero"].sum(),
        "Duplicados por fecha-proveedor-monto": compras["duplicado_fecha_prov_monto"].sum(),
        "Duplicados por campos clave": compras["duplicado_campos_clave"].sum(),
        "Duplicados entre compras y contabilidad": len(duplicados_entre_archivos),
        "Facturas válidas (no anuladas)": compras["valida_estado"].sum()
    }
    registro_log = {
        "usuario": usuario,
        "fecha_ejecucion": hora,
        **resumen
    }
    try:
        log = pd.read_csv("log_ejecuciones.csv")
        log = pd.concat([log, pd.DataFrame([registro_log])], ignore_index=True)
    except FileNotFoundError:
        log = pd.DataFrame([registro_log])
    log.to_csv("log_ejecuciones.csv", index=False)

    sospechosas = compras[
        compras["duplicado_numero"] | compras["duplicado_fecha_prov_monto"] | compras["duplicado_campos_clave"]
    ]

    ranking = sospechosas.groupby("usuario_registro").size().reset_index(name="cantidad_duplicados")
    ranking = ranking.sort_values(by="cantidad_duplicados", ascending=False)

    def calcular_hash(nombre_archivo):
        with open(nombre_archivo, "rb") as f:
            bytes_archivo = f.read()
            return hashlib.sha256(bytes_archivo).hexdigest()

    hash_compras = calcular_hash("facturas_compras.csv")
    hash_contabilidad = calcular_hash("facturas_contabilidad.csv")

    # ------------------------
    # INTERFAZ INTERACTIVA
    # ------------------------
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Datos cargados", 
        "🧮 Detección de duplicados", 
        "📈 Gráfico resumen", 
        "🧾 Log de auditoría", 
        "🔐 Verificación de integridad", 
        "🥇 Ranking de usuarios"
    ])

    with tab1:
        st.subheader("📋 Vista previa de los archivos")
        st.write("Facturas de compras:")
        st.dataframe(compras)
        st.write("Facturas de contabilidad:")
        st.dataframe(contabilidad)

    with tab2:
        st.subheader("🧮 Detección de facturas sospechosas")
        st.write("Facturas sospechosas por duplicación:")
        st.dataframe(sospechosas.drop(columns=[
            "duplicado_numero", "duplicado_fecha_prov_monto", "duplicado_campos_clave", "valida_estado"
        ]))
        
        with st.expander("📊 Resumen de hallazgos"):
            for k, v in resumen.items():
                st.markdown(f"- **{k}**: {v} registros")

    with tab3:
        st.subheader("📈 Gráfico de resumen")
        fig, ax = plt.subplots()
        ax.bar(resumen.keys(), resumen.values(), color="green")
        ax.set_ylabel("Cantidad")
        ax.set_xticklabels(resumen.keys(), rotation=45, ha='right')
        st.pyplot(fig)

    with tab4:
        st.subheader("🧾 Log de esta ejecución:")
        for k, v in registro_log.items():
            st.markdown(f"- **{k}**: {v}")
        
        st.markdown("### 📁 Historial de ejecuciones anteriores:")
        st.dataframe(log)

    with tab5:
        st.subheader("🔐 Verificación de integridad de archivos:")
        st.code(f"SHA-256 facturas_compras.csv: {hash_compras}", language="text")
        st.code(f"SHA-256 facturas_contabilidad.csv: {hash_contabilidad}", language="text")

    with tab6:
        st.subheader("🥇 Ranking de usuarios con más facturas sospechosas:")
        st.dataframe(ranking)

else:
    st.info("🔄 Por favor, sube los archivos .csv de compras y contabilidad desde el panel lateral izquierdo.")
