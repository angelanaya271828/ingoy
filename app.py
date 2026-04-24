import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd
import glob
import os
import plotly.express as px
from datetime import datetime, timedelta

import importlib
import mis_funciones
importlib.reload(mis_funciones)

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Tablero de Control - Planta",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# FUNCIONES DE LECTURA DE ARCHIVOS
# ==========================================

PATH_DB_OFFLINE = "offline_databases"
ARCHIVO_LOGO = "imagenes/logo_transparente.png"

@st.cache_data
def cargar_datos_offline():
    
    """Carga los maestros usando los desc_hoja correctos."""
    # Aquí aplicamos tus desc_hoja exactos
    ruta_ops = mis_funciones.obtener_ultimo_cache(PATH_DB_OFFLINE, "operadores")
    ruta_act = mis_funciones.obtener_ultimo_cache(PATH_DB_OFFLINE, "lista_actividades")
    ruta_wip = mis_funciones.obtener_ultimo_cache(PATH_DB_OFFLINE, "wip")
    
    if ruta_ops and ruta_wip and ruta_act:
        st.sidebar.success("✅ Modo Offline Activo")
        st.sidebar.caption("Últimos cachés detectados:")
        st.sidebar.code(f"{os.path.basename(ruta_ops)}\n{os.path.basename(ruta_act)}\n{os.path.basename(ruta_wip)}")
        
        if ruta_ops and ruta_act and ruta_wip:
            return pd.read_csv(ruta_ops), pd.read_csv(ruta_act), pd.read_csv(ruta_wip), [ruta_ops, ruta_act, ruta_wip]
        else:
            return None, None, None, []


# ==========================================
# MENÚ LATERAL Y LOGO
# ==========================================
with st.sidebar:

    if os.path.exists(ARCHIVO_LOGO):
        st.image(ARCHIVO_LOGO, width = 'stretch')
    st.markdown("---")
    
    # 2. Menú de navegación
    st.markdown("### 📋 Menú principal")
    opcion = st.radio(
        "Seleccione una vista:",
        ["Dashboard WIP", "Información de operadores", "Actividades Estándar", "Programación del Día"],
        label_visibility = "collapsed"
    )
    
    st.markdown("---")
    st.caption("Estatus: 🟢 Conectado (Offline)")


# ==========================================
# LÓGICA DE CONTENIDO
# ==========================================
df_ops, df_act, df_wip, rutas = cargar_datos_offline()

if df_ops is None:
    st.error("❗ No se encontraron archivos de caché en 'offline_databases'.")
    st.stop()

# --- VISTA: DASHBOARD WIP ---
if opcion == "Dashboard WIP":
    st.title("🏭 Estatus de Unidades en Planta")
    st.markdown("Visualización de las actividades actuales y su avance.")
    st.dataframe(df_wip, width='stretch', hide_index=True)

