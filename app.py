import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards
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
    page_title = "Ingoy: Dashboard",
    page_icon = "imagenes\ingoy_final.ico",
    layout = "wide",
    initial_sidebar_state = "expanded"
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
        ["Información de operadores", "Actividades estándar", "Programación del día"],
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

# --- VISTA: OPERADORES ---
if opcion == "Información de operadores":
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
    
    # Creamos las 4 columnas
    k1, k2, k3, k4 = st.columns(4)
    
    with k1:
        mis_funciones.crear_tarjeta_kpi(
            titulo="Total de operadores", 
            valor=total_operadores, 
            descripcion="Registrados en el sistema"
        )
    with k2:
        mis_funciones.crear_tarjeta_kpi(
            titulo=f"Activos el {nombre_dia}", 
            valor=activos_hoy, 
            descripcion="Personal en turno"
        )
    with k3:
        mis_funciones.crear_tarjeta_kpi(
            titulo="Faltas", 
            valor=0, 
            descripcion="Ausencias no justificadas"
        )
    with k4:
        mis_funciones.crear_tarjeta_kpi(
            titulo="Vacaciones", 
            valor=0, 
            descripcion="Periodos programados"
        )

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
        val = row['% Asistencia']
        
        # Define tus colores hexadecimales
        mis_colores = ["#51A2FF", "#162456"] 
        
        # Creamos la paleta (cmap) personalizada
        mi_cmap = mcolors.LinearSegmentedColormap.from_list("Paleta_Ingoy", mis_colores)
        
        # Normalizamos de 0 a 100
        norm = mcolors.Normalize(vmin=0, vmax=100)
        
        # Calculamos el color exacto para la celda
        color_fondo = mcolors.to_hex(mi_cmap(norm(val)))
        
        # Retornamos el estilo
        return [f'background-color: {color_fondo}; color: #000000; font-weight: 600;' for _ in row]

    # Aplicamos la función a lo largo del eje de las columnas (axis=1)
    df_estilizado = df_resumen_area.style.apply(estilo_fila_completa, axis=1).format({
        '% Asistencia': '{:.1f}%'
    })

    # 6. Mostrar Resumen por Área
    st.markdown("### 🏬 Resumen de Asistencia por Área")
    st.dataframe(df_estilizado, width='stretch', hide_index=True)

    st.markdown("---")

    # Detalle Individual
    with st.expander(f"Ver detalle de operadores activos el {nombre_dia}"):
        df_viz_ops_activos = df_ops_activos[["AREA", "OPERADOR"]].sort_values(by=['AREA', 'OPERADOR'], ascending=[True, True]).copy()
        st.dataframe(df_viz_ops_activos, width='stretch', hide_index=True)
    
    

