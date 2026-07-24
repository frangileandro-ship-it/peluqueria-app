import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
from datetime import datetime
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

# Configuración
SHEET_ID = '16azlcSMh1_zpxNQNbqyNuMBxzCFmYGSF2rWZPf2WR6I'
SERVICE_ACCOUNT_FILE = 'service_account.json'

def get_credentials():
    """
    Obtiene las credenciales de Google Sheets.
    Primero intenta desde archivo, luego desde variable de entorno.
    """
    try:
        # 1. Intentar desde archivo (desarrollo local)
        if os.path.exists(SERVICE_ACCOUNT_FILE):
            with open(SERVICE_ACCOUNT_FILE, 'r') as f:
                creds_dict = json.load(f)
                return creds_dict
        
        # 2. Intentar desde variable de entorno (Render)
        env_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if env_creds:
            # Si la variable es un JSON string, parsearlo
            try:
                creds_dict = json.loads(env_creds)
                return creds_dict
            except json.JSONDecodeError:
                # Si es una ruta a un archivo
                if os.path.exists(env_creds):
                    with open(env_creds, 'r') as f:
                        return json.load(f)
        
        # 3. Si no hay credenciales, mostrar error
        st.error("❌ No se encontraron credenciales de Google Sheets")
        st.info("""
        📌 **Configuración necesaria:**
        
        **En desarrollo local:**
        - Colocar `service_account.json` en la raíz del proyecto
        
        **En Render:**
        - Agregar Secret `GOOGLE_APPLICATION_CREDENTIALS` con el contenido del JSON
        """)
        return None
        
    except Exception as e:
        st.error(f"❌ Error al leer credenciales: {e}")
        return None

@st.cache_resource
def get_sheets_client():
    """Obtiene el cliente de Google Sheets"""
    try:
        creds_dict = get_credentials()
        if creds_dict is None:
            return None
        
        # Crear credenciales desde el diccionario
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # Método alternativo: crear credenciales desde el diccionario
        from oauth2client.client import GoogleCredentials
        creds = GoogleCredentials(
            access_token=None,
            client_id=creds_dict.get('client_id'),
            client_secret=creds_dict.get('client_secret'),
            refresh_token=None,
            token_expiry=None,
            token_uri=creds_dict.get('token_uri'),
            user_agent=None,
            revoke_uri=None
        )
        
        # Si el método anterior falla, usar ServiceAccountCredentials
        if creds is None or not creds.client_id:
            # Crear credenciales desde el archivo temporal si es necesario
            if os.path.exists(SERVICE_ACCOUNT_FILE):
                creds = ServiceAccountCredentials.from_json_keyfile_name(
                    SERVICE_ACCOUNT_FILE, scope
                )
            else:
                # Crear archivo temporal en Render
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                json.dump(creds_dict, temp_file)
                temp_file.close()
                creds = ServiceAccountCredentials.from_json_keyfile_name(
                    temp_file.name, scope
                )
                os.unlink(temp_file.name)
        
        client = gspread.authorize(creds)
        return client
        
    except Exception as e:
        st.error(f"❌ Error al conectar con Google Sheets: {e}")
        return None

def limpiar_importe(valor):
    """Convierte cualquier formato de importe a número flotante"""
    if pd.isna(valor) or valor == '' or valor is None:
        return 0.0
    
    if isinstance(valor, (int, float)):
        return float(valor)
    
    if isinstance(valor, str):
        valor = valor.replace('$', '').replace('US$', '').strip()
        
        if ',' in valor and '.' in valor:
            valor = valor.replace(',', '')
        elif '.' in valor and ',' in valor:
            valor = valor.replace('.', '').replace(',', '.')
        elif ',' in valor and '.' not in valor:
            valor = valor.replace(',', '.')
        
        valor = re.sub(r'[^\d.]', '', valor)
        
        try:
            return float(valor)
        except:
            return 0.0
    
    return 0.0

def convertir_fecha_ddmmaaaa(valor):
    """Convierte una fecha en formato DD/MM/AAAA a datetime."""
    if pd.isna(valor) or valor == '' or valor is None:
        return pd.NaT
    
    if isinstance(valor, (pd.Timestamp, datetime)):
        return valor
    
    if isinstance(valor, str):
        valor = valor.strip()
        
        for sep in ['-', '.']:
            if sep in valor:
                valor = valor.replace(sep, '/')
        
        try:
            partes = valor.split('/')
            if len(partes) == 3:
                dia = int(partes[0])
                mes = int(partes[1])
                año = int(partes[2])
                
                if 1 <= dia <= 31 and 1 <= mes <= 12 and 1900 <= año <= 2100:
                    return pd.Timestamp(year=año, month=mes, day=dia)
        except:
            pass
        
        try:
            return pd.to_datetime(valor, dayfirst=True, errors='coerce')
        except:
            return pd.NaT
    
    return pd.NaT

