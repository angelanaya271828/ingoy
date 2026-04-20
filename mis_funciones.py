
import warnings
warnings.filterwarnings("ignore", category = FutureWarning)

import gspread
from google.oauth2.service_account import Credentials
import numpy as np
import pandas as pd
from IPython.display import display
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
            display(df.head(3))

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