# --- VISTA: OPERADORES ---
elif opcion == "Información de operadores":
    st.title("Catálogo de operadores y asistencia")
    st.markdown("Análisis y disponibilidad de la fuerza laboral según el día seleccionado.")

    st.markdown("""
        <style>
        [data-testid="stMetric"] {
            text-align: center;
        }
        [data-testid="stMetricLabel"] {
            display: flex;
            justify-content: center;
            align-items: center;
        }
        </style>
        """, unsafe_allow_html=True)
    
    fecha_seleccionada = st.date_input("📅 Seleccione el día a analizar:", value="today")
    
    dias_semana_espanol = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    nombre_dia = dias_semana_espanol[fecha_seleccionada.weekday()]
    
    total_operadores = len(df_ops)
    df_ops_activos = df_ops[df_ops['DIA_DESCANSO'] != nombre_dia]
    activos_hoy = len(df_ops_activos)
    faltas = 0
    vacaciones = 0
    
    st.markdown("### 📊 Indicadores diarios")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.metric("Total de Operadores", total_operadores)
    with kpi2:
        st.metric(f"Activos el {nombre_dia}", activos_hoy)
    with kpi3:
        st.metric("Vacaciones programadas", vacaciones)
    with kpi4:
        st.metric("Faltas", faltas)
        
    st.markdown("---")
    
    # Total por área en el catálogo
    resumen_total = df_ops.groupby('AREA').size().reset_index(name='Total de operadores')
    # Activos por área hoy
    resumen_activos = df_ops_activos.groupby('AREA').size().reset_index(name='Operadores que asistieron')
    
    # Unir ambas tablas
    df_resumen_area = pd.merge(resumen_total, resumen_activos, on='AREA', how='left').fillna(0)
    df_resumen_area['Operadores que asistieron'] = df_resumen_area['Operadores que asistieron'].astype(int)
    
    # Calcular porcentaje de asistencia
    df_resumen_area['% Asistencia'] = (df_resumen_area['Operadores que asistieron'] / df_resumen_area['Total de operadores'] * 100).round(1)

    # Aplicar Estilo de Mapa de Calor
    def estilo_fila_completa(row):
        # Obtenemos el valor de la columna de porcentaje
        val = row['% Asistencia']
        
        # Usamos el mapa de colores Rojo-Amarillo-Verde (RdYlGn)
        cmap = plt.get_cmap('RdYlGn')
        norm = plt.Normalize(0, 100) # Normalizar de 0 a 100
        
        # Convertimos el valor en un color hexadecimal
        color = mcolors.to_hex(cmap(norm(val)))
        
        # Retornamos el estilo para cada celda de la fila
        # Usamos color: black para que el texto sea legible sobre el fondo de color
        return [f'background-color: {color}; color: black; font-weight: bold;' for _ in row]

    # Aplicamos la función a lo largo del eje de las columnas (axis=1)
    df_estilizado = df_resumen_area.style.apply(estilo_fila_completa, axis=1).format({
        '% Asistencia': '{:.1f}%'
    })

    # 6. Mostrar Resumen por Área
    st.markdown("### 🏬 Resumen de Asistencia por Área")
    st.dataframe(df_estilizado, width='stretch', hide_index=True)

    st.markdown("---")

    # Detalle Individual
    with st.expander(f"👁️ Ver detalle de operadores activos el {nombre_dia}"):
        df_viz_ops_activos = df_ops_activos[["AREA", "OPERADOR"]].sort_values(by=['AREA', 'OPERADOR'], ascending=[True, True]).copy()
        st.dataframe(df_viz_ops_activos, width='stretch', hide_index=True)
    
    

