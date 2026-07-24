import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sheets_manager import add_turn, clear_cache
from streamlit_calendar import calendar
import calendar as cal

def show(datos):
    # --- TÍTULO ÚNICO ---
    st.title("📅 Agenda de Turnos")
    
    turnos = datos['turnos']
    clientes = datos['clientes']
    
    # --- INICIALIZAR SESSION STATE ---
    if 'fecha_seleccionada_turno' not in st.session_state:
        st.session_state.fecha_seleccionada_turno = datetime.now().date()
    
    if 'mostrar_formulario_turno' not in st.session_state:
        st.session_state.mostrar_formulario_turno = False
    
    # --- CONVERTIR TURNOS A FORMATO PARA CALENDARIO ---
    eventos = []
    
    if not turnos.empty and 'Fecha y Hora' in turnos.columns:
        turnos['Fecha y Hora'] = pd.to_datetime(turnos['Fecha y Hora'], errors='coerce')
        turnos = turnos.dropna(subset=['Fecha y Hora'])
        
        for _, row in turnos.iterrows():
            fecha_hora = row['Fecha y Hora']
            cliente_nombre = row.get('Cliente', 'Sin cliente')
            
            eventos.append({
                "title": cliente_nombre,
                "start": fecha_hora.strftime("%Y-%m-%dT%H:%M:%S"),
                "end": (fecha_hora + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S"),
                "color": "#4CAF50"
            })
    
    # --- CALENDARIO VISUAL ---
    # (sin subtítulo, solo el calendario)
    
    calendar_options = {
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek"
        },
        "initialView": "dayGridMonth",
        "locale": "es",
        "buttonText": {
            "today": "Hoy",
            "month": "Mes",
            "week": "Semana"
        },
        "firstDay": 1,
        "height": "auto",
        "selectable": True,
        "selectMirror": True
    }
    
    # Mostrar calendario (solo visual)
    calendar(
        events=eventos,
        options=calendar_options,
        key="calendario_turnos",
        custom_css="""
        .fc-event-title {
            font-size: 11px;
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .fc-daygrid-day {
            cursor: pointer;
        }
        """
    )
    
    # --- SELECTOR DE FECHA MANUAL ---
    st.markdown("---")
    st.subheader("📌 Seleccionar día para gestionar turnos")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        # Selector de fecha manual
        fecha_manual = st.date_input(
            "Seleccionar fecha",
            st.session_state.fecha_seleccionada_turno,
            key="selector_fecha_turno"
        )
        
        # Actualizar fecha seleccionada
        st.session_state.fecha_seleccionada_turno = fecha_manual
        
        # Botón para mostrar formulario
        if st.button("➕ Agregar turno este día", use_container_width=True, type="primary"):
            st.session_state.mostrar_formulario_turno = True
            st.rerun()
    
    # --- FORMULARIO PARA AGREGAR TURNO ---
    if st.session_state.mostrar_formulario_turno:
        fecha_turno = st.session_state.fecha_seleccionada_turno
        
        st.markdown("---")
        st.subheader(f"📌 Agregar turno para el {fecha_turno.strftime('%d/%m/%Y')}")
        
        with st.form("form_nuevo_turno", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                # Fecha (precargada)
                fecha = st.date_input("📅 Fecha", fecha_turno)
                
                # Cliente
                if not clientes.empty:
                    clientes_lista = clientes['Cliente-Proveedor'].tolist()
                    if 'Ingreso/Gasto' in clientes.columns:
                        clientes_filtrados = clientes[
                            clientes['Ingreso/Gasto'].str.upper() == 'INGRESO'
                        ]['Cliente-Proveedor'].tolist()
                    else:
                        clientes_filtrados = clientes_lista
                    
                    clientes_opciones = [""] + clientes_filtrados
                    cliente = st.selectbox("👤 Cliente", clientes_opciones, index=0)
                else:
                    cliente = st.selectbox("👤 Cliente", [""], index=0)
            
            with col2:
                # Hora
                hora = st.time_input("🕐 Hora", datetime.now().replace(hour=10, minute=0))
                
                # Duración (opcional)
                duracion = st.selectbox(
                    "⏱️ Duración",
                    ["30 min", "45 min", "1 hora", "1.5 horas", "2 horas", "2.5 horas", "3 horas"],
                    index=2
                )
            
            # Botón guardar
            if st.form_submit_button("💾 Guardar turno", use_container_width=True):
                if not cliente:
                    st.error("⚠️ Seleccioná un cliente")
                else:
                    fecha_hora = datetime.combine(fecha, hora)
                    
                    data = {
                        'fecha_hora': fecha_hora,
                        'cliente': cliente,
                        'duracion': duracion
                    }
                    
                    if add_turn(data):
                        st.success("✅ Turno guardado correctamente")
                        st.balloons()
                        clear_cache()
                        st.session_state.mostrar_formulario_turno = False
                        st.rerun()
        
        # Botón para cerrar formulario
        if st.button("❌ Cancelar", use_container_width=True):
            st.session_state.mostrar_formulario_turno = False
            st.rerun()
    
    # --- LISTA DE TURNOS DEL DÍA SELECCIONADO ---
    fecha_mostrar = st.session_state.fecha_seleccionada_turno
    
    if not turnos.empty and 'Fecha y Hora' in turnos.columns:
        turnos_dia = turnos[
            turnos['Fecha y Hora'].dt.date == fecha_mostrar
        ]
        
        if not turnos_dia.empty:
            st.markdown("---")
            st.subheader(f"📋 Turnos del {fecha_mostrar.strftime('%d/%m/%Y')}")
            
            turnos_dia = turnos_dia.sort_values('Fecha y Hora')
            
            for _, turno in turnos_dia.iterrows():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.write(f"🕐 {turno['Fecha y Hora'].strftime('%H:%M')}")
                with col2:
                    st.write(f"👤 {turno['Cliente']}")
                st.divider()
        else:
            st.info(f"ℹ️ No hay turnos para el {fecha_mostrar.strftime('%d/%m/%Y')}")