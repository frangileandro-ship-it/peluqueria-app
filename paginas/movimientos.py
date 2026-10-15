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
    if 'tipo_actual' not in st.session_state:
        st.session_state.tipo_actual = ""
    if 'editor_key' not in st.session_state:
        st.session_state.editor_key = 0
    
    # --- 1. FORMULARIO PARA AGREGAR MOVIMIENTO (SIEMPRE VISIBLE) ---
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
        st.session_state.tipo_actual = tipo
        
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
        
        # --- MEDIO DE PAGO ---
        medio_pago = st.selectbox(
            "💳 Medio de Pago",
            ["", "Efectivo", "Tarjeta Débito", "Tarjeta Crédito", "Mercado Pago", "Otro"],
            index=0
        )
        
        # --- IMPORTE (VACÍO POR DEFECTO) ---
        importe_str = st.text_input(
            "💰 Importe ($)",
            placeholder="Ej: 1500.00",
            value=""
        )
    
    observaciones = st.text_area("📝 Observaciones", placeholder="Opcional...")
    
    # --- BOTÓN DE GUARDADO (FUERA DEL FORMULARIO) ---
    if st.button("💾 Guardar movimiento", use_container_width=True, type="primary"):
        # --- CONVERTIR IMPORTE ---
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
        
        # --- VALIDACIONES ---
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
            # Preparar datos
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
                st.session_state.editor_key += 1
                st.rerun()
    
    st.markdown("---")
    
    # --- 2. FILTRO POR MES ---
    st.subheader("🔍 Filtrar movimientos")
    
    # Obtener meses disponibles en los datos
    if not movimientos.empty and 'Fecha' in movimientos.columns:
        # Convertir fechas
        movimientos['Fecha'] = pd.to_datetime(movimientos['Fecha'], errors='coerce')
        movimientos_con_fecha = movimientos.dropna(subset=['Fecha'])
        
        if not movimientos_con_fecha.empty:
            # Obtener meses únicos con datos
            meses_disponibles = sorted(movimientos_con_fecha['Fecha'].dt.strftime('%Y-%m').unique().tolist())
            
            # Determinar mes por defecto
            mes_actual = datetime.now().strftime('%Y-%m')
            if mes_actual in meses_disponibles:
                mes_default = mes_actual
            else:
                mes_default = meses_disponibles[-1] if meses_disponibles else mes_actual
            
            # Selector de mes
            mes_seleccionado = st.selectbox(
                "📅 Seleccionar mes",
                meses_disponibles,
                index=meses_disponibles.index(mes_default) if mes_default in meses_disponibles else 0
            )
            
            # Filtrar datos por mes seleccionado
            año = int(mes_seleccionado.split('-')[0])
            mes = int(mes_seleccionado.split('-')[1])
            
            df_filtrado = movimientos_con_fecha[
                (movimientos_con_fecha['Fecha'].dt.year == año) &
                (movimientos_con_fecha['Fecha'].dt.month == mes)
            ].copy()
            
            # Mostrar nombre del mes
            nombre_mes = calendar.month_name[mes]
            st.caption(f"📌 Mostrando datos de {nombre_mes} {año}")
            
        else:
            st.warning("⚠️ No hay fechas válidas en los datos")
            df_filtrado = movimientos.copy()
    else:
        st.warning("⚠️ No hay movimientos para filtrar")
        df_filtrado = movimientos.copy()
    
    # --- 3. TABLA DE MOVIMIENTOS CON EDICIÓN Y ELIMINACIÓN ---
    if not df_filtrado.empty:
        total_filtrado = df_filtrado['Importe'].sum()
        st.info(f"📊 Mostrando {len(df_filtrado)} movimientos - Total: ${total_filtrado:,.2f}")
        
        # Ordenar por fecha (más reciente primero) y resetear índice
        df_filtrado = df_filtrado.sort_values('Fecha', ascending=False).reset_index(drop=True)
        
        # --- CREAR COPIA EDITABLE (SIN ID) ---
        df_editable = df_filtrado.drop(columns=['ID'], errors='ignore').copy()
        
        # --- CONFIGURACIÓN DE COLUMNAS PARA EDITOR ---
        column_config = {
            "Fecha": st.column_config.DateColumn(
                "Fecha",
                format="DD/MM/YYYY",
                required=True
            ),
            "Ingreso/Gasto": st.column_config.SelectboxColumn(
                "Tipo",
                options=["Ingreso", "Gasto"],
                required=True
            ),
            "Categoría": st.column_config.TextColumn(
                "Categoría",
                required=True
            ),
            "Cliente/Proveedor": st.column_config.TextColumn(
                "Cliente/Proveedor"
            ),
            "Medio de Pago": st.column_config.SelectboxColumn(
                "Medio de Pago",
                options=["Efectivo", "Tarjeta Débito", "Tarjeta Crédito", "Transferencia", "Mercado Pago", "Otro"],
                required=True
            ),
            "Importe": st.column_config.NumberColumn(
                "Importe",
                format="$%.2f",
                min_value=0,
                required=True
            ),
            "Observaciones": st.column_config.TextColumn(
                "Observaciones"
            )
        }
        
        # --- DATA EDITOR ---
        edited_df = st.data_editor(
            df_editable,
            use_container_width=True,
            column_config=column_config,
            hide_index=True,
            num_rows="dynamic",
            key=f"editor_movimientos_{st.session_state.editor_key}"
        )
        
        # --- BOTONES DE ACCIÓN ---
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            guardar = st.button("💾 Guardar cambios", use_container_width=True, type="primary")
        
        with col_btn2:
            eliminar_ultima = st.button("🗑️ Eliminar última fila", use_container_width=True)
        
        # --- GUARDAR CAMBIOS (EDICIÓN) ---
        if guardar:
            cambios_realizados = False
            
            for idx in range(min(len(edited_df), len(df_filtrado))):
                row = edited_df.iloc[idx]
                original_row = df_filtrado.iloc[idx]
                id_original = original_row['ID']
                
                # Verificar si hubo cambios
                hubo_cambio = False
                for col in df_editable.columns:
                    if col in original_row.index:
                        val_original = original_row[col]
                        val_nuevo = row[col]
                        
                        # Comparar valores
                        if pd.isna(val_original) and pd.isna(val_nuevo):
                            continue
                        if pd.isna(val_original) and not pd.isna(val_nuevo):
                            hubo_cambio = True
                            break
                        if not pd.isna(val_original) and pd.isna(val_nuevo):
                            hubo_cambio = True
                            break
                        if val_original != val_nuevo:
                            hubo_cambio = True
                            break
                
                if hubo_cambio:
                    try:
                        client = get_sheets_client()
                        if client is None:
                            st.error("❌ No se pudo conectar con Google Sheets")
                            break
                        
                        sheet = client.open_by_key(SHEET_ID).worksheet('Movimientos')
                        todas_las_filas = sheet.get_all_values()
                        
                        fila_idx = None
                        for i, fila in enumerate(todas_las_filas):
                            if i > 0 and len(fila) > 0 and fila[0] == str(id_original):
                                fila_idx = i + 1
                                break
                        
                        if fila_idx:
                            # Formatear fecha
                            if hasattr(row['Fecha'], 'strftime'):
                                fecha_str = row['Fecha'].strftime('%Y-%m-%d')
                            else:
                                fecha_str = str(row['Fecha'])
                            
                            sheet.update(f'A{fila_idx}:H{fila_idx}', [[
                                str(id_original),
                                fecha_str,
                                row['Ingreso/Gasto'],
                                row['Categoría'],
                                row['Cliente/Proveedor'] if pd.notna(row['Cliente/Proveedor']) else "",
                                row['Medio de Pago'],
                                float(row['Importe']),
                                row['Observaciones'] if pd.notna(row['Observaciones']) else ""
                            ]])
                            cambios_realizados = True
                    except Exception as e:
                        st.error(f"❌ Error al actualizar: {e}")
                        break
            
            # Detectar filas eliminadas (si el editor tiene menos filas que el original)
            if len(edited_df) < len(df_filtrado):
                try:
                    client = get_sheets_client()
                    if client is not None:
                        sheet = client.open_by_key(SHEET_ID).worksheet('Movimientos')
                        todas_las_filas = sheet.get_all_values()
                        
                        # IDs de las filas que quedaron
                        ids_restantes = []
                        for idx in range(len(edited_df)):
                            row = edited_df.iloc[idx]
                            for _, orig in df_filtrado.iterrows():
                                if (pd.notna(orig['Fecha']) and hasattr(row['Fecha'], 'strftime') and 
                                    orig['Fecha'].strftime('%Y-%m-%d') == row['Fecha'].strftime('%Y-%m-%d') and
                                    orig['Importe'] == row['Importe']):
                                    ids_restantes.append(orig['ID'])
                                    break
                        
                        ids_originales = df_filtrado['ID'].tolist()
                        ids_eliminados = [i for i in ids_originales if i not in ids_restantes]
                        
                        filas_a_eliminar = []
                        for i, fila in enumerate(todas_las_filas):
                            if i > 0 and len(fila) > 0 and fila[0] in ids_eliminados:
                                filas_a_eliminar.append(i + 1)
                        
                        for fila_idx in sorted(filas_a_eliminar, reverse=True):
                            sheet.delete_rows(fila_idx)
                        
                        if filas_a_eliminar:
                            st.success(f"✅ Se eliminaron {len(filas_a_eliminar)} movimientos")
                            cambios_realizados = True
                except Exception as e:
                    st.error(f"❌ Error al eliminar: {e}")
            
            if cambios_realizados:
                st.success("✅ Cambios guardados correctamente")
                clear_cache()
                st.session_state.editor_key += 1
                st.rerun()
            else:
                st.info("ℹ️ No se detectaron cambios")
        
        # --- ELIMINAR ÚLTIMA FILA ---
        if eliminar_ultima:
            if len(df_filtrado) > 0:
                id_ultima = df_filtrado.iloc[-1]['ID']
                try:
                    client = get_sheets_client()
                    if client is not None:
                        sheet = client.open_by_key(SHEET_ID).worksheet('Movimientos')
                        todas_las_filas = sheet.get_all_values()
                        
                        fila_idx = None
                        for i, fila in enumerate(todas_las_filas):
                            if i > 0 and len(fila) > 0 and fila[0] == str(id_ultima):
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
        
        st.caption("💡 **Para editar:** hacé doble clic en una celda, luego presioná '💾 Guardar cambios'.")
        st.caption("💡 **Para eliminar:** usá el ícono 🗑️ al final de la fila en la tabla, luego presioná '💾 Guardar cambios'.")
        
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