# --- VISTA: ACTIVIDADES ---
elif opcion == "Actividades Estándar":
    st.title("📋 Diccionario de Actividades y Flujo Teórico")
    st.markdown("Esta sección muestra la secuencia maestra de producción respetando turnos de 8h y descansos dominicales.")

    with st.expander("📄 Ver tabla de datos maestros"):
        st.dataframe(df_act, width='stretch', hide_index=True)

    st.markdown("---")
    st.subheader("📊 Cronograma Maestro (Gantt Teórico)")

    # --- LÓGICA AVANZADA PARA CALCULAR TIEMPOS (TURNOS DE 8H Y SIN DOMINGOS) ---
    def calcular_fin_con_restricciones(inicio, duracion_hrs):
        tiempo_restante = duracion_hrs
        actual = inicio
        
        while tiempo_restante > 0:
            # 1. Si es domingo, saltar al lunes a las 08:00 AM
            if actual.weekday() == 6:
                actual = (actual + timedelta(days=1)).replace(hour=8, minute=0)
                continue
            
            # 2. Definir fin de turno del día actual (16:00 PM - Asumiendo 8h desde las 08:00)
            fin_turno_hoy = actual.replace(hour=16, minute=0)
            
            # 3. Si ya pasó el turno, saltar al día siguiente a las 08:00 AM
            if actual >= fin_turno_hoy:
                actual = (actual + timedelta(days=1)).replace(hour=8, minute=0)
                continue
            
            # 4. Calcular espacio disponible hoy
            espacio_hoy = (fin_turno_hoy - actual).total_seconds() / 3600
            
            if tiempo_restante <= espacio_hoy:
                # La tarea cabe en lo que queda del día
                actual = actual + timedelta(hours=tiempo_restante)
                tiempo_restante = 0
            else:
                # La tarea se corta y sigue mañana
                tiempo_restante -= espacio_hoy
                actual = (actual + timedelta(days=1)).replace(hour=8, minute=0)
        
        return actual

    def generar_datos_gantt_v2(df):
        df_gantt = df.copy()
        df_gantt['DEPENDENCIA'] = df_gantt['DEPENDENCIA'].fillna('').astype(str)
        
        # Inicio: Lunes 20 de Abril 2026 (Para evitar iniciar en domingo por error)
        base_time = datetime(2026, 4, 20, 8, 0)
        tiempos_fin = {} 
        data_plot = []

        for _, row in df_gantt.sort_values(['ID_PROCESO', 'ID_SUBPROCESO']).iterrows():
            key = str(row['KEY_SUBPROCESO'])
            duracion = float(row['TIEMPO'])
            deps = [d.strip() for d in row['DEPENDENCIA'].split(',')] if row['DEPENDENCIA'] != '' else []

            # Calcular Inicio
            if not deps or deps == ['']:
                start = base_time
            else:
                tiempos_deps = [tiempos_fin.get(d, base_time) for d in deps]
                start = max(tiempos_deps)
            
            # Ajustar inicio si cae en domingo o fuera de turno
            if start.weekday() == 6:
                start = (start + timedelta(days=1)).replace(hour=8, minute=0)
            elif start.hour >= 16:
                start = (start + timedelta(days=1)).replace(hour=8, minute=0)

            # Calcular Fin respetando restricciones
            end = calcular_fin_con_restricciones(start, duracion)
            tiempos_fin[key] = end

            data_plot.append({
                'Tarea': f"{key} - {row['ACTIVIDAD']}",
                'Inicio': start,
                'Fin': end,
                'Área': row['AREA'],
                'Proceso': row['DESC_PROCESO']
            })

        return pd.DataFrame(data_plot)

    df_plot = generar_datos_gantt_v2(df_act)

    # --- CREAR GRÁFICO ---
    fig = px.timeline(
        df_plot, 
        x_start="Inicio", 
        x_end="Fin", 
        y="Tarea", 
        color="Área",
        hover_data=["Proceso"],
        template="plotly_dark"
    )

    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        height=1600, # Aumentamos la altura para mejor lectura de las 87 tareas
        font_color="#E6EDF3",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title="Línea de Tiempo (Jornadas de 8h)",
        yaxis_title=None
    )

    st.plotly_chart(fig, use_container_width=True)


# --- VISTA: PROGRAMACIÓN ---
elif opcion == "Programación del Día":
    st.title("📅 Programación Final de Actividades")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        fecha_target = st.text_input("Ingrese fecha (YYYY-MM-DD):", value="2026-04-22")
    
    if st.button("🔍 Buscar Programación", type="primary"):
        # Buscamos archivos que contengan 'asignacion' y la fecha
        patron_plan = os.path.join(PATH_DB_OFFLINE, "**", f"*asignacion_{fecha_target}*.csv")
        archivos_plan = glob.glob(patron_plan, recursive=True)
        
        if archivos_plan:
            archivos_plan.sort(reverse=True)
            df_plan = pd.read_csv(archivos_plan[0])
            st.success(f"✅ Cargado: {os.path.basename(archivos_plan[0])}")
            st.dataframe(df_plan, width = 'stretch', hide_index=True)
            
            # Estadísticas rápidas en el modo oscuro
            m1, m2 = st.columns(2)
            m1.metric("Actividades Totales", len(df_plan))
            m2.metric("Unidades Atendidas", df_plan['ID_UNIDAD'].nunique())
        else:
            st.warning(f"No se encontró ninguna asignación para la fecha: {fecha_target}")