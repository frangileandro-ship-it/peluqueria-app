import streamlit as st
from sheets_manager import load_all_data
import os

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Peluquería AC",
    page_icon="✂️",
    layout="wide"
)

# --- CSS CON PALETA CORPORATIVA ---
st.markdown(f"""
<style>
    /* ===== PALETA DE COLORES ===== */
    :root {{
        --primary:   #6B1A3B;
        --secondary: #AA5572;
        --accent:    #D09AA9;
        --background:#FDFBFC;
    }}

    /* ===== SIDEBAR ===== */
    section[data-testid="stSidebar"] {{
        background-color: {st.session_state.get('sidebar_bg', '#FFFFFF')} !important;
        box-shadow: 2px 0 12px rgba(107, 26, 59, 0.08) !important;
    }}
    section[data-testid="stSidebar"] .stButton button {{
        background-color: transparent !important;
        border: 1px solid #e8e0e3 !important;
        color: #4a3a40 !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        padding: 10px 16px !important;
        text-align: left !important;
    }}
    section[data-testid="stSidebar"] .stButton button:hover {{
        background-color: #f5edf0 !important;
        border-color: #d09aa9 !important;
        color: #6B1A3B !important;
    }}
    section[data-testid="stSidebar"] .stButton button[data-testid="baseButton-primary"] {{
        background-color: #f5edf0 !important;
        border-color: #AA5572 !important;
        color: #6B1A3B !important;
        font-weight: 600 !important;
        border-left: 4px solid #6B1A3B !important;
    }}
    .sidebar-title {{
        color: #6B1A3B !important;
        font-weight: 700 !important;
        font-size: 1.4rem !important;
        text-align: center !important;
        margin: 5px 0 !important;
    }}
    section[data-testid="stSidebar"] hr {{
        border-color: #e8e0e3 !important;
        opacity: 0.5 !important;
    }}

    /* ===== FONDO DE PÁGINAS ===== */
    .stApp {{
        background: var(--background) !important;
    }}
    .main > div {{
        background-color: rgba(255, 255, 255, 0.92) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 2px 16px rgba(107, 26, 59, 0.06) !important;
        margin: 10px !important;
        border: 1px solid #f0e8eb !important;
    }}

    /* ===== TÍTULOS ===== */
    h1, h2, h3 {{
        color: #2c1a22 !important;
        font-weight: 600 !important;
    }}
    h1 {{
        color: #6B1A3B !important;
        border-bottom: 3px solid #D09AA9 !important;
        padding-bottom: 10px !important;
    }}
    h2, h3 {{
        color: #4a2a38 !important;
    }}

    /* ===== MÉTRICAS ===== */
    [data-testid="metric-container"] {{
        background-color: #ffffff !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        box-shadow: 0 2px 8px rgba(107, 26, 59, 0.05) !important;
        border: 1px solid #f0e8eb !important;
    }}
    [data-testid="metric-container"] label {{
        color: #6a5a60 !important;
        font-weight: 500 !important;
    }}
    [data-testid="metric-container"] .stMetricValue {{
        color: #6B1A3B !important;
        font-weight: 700 !important;
    }}
    [data-testid="metric-container"] .stMetricDelta {{
        color: #AA5572 !important;
    }}

    /* ===== BOTONES ===== */
    .stButton button {{
        background-color: #6B1A3B !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        padding: 0.5rem 1.2rem !important;
        transition: all 0.2s ease !important;
    }}
    .stButton button:hover {{
        background-color: #8a2a50 !important;
        box-shadow: 0 4px 12px rgba(107, 26, 59, 0.2) !important;
    }}
    .stButton button:active {{
        transform: scale(0.97) !important;
    }}

    /* ===== SELECTORES E INPUTS ===== */
    .stSelectbox, .stDateInput, .stTextInput, .stTextArea {{
        background-color: #ffffff !important;
        border-radius: 8px !important;
        border: 1px solid #e8e0e3 !important;
    }}
    .stSelectbox:focus, .stDateInput:focus {{
        border-color: #AA5572 !important;
        box-shadow: 0 0 0 2px rgba(170, 85, 114, 0.15) !important;
    }}

    /* ===== DIVIDERS ===== */
    hr {{
        border-color: #e8e0e3 !important;
        opacity: 0.5 !important;
    }}

    /* ===== TARJETAS CLIENTES (TOP 5) ===== */
    div[style*="background: #f8f9fa;"] {{
        background-color: #faf5f7 !important;
        border: 1px solid #e8e0e3 !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 6px rgba(107, 26, 59, 0.04) !important;
        transition: all 0.2s ease !important;
    }}
    div[style*="background: #f8f9fa;"]:hover {{
        border-color: #D09AA9 !important;
        box-shadow: 0 4px 12px rgba(107, 26, 59, 0.08) !important;
    }}

    /* ===== TABS (CONFIGURACIÓN) ===== */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: #ffffff !important;
        border-radius: 12px !important;
        padding: 4px !important;
        border: 1px solid #f0e8eb !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px !important;
        padding: 8px 16px !important;
        color: #6a5a60 !important;
        font-weight: 500 !important;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: #6B1A3B !important;
        color: white !important;
    }}
    .stTabs [aria-selected="true"]:hover {{
        background-color: #8a2a50 !important;
    }}

    /* ===== EXPANDER ===== */
    .stExpander {{
        border: 1px solid #f0e8eb !important;
        border-radius: 12px !important;
        background-color: #ffffff !important;
    }}
    .stExpander summary {{
        color: #6B1A3B !important;
        font-weight: 600 !important;
    }}

    /* ===== DATAFRAME ===== */
    .stDataFrame {{
        border-radius: 12px !important;
        border: 1px solid #f0e8eb !important;
    }}
    .stDataFrame thead th {{
        background-color: #faf5f7 !important;
        color: #4a2a38 !important;
        font-weight: 600 !important;
    }}

    /* ===== SIDEBAR LOGO ===== */
    .sidebar-logo {{
        display: block !important;
        margin: 0 auto !important;
        max-width: 120px !important;
        padding: 8px !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL ---
with st.sidebar:
    # LOGO PEQUEÑO Y CENTRADO
    if os.path.exists("logo.png"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("logo.png", width=110)
    else:
        st.warning("⚠️ Logo no encontrado")
    
    # TÍTULO CENTRADO
    st.markdown('<p class="sidebar-title">✂️ Peluquería AC</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # NAVEGACIÓN
    if "pagina" not in st.session_state:
        st.session_state.pagina = "Panel de control"
    
    opciones = [
        "📊 Panel de control",
        "💸 Movimientos",
        "📅 Turnos",
        "💰 Caja",
        "⚙️ Configuración"
    ]
    
    for opcion in opciones:
        if st.button(
            opcion,
            key=opcion,
            use_container_width=True,
            type="primary" if st.session_state.pagina == opcion else "secondary"
        ):
            st.session_state.pagina = opcion
            st.rerun()
    
    st.markdown("---")

# --- CARGA DE DATOS ---
with st.spinner("Cargando datos..."):
    datos = load_all_data()

# --- VERIFICAR DATOS ---
if datos['movimientos'].empty and datos['caja'].empty:
    st.warning("⚠️ No se pudieron cargar los datos. Verificá la conexión con Google Sheets.")
    with st.expander("🔍 Diagnóstico"):
        st.write("**ID del Sheet:**", "16azlcSMh1_zpxNQNbqyNuMBxzCFmYGSF2rWZPf2WR6I")
        st.write("**Archivo service_account.json existe:**", os.path.exists('service_account.json'))
        try:
            import json
            with open('service_account.json', 'r') as f:
                creds_data = json.load(f)
                st.write("**Email de la cuenta de servicio:**", creds_data.get('client_email', 'No encontrado'))
                st.info(f"📧 Compartí el sheet con: {creds_data.get('client_email', '')}")
        except:
            st.error("No se pudo leer el archivo service_account.json")
else:
    st.session_state['datos'] = datos
    pagina = st.session_state.pagina
    
    if pagina == "📊 Panel de control":
        import paginas.dashboard as dashboard
        dashboard.show(datos)
    elif pagina == "💸 Movimientos":
        import paginas.movimientos as movimientos
        movimientos.show(datos)
    elif pagina == "📅 Turnos":
        import paginas.turnos as turnos
        turnos.show(datos)
    elif pagina == "💰 Caja":
        import paginas.caja as caja
        caja.show(datos)
    elif pagina == "⚙️ Configuración":
        import paginas.configuracion as configuracion
        configuracion.show()