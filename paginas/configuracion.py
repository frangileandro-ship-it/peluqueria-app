import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from sheets_manager import get_sheets_client, clear_cache, SHEET_ID

def show():
    st.title("⚙️ Configuración - Maestro de Datos")
    
    # --- INICIALIZAR SESIÓN ---
    if 'datos_config' not in st.session_state:
        st.session_state.datos_config = {}
    
    # --- OBTENER DATOS ACTUALIZADOS ---
    client = get_sheets_client()
    if client is None:
        st.error("❌ No se pudo conectar con Google Sheets")
        return
    
    # Cargar todas las hojas
    try:
        sheet = client.open_by_key(SHEET_ID)
        
        # Hojas existentes
        hojas_disponibles = [ws.title for ws in sheet.worksheets()]
        
        # Cargar datos de cada hoja
        if 'Movimientos' in hojas_disponibles:
            ws_mov = sheet.worksheet('Movimientos')
            df_mov = pd.DataFrame(ws_mov.get_all_records())
        else:
            df_mov = pd.DataFrame()
            st.warning("⚠️ No se encuentra la hoja 'Movimientos'")
        
        if 'Cliente - Proveedor' in hojas_disponibles:
            ws_cli = sheet.worksheet('Cliente - Proveedor')
            df_cli = pd.DataFrame(ws_cli.get_all_records())
        else:
            df_cli = pd.DataFrame()
            st.warning("⚠️ No se encuentra la hoja 'Cliente - Proveedor'")
        
        if 'Categorias' in hojas_disponibles:
            ws_cat = sheet.worksheet('Categorias')
            df_cat = pd.DataFrame(ws_cat.get_all_records())
        else:
            df_cat = pd.DataFrame()
            st.warning("⚠️ No se encuentra la hoja 'Categorias'")
        
        # --- NUEVA HOJA: MEDIOS DE PAGO ---
        if 'Medios de Pago' in hojas_disponibles:
            ws_medios = sheet.worksheet('Medios de Pago')
            df_medios = pd.DataFrame(ws_medios.get_all_records())
        else:
            # Si no existe, la creamos
            st.warning("⚠️ No se encuentra la hoja 'Medios de Pago'. Creándola...")
            try:
                ws_medios = sheet.add_worksheet(title="Medios de Pago", rows="100", cols="1")
                ws_medios.update('A1', [['Medios de Pago']])
                ws_medios.append_row(['Efectivo'])
                ws_medios.append_row(['Mercado Pago'])
                df_medios = pd.DataFrame({'Medios de Pago': ['Efectivo', 'Mercado Pago']})
                st.success("✅ Hoja 'Medios de Pago' creada correctamente")
            except Exception as e:
                st.error(f"❌ Error al crear la hoja 'Medios de Pago': {e}")
                df_medios = pd.DataFrame()
        
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {e}")
        return
    
    # --- SOLAPAS ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👤 Clientes", 
        "🏢 Proveedores", 
        "📂 Categorías", 
        "💳 Medios de Pago", 
        "🧹 Limpieza Masiva"
    ])
    
    # --- SOLAPA 1: CLIENTES ---
    with tab1:
        st.subheader("👤 Gestión de Clientes")
        st.caption("Clientes = Ingreso/Gasto = INGRESO")
        
        # Filtrar solo clientes
        if not df_cli.empty and 'Ingreso/Gasto' in df_cli.columns and 'Cliente-Proveedor' in df_cli.columns:
            df_clientes = df_cli[df_cli['Ingreso/Gasto'].str.upper() == 'INGRESO'].copy()
        else:
            df_clientes = pd.DataFrame()
        
        # Mostrar lista actual
        if not df_clientes.empty:
            st.dataframe(
                df_clientes[['Cliente-Proveedor']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Cliente-Proveedor": "Cliente"
                }
            )
            st.caption(f"📊 Total: {len(df_clientes)} clientes")
        else:
            st.info("No hay clientes cargados")
        
        st.markdown("---")
        
        # Formulario para agregar
        with st.form("agregar_cliente", clear_on_submit=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                nuevo_cliente = st.text_input("Nombre del nuevo cliente")
            with col2:
                agregar = st.form_submit_button("➕ Agregar", use_container_width=True)
            
            if agregar and nuevo_cliente:
                try:
                    # Buscar si ya existe
                    existe = False
                    if not df_cli.empty and 'Cliente-Proveedor' in df_cli.columns:
                        existe = nuevo_cliente in df_cli['Cliente-Proveedor'].tolist()
                    
                    if existe:
                        st.error("⚠️ El cliente ya existe")
                    else:
                        # Agregar a Google Sheets
                        ws_cli.append_row(["INGRESO", nuevo_cliente])
                        st.success(f"✅ Cliente '{nuevo_cliente}' agregado correctamente")
                        clear_cache()
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al agregar: {e}")
    
    # --- SOLAPA 2: PROVEEDORES ---
    with tab2:
        st.subheader("🏢 Gestión de Proveedores")
        st.caption("Proveedores = Ingreso/Gasto = GASTO")
        
        # Filtrar solo proveedores
        if not df_cli.empty and 'Ingreso/Gasto' in df_cli.columns and 'Cliente-Proveedor' in df_cli.columns:
            df_proveedores = df_cli[df_cli['Ingreso/Gasto'].str.upper() == 'GASTO'].copy()
        else:
            df_proveedores = pd.DataFrame()
        
        # Mostrar lista actual
        if not df_proveedores.empty:
            st.dataframe(
                df_proveedores[['Cliente-Proveedor']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Cliente-Proveedor": "Proveedor"
                }
            )
            st.caption(f"📊 Total: {len(df_proveedores)} proveedores")
        else:
            st.info("No hay proveedores cargados")
        
        st.markdown("---")
        
        # Formulario para agregar
        with st.form("agregar_proveedor", clear_on_submit=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                nuevo_proveedor = st.text_input("Nombre del nuevo proveedor")
            with col2:
                agregar = st.form_submit_button("➕ Agregar", use_container_width=True)
            
            if agregar and nuevo_proveedor:
                try:
                    # Buscar si ya existe
                    existe = False
                    if not df_cli.empty and 'Cliente-Proveedor' in df_cli.columns:
                        existe = nuevo_proveedor in df_cli['Cliente-Proveedor'].tolist()
                    
                    if existe:
                        st.error("⚠️ El proveedor ya existe")
                    else:
                        # Agregar a Google Sheets
                        ws_cli.append_row(["GASTO", nuevo_proveedor])
                        st.success(f"✅ Proveedor '{nuevo_proveedor}' agregado correctamente")
                        clear_cache()
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al agregar: {e}")
    
    # --- SOLAPA 3: CATEGORÍAS ---
    with tab3:
        st.subheader("📂 Gestión de Categorías")
        
        # Mostrar lista actual
        if not df_cat.empty:
            st.dataframe(
                df_cat,
                use_container_width=True,
                hide_index=True
            )
            st.caption(f"📊 Total: {len(df_cat)} categorías")
        else:
            st.info("No hay categorías cargadas")
        
        st.markdown("---")
        
        # Formulario para agregar
        with st.form("agregar_categoria", clear_on_submit=True):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                tipo_cat = st.selectbox("Tipo", ["INGRESO", "GASTO"])
            with col2:
                nueva_categoria = st.text_input("Nombre de la nueva categoría")
            with col3:
                agregar = st.form_submit_button("➕ Agregar", use_container_width=True)
            
            if agregar and nueva_categoria:
                try:
                    # Buscar si ya existe
                    existe = False
                    if not df_cat.empty and 'Categoría' in df_cat.columns:
                        existe = nueva_categoria in df_cat['Categoría'].tolist()
                    
                    if existe:
                        st.error("⚠️ La categoría ya existe")
                    else:
                        # Agregar a Google Sheets
                        ws_cat.append_row([tipo_cat, nueva_categoria])
                        st.success(f"✅ Categoría '{nueva_categoria}' agregada correctamente")
                        clear_cache()
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al agregar: {e}")
    
    # --- SOLAPA 4: MEDIOS DE PAGO ---
    with tab4:
        st.subheader("💳 Gestión de Medios de Pago")
        
        # Mostrar lista actual
        if not df_medios.empty and 'Medios de Pago' in df_medios.columns:
            st.dataframe(
                df_medios[['Medios de Pago']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Medios de Pago": "Medio de Pago"
                }
            )
            st.caption(f"📊 Total: {len(df_medios)} medios de pago")
        else:
            st.info("No hay medios de pago cargados")
        
        st.markdown("---")
        
        # Formulario para agregar
        with st.form("agregar_medio", clear_on_submit=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                nuevo_medio = st.text_input("Nombre del nuevo medio de pago")
            with col2:
                agregar = st.form_submit_button("➕ Agregar", use_container_width=True)
            
            if agregar and nuevo_medio:
                try:
                    # Buscar si ya existe
                    existe = False
                    if not df_medios.empty and 'Medios de Pago' in df_medios.columns:
                        existe = nuevo_medio in df_medios['Medios de Pago'].tolist()
                    
                    if existe:
                        st.error("⚠️ El medio de pago ya existe")
                    else:
                        # Agregar a Google Sheets
                        ws_medios.append_row([nuevo_medio])
                        st.success(f"✅ Medio de pago '{nuevo_medio}' agregado correctamente")
                        clear_cache()
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al agregar: {e}")
    
    # --- SOLAPA 5: LIMPIEZA MASIVA ---
    with tab5:
        st.subheader("🧹 Limpieza Masiva de Movimientos")
        st.warning("⚠️ **ADVERTENCIA:** Esta acción es irreversible. Elimina movimientos de la base de datos.")
        
        if df_mov.empty:
            st.info("No hay movimientos para eliminar")
        else:
            # Mostrar resumen
            st.write(f"📊 Total de movimientos en la base: **{len(df_mov)}**")
            
            # Opciones de filtro
            st.subheader("Filtrar movimientos a eliminar")
            
            col1, col2 = st.columns(2)
            with col1:
                # Filtro por fecha
                fecha_desde = st.date_input("Eliminar desde", datetime.now() - timedelta(days=30))
                fecha_hasta = st.date_input("Eliminar hasta", datetime.now())
            
            with col2:
                # Filtro por tipo
                tipos = ["Todos"]
                if 'Ingreso/Gasto' in df_mov.columns:
                    tipos = ["Todos"] + df_mov['Ingreso/Gasto'].unique().tolist()
                tipo_eliminar = st.selectbox("Tipo de movimiento", tipos)
            
            # Contar cuántos se van a eliminar
            df_temp = df_mov.copy()
            if 'Fecha' in df_temp.columns:
                df_temp['Fecha'] = pd.to_datetime(df_temp['Fecha'], errors='coerce')
                df_temp = df_temp.dropna(subset=['Fecha'])
                df_temp = df_temp[
                    (df_temp['Fecha'] >= pd.to_datetime(fecha_desde)) &
                    (df_temp['Fecha'] <= pd.to_datetime(fecha_hasta))
                ]
            
            if tipo_eliminar != "Todos" and 'Ingreso/Gasto' in df_temp.columns:
                df_temp = df_temp[df_temp['Ingreso/Gasto'] == tipo_eliminar]
            
            cantidad_eliminar = len(df_temp)
            st.info(f"📌 Se eliminarán **{cantidad_eliminar}** movimientos con los filtros seleccionados")
            
            # Mostrar vista previa
            if cantidad_eliminar > 0:
                with st.expander("🔍 Ver movimientos a eliminar"):
                    st.dataframe(
                        df_temp.head(20),
                        use_container_width=True,
                        hide_index=True
                    )
                    if cantidad_eliminar > 20:
                        st.caption(f"... y {cantidad_eliminar - 20} movimientos más")
            
            # Botón de confirmación
            st.markdown("---")
            st.warning("⚠️ Para eliminar, escribí **CONFIRMAR** en el campo de abajo")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                confirmacion = st.text_input("Escribí CONFIRMAR para proceder", type="password")
            with col2:
                eliminar = st.button("🗑️ Eliminar movimientos", use_container_width=True, type="primary")
            
            if eliminar:
                if confirmacion == "CONFIRMAR":
                    if cantidad_eliminar == 0:
                        st.warning("No hay movimientos para eliminar con los filtros seleccionados")
                    else:
                        try:
                            # Obtener IDs de los movimientos a eliminar
                            ids_eliminar = df_temp['ID'].tolist()
                            
                            # Eliminar de Google Sheets (desde la última fila hacia arriba)
                            ws_mov = sheet.worksheet('Movimientos')
                            todas_las_filas = ws_mov.get_all_values()
                            
                            # Encontrar índices de filas a eliminar (primera fila es encabezado)
                            filas_a_eliminar = []
                            for idx, row in enumerate(todas_las_filas):
                                if idx == 0:  # Saltar encabezado
                                    continue
                                if len(row) > 0 and row[0] in ids_eliminar:
                                    filas_a_eliminar.append(idx + 1)  # +1 porque gspread es 1-indexed
                            
                            # Eliminar filas (de atrás hacia adelante para no afectar índices)
                            for fila in sorted(filas_a_eliminar, reverse=True):
                                ws_mov.delete_rows(fila)
                            
                            st.success(f"✅ Se eliminaron {len(filas_a_eliminar)} movimientos correctamente")
                            clear_cache()
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error al eliminar movimientos: {e}")
                else:
                    st.error("❌ Confirmación incorrecta. Escribí 'CONFIRMAR' para proceder.")