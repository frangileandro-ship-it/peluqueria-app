import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sheets_manager import add_caja_registro, clear_cache

def show(datos):
    st.title("💰 Gestión de Caja")
    
    # Cargar datos de caja
    caja = datos.get('caja', pd.DataFrame())
    
    # --- SALDOS ACTUALES ---
    st.subheader("📊 Resumen de Caja")
    
    # Calcular saldos actuales
    if not caja.empty:
        # Convertir fechas
        caja['Fecha'] = pd.to_datetime(caja['Fecha'], errors='coerce')
        
        # Ordenar por fecha
        caja = caja.sort_values('Fecha')
        
        # Último registro (saldo más reciente)
        ultimo_registro = caja.iloc[-1] if not caja.empty else None
        
        # Saldos actuales (del último registro)
        efectivo_actual = ultimo_registro['Efectivo'] if ultimo_registro is not None else 0.0
        mp_actual = ultimo_registro['MercadoPago'] if ultimo_registro is not None else 0.0
        total_actual = efectivo_actual + mp_actual
        
        # Mostrar métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💵 Efectivo", f"${efectivo_actual:,.2f}")
        with col2:
            st.metric("📱 Mercado Pago", f"${mp_actual:,.2f}")
        with col3:
            st.metric("💰 Total Caja", f"${total_actual:,.2f}")
        
        # Última actualización
        if ultimo_registro is not None:
            st.caption(f"Última actualización: {ultimo_registro['Fecha'].strftime('%d/%m/%Y')} - {ultimo_registro['Concepto']}")
    else:
        st.info("ℹ️ No hay registros de caja. Cargá un saldo inicial.")
    
    st.markdown("---")
    
    # --- AGREGAR REGISTRO ---
    with st.expander("➕ Agregar registro de caja", expanded=False):
        with st.form("nuevo_registro_caja"):
            col1, col2 = st.columns(2)
            
            with col1:
                fecha = st.date_input("📅 Fecha", datetime.now())
                tipo = st.selectbox("📌 Tipo", ["Saldo Inicial", "Cierre", "Ajuste", "Retiro", "Depósito"])
                concepto = st.text_input("📝 Concepto", placeholder="Ej: Cierre mensual enero 2026")
            
            with col2:
                efectivo = st.number_input("💵 Efectivo", min_value=0.0, step=1000.0, format="%.2f", help="Saldo de efectivo")
                mercado_pago = st.number_input("📱 Mercado Pago", min_value=0.0, step=1000.0, format="%.2f", help="Saldo de Mercado Pago")
                observaciones = st.text_area("📝 Observaciones", placeholder="Opcional...")
            
            if st.form_submit_button("💾 Guardar registro", use_container_width=True):
                if concepto == "":
                    st.error("⚠️ El concepto es obligatorio")
                else:
                    data = {
                        'fecha': fecha,
                        'tipo': tipo,
                        'concepto': concepto,
                        'efectivo': efectivo,
                        'mercado_pago': mercado_pago,
                        'observaciones': observaciones
                    }
                    
                    if add_caja_registro(data):
                        st.success("✅ Registro guardado correctamente")
                        clear_cache()
                        st.rerun()
    
    st.markdown("---")
    
    # --- HISTORIAL DE CAJA ---
    st.subheader("📋 Historial de Caja")
    
    if not caja.empty:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            fecha_desde = st.date_input("Desde", caja['Fecha'].min().date() if not caja.empty else datetime.now() - timedelta(days=30))
        with col2:
            fecha_hasta = st.date_input("Hasta", datetime.now().date())
        
        # Filtrar
        caja_filtrada = caja[
            (caja['Fecha'] >= pd.to_datetime(fecha_desde)) &
            (caja['Fecha'] <= pd.to_datetime(fecha_hasta))
        ]
        
        if not caja_filtrada.empty:
            # Mostrar tabla
            st.dataframe(
                caja_filtrada.sort_values('Fecha', ascending=False),
                use_container_width=True,
                column_config={
                    "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                    "Efectivo": st.column_config.NumberColumn("Efectivo", format="$%.2f"),
                    "MercadoPago": st.column_config.NumberColumn("Mercado Pago", format="$%.2f"),
                    "Tipo": st.column_config.TextColumn("Tipo"),
                    "Concepto": st.column_config.TextColumn("Concepto"),
                    "Observaciones": st.column_config.TextColumn("Observaciones")
                },
                hide_index=True
            )
            
            # Botón para exportar
            csv = caja_filtrada.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"caja_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No hay registros en el rango seleccionado")
    else:
        st.info("ℹ️ No hay registros de caja aún")