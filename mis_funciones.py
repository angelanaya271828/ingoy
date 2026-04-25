
import warnings
warnings.filterwarnings("ignore", category = FutureWarning)

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
import numpy as np
import pandas as pd
import os
import glob
from datetime import datetime


def obtener_ultimo_cache(ruta, desc_hoja):
    patron = os.path.join(ruta, f"informacion_{desc_hoja}_*.csv")
    archivos = glob.glob(patron)

    if not archivos:
        return None

    archivos.sort(reverse = True)
    return archivos[0]


def lectura_hoja_gs(id_libro, 
                    id_hoja, 
                    desc_hoja, 
                    keys = "secrets.json", 
                    ruta_db_offline = "offline_databases", 
                    flag_lectura_offline = False):
    
    # Nombre del archivo con timestamp
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archivo_db_offline = os.path.join(
        ruta_db_offline,
        f"informacion_{desc_hoja}_{fecha}.csv"
    )

    if not flag_lectura_offline:
        
        try:

            print("🔄 Iniciando lectura online...")

            # Lectura de credencials y acceso al libro
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            credenciales = Credentials.from_service_account_file(keys, scopes = scopes)
            cliente = gspread.authorize(credenciales)
            
            base_datos_ingoy = cliente.open_by_key(id_libro)
            hoja = base_datos_ingoy.get_worksheet_by_id(int(id_hoja))

            datos = hoja.get_all_records()
            df = pd.DataFrame(datos)
            print(f"   - Total de registros: {len(df)}")
            print(df.head(3))

            # Guardar nueva versión
            df.to_csv(archivo_db_offline, index = False)
            print(f"💾 Archivo guardado para lectura offline en: {archivo_db_offline}")

            return df
        
        except Exception as e:
            print(f"❗ Error en la lectura online: {e}")
            print("🔁 Intentando cargar versión anterior offline...")

    # Buscar último archivo disponible
    archivo_cache = obtener_ultimo_cache(ruta_db_offline, desc_hoja)

    if archivo_cache:
        df = pd.read_csv(archivo_cache)
        print(f"📂 Total de registros: {len(df)}")
        return df
    else:
        raise Exception("❗ No hay datos online ni cache local disponible.")
    

def crear_tarjeta_kpi(titulo, valor, descripcion=""):
    """
    Genera una tarjeta HTML/CSS con el diseño azul moderno.
    """
    html_card = f"""
    <div style="
        background-color: #1A2235; /* Azul marino profundo (se funde mejor con el fondo oscuro) */
        border: 1px solid #2A3654; /* Borde sutil azulado para darle profundidad */
        border-radius: 16px; 
        padding: 24px; 
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        font-family: 'Inter', sans-serif;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); /* Sombra para despegarlo del fondo */
    ">
        <div>
            <div style="color: #FFFFFF; font-size: 3rem; font-weight: 800; line-height: 1.1; margin-bottom: 8px;">
                {valor}
            </div>
            <div style="color: #8BA1C8; font-size: 1rem; font-weight: 600; line-height: 1.4; margin-bottom: 20px;">
                {titulo} <br> <span style="font-size: 0.85rem; font-weight: 400; opacity: 0.7;">{descripcion}</span>
            </div>
        </div>
        <div style="color: #4A81FF; font-size: 0.8rem; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;">
        </div>
    </div>
    """
    # st.markdown renderiza el HTML directamente en Streamlit
    st.markdown(html_card, unsafe_allow_html=True)