@st.cache_data(ttl=60, show_spinner=False)
def load_sheet_data(sheet_name):
    """Carga los datos de una hoja específica"""
    try:
        client = get_sheets_client()
        if client is None:
            return pd.DataFrame()
            
        sheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)
        records = sheet.get_all_records()
        
        if not records:
            return pd.DataFrame()
            
        df = pd.DataFrame(records)
        
        # Renombrar columnas
        mapeo = {
            'IDENTIFICACIÓN': 'ID',
            'Fecha': 'Fecha',
            'Ingreso/Gasto': 'Ingreso/Gasto',
            'Categoría': 'Categoría',
            'Cliente/Proveedor': 'Cliente/Proveedor',
            'Medio de Pago': 'Medio de Pago',
            'Importe': 'Importe',
            'Importar': 'Importe',
            'Observaciones': 'Observaciones'
        }
        
        for col in df.columns:
            if col in mapeo:
                df = df.rename(columns={col: mapeo[col]})
        
        # Convertir fechas
        if 'Fecha' in df.columns:
            df['Fecha'] = df['Fecha'].apply(convertir_fecha_ddmmaaaa)
            df = df.dropna(subset=['Fecha'])
        
        # Convertir importe
        if 'Importe' in df.columns:
            df['Importe'] = df['Importe'].apply(limpiar_importe)
            df['Importe'] = pd.to_numeric(df['Importe'], errors='coerce').fillna(0.0)
        
        # Normalizar Ingreso/Gasto
        if 'Ingreso/Gasto' in df.columns:
            df['Ingreso/Gasto'] = df['Ingreso/Gasto'].astype(str).str.upper().str.strip()
            df['Ingreso/Gasto'] = df['Ingreso/Gasto'].map({
                'INGRESO': 'Ingreso',
                'GASTO': 'Gasto'
            }).fillna(df['Ingreso/Gasto'])
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error en {sheet_name}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60, show_spinner=False)
def load_all_data():
    """Carga todas las hojas"""
    return {
        'movimientos': load_sheet_data('Movimientos'),
        'categorias': load_sheet_data('Categorias'),
        'clientes': load_sheet_data('Cliente - Proveedor'),
        'turnos': load_sheet_data('Turnos'),
        'caja': load_sheet_data('Caja')
    }

def add_movement(data):
    """Agrega un nuevo movimiento"""
    try:
        client = get_sheets_client()
        if client is None:
            return False
            
        sheet = client.open_by_key(SHEET_ID).worksheet('Movimientos')
        records = sheet.get_all_records()
        next_id = len(records) + 1 if records else 1
        
        row = [
            next_id,
            data['fecha'].strftime('%Y-%m-%d'),
            data['tipo'],
            data['categoria'],
            data['cliente'],
            data['medio_pago'],
            float(data['importe']),
            data['observaciones']
        ]
        
        sheet.append_row(row)
        st.cache_data.clear()
        return True
        
    except Exception as e:
        st.error(f"❌ Error al guardar: {e}")
        return False

def add_caja_registro(data):
    """Agrega un nuevo registro de caja"""
    try:
        client = get_sheets_client()
        if client is None:
            return False
            
        sheet = client.open_by_key(SHEET_ID).worksheet('Caja')
        records = sheet.get_all_records()
        next_id = len(records) + 1 if records else 1
        
        row = [
            next_id,
            data['fecha'].strftime('%Y-%m-%d'),
            data['tipo'],
            data['concepto'],
            float(data['efectivo']),
            float(data['mercado_pago']),
            data['observaciones']
        ]
        
        sheet.append_row(row)
        st.cache_data.clear()
        return True
        
    except Exception as e:
        st.error(f"❌ Error al guardar registro de caja: {e}")
        return False

def add_turn(data):
    """Agrega un nuevo turno"""
    try:
        client = get_sheets_client()
        if client is None:
            return False
            
        sheet = client.open_by_key(SHEET_ID).worksheet('Turnos')
        records = sheet.get_all_records()
        next_id = len(records) + 1 if records else 1
        
        row = [next_id, data['fecha_hora'].strftime('%Y-%m-%d %H:%M'), data['cliente']]
        sheet.append_row(row)
        st.cache_data.clear()
        return True
        
    except Exception as e:
        st.error(f"❌ Error al guardar turno: {e}")
        return False

def clear_cache():
    """Limpia el caché"""
    st.cache_data.clear()
    st.cache_resource.clear()
    st.success("✅ Caché limpiado")