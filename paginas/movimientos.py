import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sheets_manager import add_movement, clear_cache, get_sheets_client, SHEET_ID
import re
import calendar

def show(datos):
    st.title("💸 Gestión de Movimientos")
    
    movimientos = datos['movimientos']
    categorias = datos['categorias']
    clientes = datos['clientes']
    
    # --- INICIALIZAR SESSION STATE ---
    if 'editor_key' not in st.session_state:
        st.session_state.editor_key = 0
    
    # --- 1. FORMULARIO ---
    st.subheader("➕ Nuevo Movimiento")
    
    # --- CAMPOS FUERA DEL FORMULARIO PARA ACTUALIZACIÓN EN TIEMPO REAL ---
    col1, col2 = st.columns(2)
    
    with col1:
        fecha = st.date_input("📅 Fecha", datetime.now())
        
        # --- TIPO (actualiza session_state) ---
        tipo = st.selectbox(
            "📌 Tipo", 
            ["", "Ingreso", "Gasto"],
            index=0,
            key="tipo_select"
        )
        
        # --- CATEGORÍA (filtrada por tipo) ---
        if not categorias.empty and 'Ingreso/Gasto' in categorias.columns and 'Categoría' in categorias.columns:
            if tipo:
                cat_disponibles = categorias[
                    categorias['Ingreso/Gasto'].str.upper() == tipo.upper()
                ]['Categoría'].tolist()
            else:
                cat_disponibles = []
            
            cat_opciones = [""] + cat_disponibles
            categoria = st.selectbox("📂 Categoría", cat_opciones, index=0)
        else:
            categoria = st.selectbox("📂 Categoría", [""], index=0)
    
    with col2:
        # --- CLIENTE/PROVEEDOR (filtrado por tipo) ---
        if not clientes.empty and 'Cliente-Proveedor' in clientes.columns:
            if 'Ingreso/Gasto' in clientes.columns:
                if tipo == "Ingreso":
                    clientes_filtrados = clientes[
                        clientes['Ingreso/Gasto'].str.upper() == 'INGRESO'
                    ]['Cliente-Proveedor'].tolist()
                elif tipo == "Gasto":
                    clientes_filtrados = clientes[
                        clientes['Ingreso/Gasto'].str.upper() == 'GASTO'
                    ]['Cliente-Proveedor'].tolist()
                else:
                    clientes_filtrados = clientes['Cliente-Proveedor'].tolist()
            else:
                clientes_filtrados = clientes['Cliente-Proveedor'].tolist()
        else:
            clientes_filtrados = []
        
        clientes_opciones = [""] + clientes_filtrados
        cliente = st.selectbox(
            "👤 Cliente/Proveedor", 
            clientes_opciones, 
            index=0,
            help="Se filtran según el tipo seleccionado"
        )
        
        medio_pago = st.selectbox(
            "💳 Medio de Pago",
            ["", "Efectivo", "Tarjeta Débito", "Tarjeta Crédito", "Transferencia", "Mercado Pago", "Otro"],
            index=0
        )
        
        importe_str = st.text_input(
            "💰 Importe ($)",
            placeholder="Ej: 1500.00",
            value=""
        )
    
    observaciones = st.text_area("📝 Observaciones", placeholder="Opcional...")
    
    # --- BOTÓN GUARDAR ---
    if st.button("💾 Guardar movimiento", use_container_width=True, type="primary"):
        importe = 0.0
        importe_error = False
        
        if importe_str:
            importe_limpio = importe_str.strip().replace(',', '.')
            importe_limpio = re.sub(r'[^\d.]', '', importe_limpio)
            
            try:
                importe = float(importe_limpio)
                if importe <= 0:
                    importe_error = True
            except:
                importe_error = True
        else:
            importe_error = True
        
        errores = []
        
        if not tipo:
            errores.append("⚠️ Seleccioná un Tipo (Ingreso o Gasto)")
        
        if not categoria:
            errores.append("⚠️ Seleccioná una Categoría")
        
        if not cliente:
            errores.append("⚠️ Seleccioná un Cliente/Proveedor")
        
        if not medio_pago:
            errores.append("⚠️ Seleccioná un Medio de Pago")
        
        if importe_error or importe <= 0:
            errores.append("⚠️ Ingresá un Importe válido mayor a 0")
        
        if errores:
            for error in errores:
                st.error(error)
        else:
            data = {
                'fecha': fecha,
                'tipo': tipo,
                'categoria': categoria,
                'cliente': cliente,
                'medio_pago': medio_pago,
                'importe': importe,
                'observaciones': observaciones
            }
            
            if add_movement(data):
                st.success("✅ Movimiento guardado correctamente")
                st.balloons()
                clear_cache()
                # Resetear el formulario
                st.session_state.tipo_select = ""
                st.rerun()
    
    st.markdown("---")
    
    # --- 2. FILTRO POR MES ---
    st.subheader("🔍 Filtrar movimientos")
    
    if not movimientos.empty and 'Fecha' in movimientos.columns:
        movimientos['Fecha'] = pd.to_datetime(movimientos['Fecha'], errors='coerce')
        movimientos_con_fecha = movimientos.dropna(subset=['Fecha'])
        
        if not movimientos_con_fecha.empty:
            meses_disponibles = sorted(movimientos_con_fecha['Fecha'].dt.strftime('%Y-%m').unique().tolist())
            
            mes_actual = datetime.now().strftime('%Y-%m')
            if mes_actual in meses_disponibles:
                mes_default = mes_actual
            else:
                mes_default = meses_disponibles[-1] if meses_disponibles else mes_actual
            
            mes_seleccionado = st.selectbox(
                "📅 Seleccionar mes",
                meses_disponibles,
                index=meses_disponibles.index(mes_default) if mes_default in meses_disponibles else 0
            )
            
            año = int(mes_seleccionado.split('-')[0])
            mes = int(mes_seleccionado.split('-')[1])
            
            df_filtrado = movimientos_con_fecha[
                (movimientos_con_fecha['Fecha'].dt.year == año) &
                (movimientos_con_fecha['Fecha'].dt.month == mes)
            ]
            
            nombre_mes = calendar.month_name[mes]
            st.caption(f"📌 Mostrando datos de {nombre_mes} {año}")
        else:
            st.warning("⚠️ No hay fechas válidas en los datos")
            df_filtrado = movimientos
    else:
        st.warning("⚠️ No hay movimientos para filtrar")
        df_filtrado = movimientos
    
    # --- 3. TABLA ---
    if not df_filtrado.empty:
        total_filtrado = df_filtrado['Importe'].sum()
        st.info(f"📊 Mostrando {len(df_filtrado)} movimientos")
        
        df_filtrado = df_filtrado.sort_values('Fecha', ascending=False)
        
        # --- CREAR COPIA PARA EDICIÓN (SIN ID) ---
        df_editable = df_filtrado.drop(columns=['ID'], errors='ignore').copy()
        
        # Configurar columnas
        column_config = {
            "Fecha": st.column_config.DateColumn(
                "Fecha",
                format="DD/MM/YYYY",
                required=True,
                width=120
            ),
            "Ingreso/Gasto": st.column_config.SelectboxColumn(
                "Tipo",
                options=["Ingreso", "Gasto"],
                required=True,
                width=100
            ),
            "Categoría": st.column_config.TextColumn(
                "Categoría",
                required=True,
                width=150
            ),
            "Cliente/Proveedor": st.column_config.TextColumn(
                "Cliente/Proveedor",
                required=True,
                width=150
            ),
            "Medio de Pago": st.column_config.SelectboxColumn(
                "Medio de Pago",
                options=["Efectivo", "Tarjeta Débito", "Tarjeta Crédito", "Transferencia", "Mercado Pago", "Otro"],
                required=True,
                width=140
            ),
            "Importe": st.column_config.NumberColumn(
                "Importe",
                format="$%.2f",
                min_value=0,
                required=True,
                width=120
            ),
            "Observaciones": st.column_config.TextColumn(
                "Observaciones",
                width=400
            )
        }
        
        # Mostrar editor de datos
        edited_df = st.data_editor(
            df_editable,
            use_container_width=True,
            column_config=column_config,
            hide_index=True,
            num_rows="dynamic",
            key=f"editor_movimientos_{st.session_state.editor_key}"
        )
        
        # --- BOTÓN PARA ELIMINAR ---
        if st.button("🗑️ Eliminar fila seleccionada", use_container_width=False):
            if 'selected_rows' in st.session_state:
                indices_seleccionados = st.session_state.selected_rows
                if indices_seleccionados:
                    idx = indices_seleccionados[0]
                    if idx < len(df_filtrado):
                        id_eliminar = df_filtrado.iloc[idx]['ID']
                        
                        try:
                            client = get_sheets_client()
                            if client is None:
                                st.error("❌ No se pudo conectar con Google Sheets")
                            else:
                                sheet = client.open_by_key(SHEET_ID).worksheet('Movimientos')
                                todas_las_filas = sheet.get_all_values()
                                
                                fila_idx = None
                                for i, fila in enumerate(todas_las_filas):
                                    if i > 0 and len(fila) > 0 and fila[0] == str(id_eliminar):
                                        fila_idx = i + 1
                                        break
                                
                                if fila_idx:
                                    sheet.delete_rows(fila_idx)
                                    st.success(f"✅ Movimiento eliminado correctamente")
                                    clear_cache()
                                    st.session_state.editor_key += 1
                                    st.rerun()
                                else:
                                    st.error("❌ No se encontró el movimiento")
                        except Exception as e:
                            st.error(f"❌ Error al eliminar: {e}")
        
        st.caption("💡 Para eliminar una fila, seleccioná la fila (haciendo clic en el número) y luego hacé clic en el botón '🗑️ Eliminar fila seleccionada'.")
        
        # --- BOTÓN PARA EXPORTAR CSV ---
        st.markdown("---")
        csv = df_filtrado.drop(columns=['ID'], errors='ignore').to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name=f"movimientos_{mes_seleccionado}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("ℹ️ No hay movimientos para el mes seleccionado")