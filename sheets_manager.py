import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
from datetime import datetime
import json
import os
import re
import tempfile

# Configuración
SHEET_ID = '16azlcSMh1_zpxNQNbqyNuMBxzCFmYGSF2rWZPf2WR6I'
SERVICE_ACCOUNT_FILE = 'service_account.json'

def get_credentials_dict():
    """
    Obtiene las credenciales desde variable de entorno o archivo local.
    Versión robusta para Render.
    """
    try:
        # 1. Intentar desde variable de entorno (Render)
        env_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if env_creds:
            try:
                # Intentar parsear como JSON directo
                creds_dict = json.loads(env_creds)
                return creds_dict
            except json.JSONDecodeError:
                # Si no es JSON, podría ser una ruta a un archivo
                if os.path.exists(env_creds):
                    with open(env_creds, 'r') as f:
                        return json.load(f)
                else:
                    # Si es un string que parece JSON pero tiene problemas, limpiarlo
                    cleaned = env_creds.strip()
                    if cleaned.startswith('{') and cleaned.endswith('}'):
                        try:
                            return json.loads(cleaned)
                        except:
                            pass
        
        # 2. Intentar desde archivo local (desarrollo)
        if os.path.exists(SERVICE_ACCOUNT_FILE):
            with open(SERVICE_ACCOUNT_FILE, 'r') as f:
                return json.load(f)
        
        # 3. No se encontraron credenciales
        return None
        
    except Exception as e:
        st.error(f"❌ Error al obtener credenciales: {e}")
        return None

@st.cache_resource
def get_sheets_client():
    """Obtiene el cliente de Google Sheets."""
    try:
        creds_dict = get_credentials_dict()
        
        if creds_dict is None:
            st.error("❌ No se encontraron credenciales de Google Sheets")
            st.info("""
            📌 **Configuración necesaria:**
            
            **En Render:**
            1. Ir a tu servicio → Environment → Secrets
            2. Agregar Secret con:
               - Key: `GOOGLE_APPLICATION_CREDENTIALS`
               - Value: Copiar TODO el contenido de `service_account.json`
            
            **En desarrollo local:**
            1. Colocar `service_account.json` en la raíz del proyecto
            2. El archivo debe tener el formato JSON de Google Cloud
            """)
            return None
        
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # Crear archivo temporal con las credenciales
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(creds_dict, temp_file)
        temp_file.close()
        
        try:
            # Usar el archivo temporal para autenticar
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                temp_file.name, scope
            )
            client = gspread.authorize(creds)
            
            # Limpiar archivo temporal
            os.unlink(temp_file.name)
            
            return client
        except Exception as e:
            # Si falla la autenticación, limpiar y lanzar error
            os.unlink(temp_file.name)
            raise e
        
    except Exception as e:
        st.error(f"❌ Error al conectar con Google Sheets: {e}")
        st.error(f"Detalle del error: {str(e)}")
        return None

# El resto de las funciones (limpiar_importe, convertir_fecha_ddmmaaaa, etc.)
# se mantienen igual que antes