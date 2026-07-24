import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import calendar

def show(datos):
    st.title("📊 Panel de control")
    
    movimientos = datos['movimientos']
    
    # --- VERIFICAR DATOS ---
    if movimientos.empty or 'Importe' not in movimientos.columns:
        st.warning("⚠️ No hay datos de movimientos")
        return
    
    # --- CORRECCIÓN DE FECHAS: Convertir y limpiar ---
    movimientos['Fecha'] = pd.to_datetime(movimientos['Fecha'], errors='coerce')
    # Eliminar filas con fecha nula
    movimientos = movimientos.dropna(subset=['Fecha'])
    
    if movimientos.empty:
        st.warning("⚠️ No hay fechas válidas en los datos")
        return
    
    # --- FILTRO DE PERÍODO (SOLAPAS) ---
    st.subheader("📅 Período de análisis")
    col_periodo1, col_periodo2 = st.columns([1, 3])
    
    with col_periodo1:
        periodo = st.radio(
            "Ver:",
            ["📆 Mensual", "📅 Anual"],
            index=0,
            horizontal=True
        )
    
    with col_periodo2:
        # Obtener fechas únicas para filtros (SOLO FECHAS VÁLIDAS)
        fechas_validas = movimientos['Fecha'].dropna()
        
        if fechas_validas.empty:
            st.warning("⚠️ No hay fechas válidas en los datos")
            datos_filtrados = movimientos
        else:
            if periodo == "📆 Mensual":
                # Obtener meses REALES con datos
                meses_con_datos = fechas_validas.dt.strftime('%Y-%m').unique().tolist()
                meses_con_datos = sorted(meses_con_datos)
                
                if meses_con_datos:
                    mes_actual = datetime.now().strftime('%Y-%m')
                    
                    if mes_actual not in meses_con_datos:
                        mes_actual = meses_con_datos[-1]
                    
                    mes_seleccionado = st.selectbox(
                        "Seleccionar mes:",
                        meses_con_datos,
                        index=meses_con_datos.index(mes_actual) if mes_actual in meses_con_datos else 0
                    )
                    
                    año_mes = mes_seleccionado.split('-')
                    año = int(año_mes[0])
                    mes = int(año_mes[1])
                    
                    datos_filtrados = movimientos[
                        (movimientos['Fecha'].dt.year == año) &
                        (movimientos['Fecha'].dt.month == mes)
                    ]
                    
                    nombre_mes = calendar.month_name[mes]
                    st.caption(f"📌 Mostrando datos de {nombre_mes} {año}")
                else:
                    st.warning("No hay datos de fechas disponibles")
                    datos_filtrados = movimientos
            else:  # Anual
                años_con_datos = sorted(fechas_validas.dt.year.unique().tolist())
                
                if años_con_datos:
                    año_actual = datetime.now().year
                    
                    if año_actual not in años_con_datos:
                        año_actual = años_con_datos[-1]
                    
                    año_seleccionado = st.selectbox(
                        "Seleccionar año:",
                        años_con_datos,
                        index=años_con_datos.index(año_actual) if año_actual in años_con_datos else 0
                    )
                    
                    datos_filtrados = movimientos[
                        movimientos['Fecha'].dt.year == año_seleccionado
                    ]
                    st.caption(f"📌 Mostrando datos de {año_seleccionado}")
                else:
                    st.warning("No hay datos de años disponibles")
                    datos_filtrados = movimientos
    
    st.markdown("---")
    
    # --- MÉTRICAS PRINCIPALES (SIN MOVIMIENTOS) ---
    ingresos = datos_filtrados[datos_filtrados['Ingreso/Gasto'] == 'Ingreso']['Importe'].sum()
    gastos = datos_filtrados[datos_filtrados['Ingreso/Gasto'] == 'Gasto']['Importe'].sum()
    ganancia = ingresos - gastos
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="💰 Ingresos",
            value=f"${ingresos:,.2f}"
        )
    
    with col2:
        st.metric(
            label="💸 Gastos", 
            value=f"${gastos:,.2f}"
        )
    
    with col3:
        st.metric(
            label="📈 Ganancia",
            value=f"${ganancia:,.2f}",
            delta_color="normal" if ganancia >= 0 else "inverse"
        )
    
    st.markdown("---")
    
    # --- MÉTRICAS POR MEDIO DE PAGO (VERSIÓN 2 COLUMNAS) ---
    st.subheader("💳 Resumen por Medio de Pago")
    
    # Verificar que exista la columna
    if 'Medio de Pago' not in datos_filtrados.columns:
        st.info("No se encuentra la columna 'Medio de Pago'")
    else:
        # --- OBTENER DATOS POR MEDIO DE PAGO ---
        # Ingresos por medio
        ingresos_efectivo = datos_filtrados[
            (datos_filtrados['Ingreso/Gasto'] == 'Ingreso') &
            (datos_filtrados['Medio de Pago'].str.upper().str.contains('EFECTIVO', na=False))
        ]['Importe'].sum()
        
        ingresos_mp = datos_filtrados[
            (datos_filtrados['Ingreso/Gasto'] == 'Ingreso') &
            (datos_filtrados['Medio de Pago'].str.upper().str.contains('MERCADO|MP|MERCADOPAGO', na=False))
        ]['Importe'].sum()
        
        # Egresos por medio
        egresos_efectivo = datos_filtrados[
            (datos_filtrados['Ingreso/Gasto'] == 'Gasto') &
            (datos_filtrados['Medio de Pago'].str.upper().str.contains('EFECTIVO', na=False))
        ]['Importe'].sum()
        
        egresos_mp = datos_filtrados[
            (datos_filtrados['Ingreso/Gasto'] == 'Gasto') &
            (datos_filtrados['Medio de Pago'].str.upper().str.contains('MERCADO|MP|MERCADOPAGO', na=False))
        ]['Importe'].sum()
        
        # --- SALDOS INICIALES DESDE HOJA "CAJA" (SOLO PARA ANUAL) ---
        saldo_inicial_efectivo = 0.0
        saldo_inicial_mp = 0.0
        mostrar_saldo_inicial = False
        
        # Solo si el período es Anual, buscar saldo inicial
        if periodo == "📅 Anual":
            caja = datos.get('caja', pd.DataFrame())
            
            if not caja.empty:
                # Asegurar que la columna Fecha sea datetime
                if 'Fecha' in caja.columns:
                    caja['Fecha'] = pd.to_datetime(caja['Fecha'], errors='coerce')
                
                # Buscar registros de tipo "Saldo Inicial"
                caja_saldos = caja[caja['Tipo'] == 'Saldo Inicial']
                
                if not caja_saldos.empty:
                    # Ordenar por fecha (más reciente primero) y tomar el primero
                    caja_saldos = caja_saldos.sort_values('Fecha', ascending=False)
                    ultimo_saldo = caja_saldos.iloc[0]
                    
                    # Extraer valores (con manejo de errores)
                    try:
                        saldo_inicial_efectivo = float(ultimo_saldo.get('Efectivo', 0.0) or 0.0)
                    except:
                        saldo_inicial_efectivo = 0.0
                        
                    try:
                        saldo_inicial_mp = float(ultimo_saldo.get('MercadoPago', 0.0) or 0.0)
                    except:
                        saldo_inicial_mp = 0.0
                    
                    mostrar_saldo_inicial = True
                    
                    # Mostrar qué saldo se está usando
                    fecha_saldo = ultimo_saldo.get('Fecha', '')
                    if isinstance(fecha_saldo, pd.Timestamp):
                        fecha_saldo = fecha_saldo.strftime('%d/%m/%Y')
                    st.caption(f"📌 Saldo inicial cargado desde Caja: {fecha_saldo}")
                else:
                    st.info("💡 Cargá un 'Saldo Inicial' en la sección Caja para ver el acumulado anual.")
            else:
                st.info("💡 No hay datos en la hoja 'Caja'. Cargá un 'Saldo Inicial' para ver el acumulado anual.")
        
        # --- CALCULAR TOTALES ---
        total_efectivo = ingresos_efectivo - egresos_efectivo
        total_mp = ingresos_mp - egresos_mp
        
        # --- CORRECCIÓN: Acumulado SOLO en modo Anual ---
        if periodo == "📅 Anual" and mostrar_saldo_inicial:
            acumulado_efectivo = total_efectivo + saldo_inicial_efectivo
            acumulado_mp = total_mp + saldo_inicial_mp
            etiqueta_acumulado = "📈 Acumulado Anual"
            mostrar_saldo = True
        else:
            acumulado_efectivo = total_efectivo
            acumulado_mp = total_mp
            etiqueta_acumulado = ""
            mostrar_saldo = False
        
        # --- MOSTRAR EN 2 COLUMNAS ---
        col_efectivo, col_mp = st.columns(2)
        
        with col_efectivo:
            st.markdown("""
            <div style="
                background: #e8f5e9;
                border-radius: 12px;
                padding: 15px;
                border: 1px solid #c8e6c9;
            ">
                <h4 style="text-align: center; color: #2e7d32; margin: 0 0 10px 0;">💵 Efectivo</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Métricas de Efectivo (SIN DELTAS)
            st.metric(
                label="💰 Ingresos Efectivo",
                value=f"${ingresos_efectivo:,.2f}"
            )
            st.metric(
                label="💸 Egresos Efectivo",
                value=f"${egresos_efectivo:,.2f}"
            )
            st.metric(
                label="📊 Total Efectivo",
                value=f"${total_efectivo:,.2f}",
                delta=None
            )
            
            # Mostrar saldo inicial y acumulado SOLO en modo Anual
            if mostrar_saldo:
                if saldo_inicial_efectivo > 0:
                    st.caption(f"📌 Saldo inicial: ${saldo_inicial_efectivo:,.2f}")
                
                st.metric(
                    label=etiqueta_acumulado,
                    value=f"${acumulado_efectivo:,.2f}",
                    delta=None
                )
        
        with col_mp:
            st.markdown("""
            <div style="
                background: #e3f2fd;
                border-radius: 12px;
                padding: 15px;
                border: 1px solid #bbdefb;
            ">
                <h4 style="text-align: center; color: #1565c0; margin: 0 0 10px 0;">📱 Mercado Pago</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Métricas de Mercado Pago (SIN DELTAS)
            st.metric(
                label="💰 Ingresos MP",
                value=f"${ingresos_mp:,.2f}"
            )
            st.metric(
                label="💸 Egresos MP",
                value=f"${egresos_mp:,.2f}"
            )
            st.metric(
                label="📊 Total MP",
                value=f"${total_mp:,.2f}",
                delta=None
            )
            
            # Mostrar saldo inicial y acumulado SOLO en modo Anual
            if mostrar_saldo:
                if saldo_inicial_mp > 0:
                    st.caption(f"📌 Saldo inicial: ${saldo_inicial_mp:,.2f}")
                
                st.metric(
                    label=etiqueta_acumulado,
                    value=f"${acumulado_mp:,.2f}",
                    delta=None
                )
    
    st.markdown("---")
    
    # --- TOP 5 CLIENTES ---
    st.subheader("🏆 Top 5 Clientes")
    
    if 'Cliente/Proveedor' in datos_filtrados.columns:
        clientes_ingresos = datos_filtrados[
            (datos_filtrados['Ingreso/Gasto'] == 'Ingreso') &
            (datos_filtrados['Cliente/Proveedor'].notna()) &
            (datos_filtrados['Cliente/Proveedor'] != '') &
            (datos_filtrados['Cliente/Proveedor'].str.strip() != '')
        ]
        
        if not clientes_ingresos.empty:
            top_clientes = clientes_ingresos.groupby('Cliente/Proveedor').agg({
                'Importe': ['sum', 'count']
            }).reset_index()
            
            top_clientes.columns = ['Cliente', 'Total', 'Cantidad']
            top_clientes = top_clientes.sort_values('Total', ascending=False).head(5)
            
            cols = st.columns(5)
            
            for idx, (_, row) in enumerate(top_clientes.iterrows()):
                with cols[idx]:
                    st.markdown(f"""
                    <div style="
                        background: #f8f9fa;
                        border-radius: 10px;
                        padding: 10px;
                        text-align: center;
                        border: 1px solid #e9ecef;
                        margin: 5px;
                    ">
                        <div style="font-weight: 600; font-size: 14px; color: #1a1a1a; margin-bottom: 5px;">
                            {row['Cliente']}
                        </div>
                        <div style="font-size: 16px; font-weight: 700; color: #2e7d32;">
                            ${row['Total']:,.0f}
                        </div>
                        <div style="font-size: 12px; color: #6c757d;">
                            🛒 {row['Cantidad']} veces
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            total_clientes = len(clientes_ingresos['Cliente/Proveedor'].unique())
            st.caption(f"📊 Total de clientes únicos: {total_clientes}")
        else:
            st.info("No hay clientes con ingresos registrados")
    else:
        st.info("No se encuentra la columna 'Cliente/Proveedor'")
    
    st.markdown("---")
    
    # --- TOP CATEGORÍAS CON SEPARADOR VERTICAL ---
    st.subheader("📂 Top Categorías")
    
    # Usar columnas con separador visual
    col_ingresos, col_separador, col_gastos = st.columns([2.5, 0.3, 2.5])
    
    with col_ingresos:
        st.markdown("### 💰 Ingresos")
        cat_ingresos = datos_filtrados[
            datos_filtrados['Ingreso/Gasto'] == 'Ingreso'
        ].groupby('Categoría')['Importe'].sum().reset_index()
        
        if not cat_ingresos.empty and cat_ingresos['Importe'].sum() > 0:
            cat_ingresos = cat_ingresos.sort_values('Importe', ascending=False)
            
            for _, row in cat_ingresos.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{row['Categoría']}**")
                with col2:
                    st.write(f"${row['Importe']:,.0f}")
                st.divider()
        else:
            st.info("No hay ingresos por categoría")
    
    with col_separador:
        # Línea vertical separadora
        st.markdown("""
        <div style="
            border-left: 2px solid #dee2e6;
            height: 100%;
            min-height: 300px;
            margin: 0 auto;
        "></div>
        """, unsafe_allow_html=True)
    
    with col_gastos:
        st.markdown("### 💸 Gastos")
        cat_gastos = datos_filtrados[
            datos_filtrados['Ingreso/Gasto'] == 'Gasto'
        ].groupby('Categoría')['Importe'].sum().reset_index()
        
        if not cat_gastos.empty and cat_gastos['Importe'].sum() > 0:
            cat_gastos = cat_gastos.sort_values('Importe', ascending=False)
            
            for _, row in cat_gastos.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{row['Categoría']}**")
                with col2:
                    st.write(f"${row['Importe']:,.0f}")
                st.divider()
        else:
            st.info("No hay gastos por categoría")