# --- VISTA: ACTIVIDADES ---
elif opcion == "Actividades estándar":
    st.title("📋 Diccionario de Actividades y Flujo Teórico")
    st.markdown("Estructura de Desglose del Trabajo (Secuencia Maestra de Producción).")

    if df_act is not None:
        
        # ==========================================
        # FILTRO ESTRICTO POR MODELO
        # ==========================================
        st.subheader("🔍 Filtrar Receta Maestra")
        
        # Verificamos si la columna MODELO ya existe en tu archivo actual
        tiene_columna_modelo = 'MODELO' in df_act.columns
        
        if tiene_columna_modelo:
            unidades_disponibles = sorted(df_act['MODELO'].dropna().unique())
        else:
            # Respaldo temporal por si tu CSV actual aún no tiene la columna escrita
            unidades_disponibles = ["Modelo Estándar (Único)"]
        
        # Mostramos el menú desplegable
        unidad_seleccionada = st.selectbox("Selecciona el Modelo:", unidades_disponibles)
        st.markdown("---")
        
        # Filtramos la tabla maestra solo si la columna existe
        if tiene_columna_modelo:
            df_act_filtrado = df_act[df_act['MODELO'] == unidad_seleccionada].copy()
        else:
            df_act_filtrado = df_act.copy()

        # ==========================================
        # CREACIÓN DE LA JERARQUÍA (PROCESO -> SUBPROCESO)
        # ==========================================
        # Usamos nombres estrictos según tu CSV anterior
        col_subproc = 'ID_SUBPROCESO'
        
        if 'ID_PROCESO' in df_act_filtrado.columns and col_subproc in df_act_filtrado.columns:
            df_act_sorted = df_act_filtrado.sort_values(by=['ID_PROCESO', col_subproc])
        else:
            df_act_sorted = df_act_filtrado.copy()
        
        filas_jerarquia = []
        
        if 'ID_PROCESO' in df_act_sorted.columns:
            procesos_unicos = df_act_sorted[['ID_PROCESO', 'DESC_PROCESO']].drop_duplicates()
            
            for _, row_proc in procesos_unicos.iterrows():
                id_proc = row_proc['ID_PROCESO']
                desc_proc = str(row_proc['DESC_PROCESO']).upper() if pd.notna(row_proc['DESC_PROCESO']) else "PROCESO DESCONOCIDO"
                
                # Fila Padre (Proceso)
                filas_jerarquia.append({
                    'Estructura de Actividades': f"{int(id_proc)}. {desc_proc}",
                    'Área': '',
                    'Tiempo (hrs)': '',
                    'Dependencia': ''
                })
                
                # Filas Hijo (Actividades)
                subprocesos = df_act_sorted[df_act_sorted['ID_PROCESO'] == id_proc]
                for _, row_sub in subprocesos.iterrows():
                    key_sub = str(row_sub.get('KEY_SUBPROCESO', ''))
                    actividad = str(row_sub.get('ACTIVIDAD', ''))
                    area = str(row_sub.get('AREA', '')) if pd.notna(row_sub.get('AREA')) else ''
                    tiempo = str(row_sub.get('TIEMPO', '')) if pd.notna(row_sub.get('TIEMPO')) else ''
                    dep = str(row_sub.get('DEPENDENCIA', '')) if pd.notna(row_sub.get('DEPENDENCIA')) else ''
                    
                    filas_jerarquia.append({
                        'Estructura de Actividades': f"    ↳ {key_sub} - {actividad}", 
                        'Área': area,
                        'Tiempo (hrs)': tiempo,
                        'Dependencia': dep
                    })
                    
            df_jerarquia = pd.DataFrame(filas_jerarquia)

            if not df_jerarquia.empty:
                # Diseño corporativo: Fondo oscuro y letras azules para los Procesos principales
                def resaltar_procesos(row):
                    if row['Área'] == '':
                        return ['background-color: #1A2235; color: #51A2FF; font-weight: bold;'] * len(row)
                    else:
                        return [''] * len(row)

                df_estilizado = df_jerarquia.style.apply(resaltar_procesos, axis=1)

                st.dataframe(
                    df_estilizado, 
                    width='stretch', 
                    hide_index=True,
                    height=800 
                )
            else:
                st.info("ℹ️ No hay actividades registradas para este modelo en particular.")
        else:
            st.error("❌ Faltan las columnas 'ID_PROCESO' o 'ID_SUBPROCESO' en la base de datos maestra.")
    else:
        st.warning("⚠️ No se encontró la base de datos de actividades estándar.")


