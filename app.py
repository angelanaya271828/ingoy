import streamlit as st
import pandas as pd
import glob
import os

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(page_title="Visor de Producción", page_icon="🏭", layout="wide")
st.title("🏭 Visor de Asignación de Actividades")

# ==========================================
# 1. FUNCIONES DE LECTURA DE ARCHIVOS
# ==========================================

PATH_DATABASES = "offline_databases"

def obtener_archivo_mas_reciente(patron_nombre):
    """Busca archivos que coincidan con el patrón dentro de la subcarpeta."""
    # Construimos la ruta de búsqueda: "offline/databases/NombreDelArchivo*.csv"
    patron_completo = os.path.join(PATH_DATABASES, f"{patron_nombre}*.csv")
    lista_archivos = glob.glob(patron_completo)
    
    if not lista_archivos:
        return None
    
    # Retorna el más reciente según fecha de modificación
    return max(lista_archivos, key=os.path.getmtime)

@st.cache_data
def cargar_datos_maestros():
    """Carga los 3 archivos maestros desde la subcarpeta."""
    ruta_ops = obtener_archivo_mas_reciente("Bosquejo de Gannt_Operadores")
    ruta_wip = obtener_archivo_mas_reciente("Bosquejo de Gannt_WIP")
    ruta_act = obtener_archivo_mas_reciente("Bosquejo de Gannt_Actividades")
    
    if ruta_ops and ruta_wip and ruta_act:
        st.sidebar.success(f"✅ Conectado a: {PATH_DATABASES}")
        return pd.read_csv(ruta_ops), pd.read_csv(ruta_wip), pd.read_csv(ruta_act)
    else:
        st.error(f"❌ Error: No se encontraron archivos maestros en '{PATH_DATABASES}'")
        st.info("Asegúrate de que la carpeta se llame exactamente 'offline' y dentro tenga 'databases'.")
        st.stop()

# Título y carga inicial
st.title("🏭 Visor de Producción")
df_operadores, df_wip, df_lista_actividades = cargar_datos_maestros()

# ==========================================
# 2. INTERFAZ DE USUARIO (PESTAÑAS)
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "👷‍♂️ Operadores", 
    "📋 Actividades Estándar", 
    "🚌 WIP (Inicio del Día)", 
    "📅 Programación Final (Offline)"
])

# --- PESTAÑA 1, 2 y 3 (Se mantienen igual para visualización) ---
with tab1:
    st.header("Catálogo de Operadores")
    st.dataframe(df_operadores, use_container_width=True, hide_index=True)

with tab2:
    st.header("Lista de Actividades Estándar")
    st.dataframe(df_lista_actividades, use_container_width=True, hide_index=True)

with tab3:
    st.header("Work in Progress (Estatus Actual)")
    st.dataframe(df_wip, use_container_width=True, hide_index=True)

# --- PESTAÑA 4: PROGRAMACIÓN (LECTURA DE OFFLINE_DATABASES) ---
with tab4:
    st.header("Plan de Asignación Guardado")
    st.markdown("Busca y visualiza los planes generados previamente en la carpeta `offline_databases`.")

    # Selección de fecha para buscar el archivo
    # Nota: Asegúrate de que el formato coincida con como guardas el archivo
    fecha_input = st.text_input("Introduce la fecha del plan (ej. 2026-04-22 o Miércoles):", value="2026-04-22")
    
    # Construcción de la ruta según tu estructura
    nombre_archivo = f"Plan_de_asignacion_{fecha_input}.csv"
    ruta_plan = os.path.join("offline_databases", nombre_archivo)

    if st.button("Cargar Plan desde Carpeta"):
        if os.path.exists(ruta_plan):
            df_plan_offline = pd.read_csv(ruta_plan)
            st.success(f"✅ Archivo encontrado: {nombre_archivo}")
            
            # Visualización del plan
            st.dataframe(df_plan_offline, use_container_width=True, hide_index=True)
            
            # Métricas del plan cargado
            col1, col2 = st.columns(2)
            col1.metric("Tareas Programadas", len(df_plan_offline))
            col2.metric("Unidades en Plan", df_plan_offline['ID_UNIDAD'].nunique() if 'ID_UNIDAD' in df_plan_offline else 0)
            
            # Gráfico de carga por operador si la columna existe
            if 'OPERADOR' in df_plan_offline and 'TIEMPO' in df_plan_offline:
                st.subheader("Carga de Trabajo Programada")
                carga = df_plan_offline.groupby('OPERADOR')['TIEMPO'].sum()
                st.bar_chart(carga)
        else:
            st.error(f"❌ No se encontró el archivo: `{ruta_plan}`. Verifica que la fecha sea correcta y que el archivo esté en la carpeta `offline_databases`.")