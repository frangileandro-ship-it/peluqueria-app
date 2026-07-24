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

@st.cache_resource
def get_sheets_client():
    """
    Obtiene el cliente de Google Sheets.
    Lee las credenciales desde variable de entorno (Render) o archivo local.
    """
    try:
        creds_json = None
        
        # 1. INTENTAR DESDE VARIABLE DE ENTORNO (RENDER)
        env_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if env_creds:
            try:
                # Intentar parsear como JSON
                creds_json = json.loads(env_creds)
                st.success("✅ Credenciales cargadas desde variable de entorno (Render)")
            except json.JSONDecodeError:
                # Si falla, podría ser una ruta a un archivo
                if os.path.exists(env_creds):
                    with open(env_creds, 'r') as f:
                        creds_json = json.load(f)
                        st.success("✅ Credenciales cargadas desde archivo (Ruta)")
        
        # 2. INTENTAR DESDE ARCHIVO LOCAL (DESARROLLO)
        if creds_json is None and os.path.exists('service_account.json'):
            with open('service_account.json', 'r') as f:
                creds_json = json.load(f)
                st.success("✅ Credenciales cargadas desde archivo local")
        
        # 3. SI NO HAY CREDENCIALES, MOSTRAR ERROR
        if creds_json is None:
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
            """)
            return None
        
        # 4. CREAR CREDENCIALES USANDO UN ARCHIVO TEMPORAL
        # Esto es necesario porque ServiceAccountCredentials espera un archivo
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(creds_json, temp_file)
        temp_file.close()
        
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(temp_file.name, scope)
        
        # Limpiar archivo temporal
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