# --- VISTA: PROGRAMACIÓN ---
elif opcion == "Programación del día":
    st.title("📅 Programación Final y Asignaciones")
    
    # 1. Buscador de fecha
    col1, col2 = st.columns([1, 3])
    with col1:
        fecha_target = st.text_input("Ingrese fecha del plan (YYYY-MM-DD):", value="2026-04-25")
    
    # Inicializamos la "memoria" si no existe
    if 'df_plan' not in st.session_state:
        st.session_state.df_plan = None
        st.session_state.nombre_archivo = ""
    
    # 2. El botón AHORA SOLO SIRVE PARA GUARDAR EN MEMORIA
    if st.button("🔍 Buscar Programación", type="primary"):
        patron_plan = os.path.join(PATH_DB_OFFLINE, "**", f"*asignacion_{fecha_target}*.csv")
        archivos_plan = glob.glob(patron_plan, recursive=True)
        
        if archivos_plan:
            archivos_plan.sort(reverse=True)
            archivo_a_leer = archivos_plan[0]
            
            try:
                # Verificamos si el archivo pesa más de 0 bytes antes de leer
                if os.path.getsize(archivo_a_leer) == 0:
                    raise pd.errors.EmptyDataError
                    
                # Guardamos la tabla en la mochila de Streamlit
                st.session_state.df_plan = pd.read_csv(archivo_a_leer)
                st.session_state.nombre_archivo = os.path.basename(archivo_a_leer)
                
            except pd.errors.EmptyDataError:
                st.warning(f"⚠️ El archivo '{os.path.basename(archivo_a_leer)}' está vacío. El motor no generó asignaciones para este día.")
                st.session_state.df_plan = None # Borramos la memoria por si había uno anterior
        else:
            st.warning(f"No se encontró ninguna asignación para la fecha: {fecha_target}")
            st.session_state.df_plan = None

    # 3. MOSTRAR VISUALIZACIÓN (Depende de la memoria, no del botón)
    if st.session_state.df_plan is not None:
        st.success(f"✅ Plan cargado: {st.session_state.nombre_archivo}")
        
        # Recuperamos la tabla de la memoria
        df_plan = st.session_state.df_plan
        
        # --- CREAMOS LAS DOS SECCIONES (TABS) ---
        tab_operadores, tab_unidades = st.tabs([
            "👷‍♂️ 1. Resumen por Operador", 
            "🚌 2. Resumen por Unidad (Gantt)"
        ])
        
        # ==========================================
        # APARTADO 1: RESUMEN POR OPERADOR
        # ==========================================
        with tab_operadores:
            st.subheader("📊 KPIs Generales del Día")
            
            # Cálculos rápidos
            total_tareas_hoy = len(df_plan)
            ops_asignados = df_plan['OPERADOR'].nunique()
            horas_totales = df_plan['TIEMPO'].sum() if 'TIEMPO' in df_plan.columns else 0
            
            # KPIs Superiores
            k1, k2, k3 = st.columns(3)
            with k1:
                mis_funciones.crear_tarjeta_kpi("Tareas Asignadas", total_tareas_hoy, "En toda la planta")
            with k2:
                mis_funciones.crear_tarjeta_kpi("Operadores Activos", ops_asignados, "Con tareas programadas")
            with k3:
                mis_funciones.crear_tarjeta_kpi("Carga Total (Hrs)", f"{horas_totales:.1f}", "Suma de tiempos estimados")
            
            st.write("")
            st.markdown("---")

            st.subheader("📈 Balanceo de Carga por Operador")
            
            if 'TIEMPO' in df_plan.columns and 'OPERADOR' in df_plan.columns and 'AREA' in df_plan.columns:
                import plotly.express as px
                import matplotlib.colors as mcolors
                
                # 1. Agrupamos y sumamos las horas por operador y área
                df_carga = df_plan.groupby(['OPERADOR', 'AREA'])['TIEMPO'].sum().reset_index()
                
                # 2. Ordenamos de MENOR a MAYOR. 
                # Plotly dibuja de abajo hacia arriba, así el operador con más carga quedará hasta arriba.
                df_carga = df_carga.sort_values(by='TIEMPO', ascending=True)
                
                # 3. Creamos la paleta de colores personalizada
                areas_unicas = df_carga['AREA'].nunique()
                mis_colores = ["#51A2FF", "#162456"] # Tu gradiente azul
                
                if areas_unicas > 1:
                    cmap_azules = mcolors.LinearSegmentedColormap.from_list("Paleta_Azul", mis_colores)
                    # Extraemos los colores exactos dividiendo el gradiente entre el número de áreas
                    colores_generados = [mcolors.to_hex(cmap_azules(i / (areas_unicas - 1))) for i in range(areas_unicas)]
                else:
                    colores_generados = [mis_colores[0]]

                # 4. Dibujamos la gráfica HORIZONTAL
                fig_carga = px.bar(
                    df_carga, 
                    x='TIEMPO',       # Ahora el Tiempo va en el eje X
                    y='OPERADOR',     # Los Nombres van en el eje Y
                    color='AREA',
                    orientation='h',  # 'h' = Horizontal
                    text_auto='.1f',
                    color_discrete_sequence=colores_generados, # Inyectamos tu paleta de azules
                    template="plotly_dark",
                    labels={'TIEMPO': 'Horas Asignadas', 'OPERADOR': 'Operador', 'AREA': 'Área'}
                )
                
                # 5. Ajustes estéticos y LÍNEA VERTICAL de 8 horas
                fig_carga.add_vline(
                    x=8, 
                    line_dash="dot", 
                    line_color="#E53935", # Mantenemos rojo para que sea una alerta clara
                    annotation_text="Límite (8h)",
                    annotation_position="top right",
                    annotation_font_color="#E53935"
                )
                
                fig_carga.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    # Altura dinámica: crece si hay muchos operadores para que no se amontonen los nombres
                    height=max(400, len(df_carga) * 35), 
                    margin=dict(l=10)
                )
                
                st.plotly_chart(fig_carga, use_container_width=True)
            else:
                st.info("Faltan datos de TIEMPO, OPERADOR o AREA en el archivo para generar la gráfica.")

            st.markdown("---")

            st.subheader("🔍 Filtrar Asignación por Personal")
            
            col_filtro1, col_filtro2 = st.columns(2)
            
            # Filtro de Área
            areas_disponibles = df_plan['AREA'].dropna().unique() if 'AREA' in df_plan.columns else ["N/A"]
            with col_filtro1:
                area_sel = st.selectbox("1. Selecciona el Área:", sorted(areas_disponibles))
            
            # Filtro de Operador (depende del Área)
            if 'AREA' in df_plan.columns:
                ops_en_area = df_plan[df_plan['AREA'] == area_sel]['OPERADOR'].dropna().unique()
            else:
                ops_en_area = df_plan['OPERADOR'].unique()
                
            with col_filtro2:
                op_sel = st.selectbox("2. Selecciona el Operador:", sorted(ops_en_area))
            
            # Mostramos la tabla filtrada para el operador seleccionado
            df_op_filtrado = df_plan[df_plan['OPERADOR'] == op_sel]
            
            st.markdown(f"**Actividades asignadas a: {op_sel}**")
            st.dataframe(df_op_filtrado, width='stretch', hide_index=True)

        # ==========================================
        # APARTADO 2: RESUMEN POR UNIDAD (GANTT ESTATUS)
        # ==========================================
        with tab_unidades:
            st.subheader("📊 Análisis de Avance y Programación")

            # --- NOMBRES EXACTOS SEGÚN TU CSV ---
            COL_DEPS = 'DEPENDENCIA' 
            COL_KEY = 'KEY_SUBPROCESO'
            COL_SUBPROC = 'ID_SUBPROCESO'

            if 'ID_UNIDAD' in df_plan.columns and df_act is not None:
                # --- 1. GRÁFICA DE BARRAS DE PROGRESO ESTRATÉGICO ---
                total_peso_maestro = df_act['TIEMPO'].sum()
                unidades_en_plan = sorted(df_plan['ID_UNIDAD'].dropna().unique())
                
                datos_progreso = []
                for unidad in unidades_en_plan:
                    hoy_unit = df_plan[df_plan['ID_UNIDAD'] == unidad]['ACTIVIDAD'].tolist()
                    indices_hoy = df_act[df_act['ACTIVIDAD'].isin(hoy_unit)].index
                    
                    if not indices_hoy.empty:
                        idx_primera_tarea = indices_hoy.min()
                        peso_previo = df_act.iloc[:idx_primera_tarea]['TIEMPO'].sum()
                        peso_hoy = df_act[df_act['ACTIVIDAD'].isin(hoy_unit)]['TIEMPO'].sum()
                    else:
                        peso_previo, peso_hoy = 0, 0
                        
                    perc_previo = (peso_previo / total_peso_maestro) * 100
                    perc_proyectado = ((peso_previo + peso_hoy) / total_peso_maestro) * 100
                    
                    datos_progreso.append({'Unidad': unidad, 'Estatus': '1. Progreso Previo', 'Porcentaje': round(perc_previo, 1)})
                    datos_progreso.append({'Unidad': unidad, 'Estatus': '2. Proyectado Hoy', 'Porcentaje': round(perc_proyectado, 1)})

                df_progreso = pd.DataFrame(datos_progreso)
                import plotly.express as px
                fig_prog = px.bar(
                    df_progreso, x='Unidad', y='Porcentaje', color='Estatus',
                    barmode='group', text_auto='.1f',
                    color_discrete_map={'1. Progreso Previo': '#2A3654', '2. Proyectado Hoy': '#51A2FF'},
                    template="plotly_dark", title="Incremento de Avance Proyectado (%)"
                )
                fig_prog.update_layout(yaxis_range=[0, 100], paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_prog, use_container_width=True)

                st.markdown("---")
                
                # --- 2. SELECTOR Y MOTOR DE GANTT CON RUTA CRÍTICA ESTRICTA ---
                unidad_sel = st.selectbox("Selecciona la Unidad para detalle:", unidades_en_plan)
                tareas_hoy_unidad = df_plan[df_plan['ID_UNIDAD'] == unidad_sel]['ACTIVIDAD'].tolist()
                
                # Ordenamos usando las columnas reales de tu CSV
                df_gantt_u = df_act.sort_values(['ID_PROCESO', COL_SUBPROC]).copy()
                
                # Mapeo de operadores
                mapa_op = dict(zip(df_plan[df_plan['ID_UNIDAD'] == unidad_sel]['ACTIVIDAD'], 
                                   df_plan[df_plan['ID_UNIDAD'] == unidad_sel]['OPERADOR']))

                # Asignación de estatus visual
                estatus_lista, op_lista = [], []
                encontramos_hoy = False
                for act in df_gantt_u['ACTIVIDAD']:
                    if act in tareas_hoy_unidad:
                        estatus_lista.append("Programado Hoy")
                        op_lista.append(mapa_op.get(act, "Pendiente de Asignar"))
                        encontramos_hoy = True
                    elif not encontramos_hoy:
                        estatus_lista.append("Ya Hecho")
                        op_lista.append("Finalizado")
                    else:
                        estatus_lista.append("Pendiente")
                        op_lista.append("N/A")
                
                df_gantt_u['ESTATUS'] = estatus_lista
                df_gantt_u['OPERADOR'] = op_lista

                # --- MOTOR DE DEPENDENCIAS REALES ---
                from datetime import datetime, timedelta
                import ast
                
                base_t = datetime.today().replace(hour=8, minute=0, second=0, microsecond=0)
                tiempos_fin = {} 
                inicios, fines = [], []
                
                df_gantt_u['TIEMPO'] = pd.to_numeric(df_gantt_u['TIEMPO'], errors='coerce').fillna(1)
                
                # Limpiamos los Key Subprocesos (Ej: "1.1", "1.3.1")
                df_gantt_u[COL_KEY] = df_gantt_u[COL_KEY].astype(str).str.strip()

                for idx, row in df_gantt_u.iterrows():
                    key = row[COL_KEY]
                    duracion = timedelta(hours=row['TIEMPO'])
                    
                    # 1. Leemos la columna "DEPENDENCIA" de tu CSV
                    deps = []
                    if COL_DEPS in df_gantt_u.columns and pd.notna(row[COL_DEPS]):
                        val_deps = str(row[COL_DEPS]).strip()
                        # Extraemos valores separados por coma (ej: "1.1", "1.2")
                        if val_deps and val_deps.lower() not in ["nan", "none", ""]:
                            try:
                                if val_deps.startswith('['):
                                    deps = [str(d).strip() for d in ast.literal_eval(val_deps)]
                                else:
                                    deps = [d.strip() for d in val_deps.split(',')]
                            except:
                                deps = []

                    # 2. Calculamos la hora de inicio basada en cuándo terminan sus dependencias
                    if not deps:
                        fecha_inicio = base_t 
                    else:
                        # Busca a qué hora terminó cada pre-requisito.
                        tiempos_deps = [tiempos_fin.get(d, base_t) for d in deps]
                        fecha_inicio = max(tiempos_deps) if tiempos_deps else base_t
                    
                    fecha_fin = fecha_inicio + duracion
                    
                    # Guardamos resultados
                    inicios.append(fecha_inicio)
                    fines.append(fecha_fin)
                    tiempos_fin[key] = fecha_fin # Guardamos en memoria para que las siguientes tareas lo vean

                # Inyectamos los tiempos calculados al DataFrame
                df_gantt_u['Inicio'] = inicios
                df_gantt_u['Fin'] = fines
                df_gantt_u['Tarea_Visual'] = df_gantt_u[COL_KEY] + " - " + df_gantt_u['ACTIVIDAD']

                # --- 3. FILTRAR Y DIBUJAR ---
                # Quitamos lo pendiente para dejar el gráfico limpio
                df_final_gantt = df_gantt_u[df_gantt_u['ESTATUS'] != "Pendiente"].copy()

                fig_gantt = px.timeline(
                    df_final_gantt, x_start="Inicio", x_end="Fin", y="Tarea_Visual", color="ESTATUS",
                    color_discrete_map={"Ya Hecho": "#2A3654", "Programado Hoy": "#00C853"},
                    hover_data=["AREA", "TIEMPO", "OPERADOR"], template="plotly_dark"
                )
                
                fig_gantt.update_yaxes(autorange="reversed")
                fig_gantt.update_xaxes(showticklabels=False) # Ocultamos fechas dummy
                fig_gantt.update_layout(
                    height=max(400, len(df_final_gantt) * 25), 
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    title=f"Secuencia de Trabajo Exacta: Unidad {unidad_sel}"
                )
                st.plotly_chart(fig_gantt, use_container_width=True)
            else:
                st.warning("No se pudo cargar la información de planificación o el catálogo maestro.")