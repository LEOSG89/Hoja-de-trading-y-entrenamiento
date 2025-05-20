import streamlit as st
import pandas as pd
import os
import time
from io import BytesIO

# Archivo para persistencia de la tabla editada
STORAGE_FILE = "tabla_edicion.json"

# Importa la función de subida a S3
auto_save_available = False
try:
    from gestor_archivos_s3 import update_file
    auto_save_available = True
except ImportError:
    auto_save_available = False


def eliminar_columna(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
    if col_name in df.columns:
        df.drop(columns=[col_name], inplace=True)
        st.success(f"Columna '{col_name}' eliminada.")
    else:
        st.warning(f"No existe la columna '{col_name}'.")
    return df


def eliminar_fila(df: pd.DataFrame, row_indices: list) -> pd.DataFrame:
    if row_indices:
        for idx in sorted(map(int, row_indices), reverse=True):
            if idx in df.index:
                df.drop(index=idx, inplace=True)
        df.reset_index(drop=True, inplace=True)
        st.success(f"Filas eliminadas: {', '.join(map(str, row_indices))}")
    else:
        st.warning("Sin filas seleccionadas para eliminar.")
    return df


def tabla_editable_eliminar_renombrar_limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    # 1) Cargar datos persistidos si df está vacío
    if df.empty and os.path.exists(STORAGE_FILE):
        try:
            stored = pd.read_json(STORAGE_FILE, orient="table")
            df = stored.copy()
        except Exception:
            st.warning("No se pudo cargar datos previos, usando el DataFrame actual.")

    # 2) Asegurar columnas personalizadas
    for col in ['Notas', 'Fotos']:
        if col not in df.columns:
            df[col] = ""

    # 3) Crear pestañas principales
    outer_tabs = st.tabs(["Editar Filas", "Editar Columnas"])
    tab_rows, tab_cols = outer_tabs

    # --- EDITAR FILAS ---
    with tab_rows:
        row_tabs = st.tabs(["Vaciar Filas", "Mover Filas", "Editar / Agregar Fila", "Eliminar Filas"])
        tab_clear, tab_move, tab_edit, tab_delete = row_tabs

        # Vaciar Filas
        with tab_clear:
            st.divider()
            opts = [str(i) for i in df.index]
            to_clear = st.multiselect("Selecciona filas a vaciar", opts, key="tab_clear_rows")
            if st.button("Vaciar filas", key="tab_clear_btn"):
                if to_clear:
                    for r in to_clear:
                        df.loc[int(r), :] = ""
                    st.success(f"Filas vaciadas: {', '.join(to_clear)}")
                else:
                    st.warning("Sin filas seleccionadas.")

        # Mover Filas
        with tab_move:
            st.divider()
            if not df.empty:
                opts = [str(i) for i in df.index]
                src = st.selectbox("Selecciona fila a mover", opts, key="tab_move_src")
                dest = st.number_input(f"Mover antes de índice (0 a {len(df)})", 0, len(df), int(src), key="tab_move_dest")
                if st.button("Mover fila", key="tab_move_btn"):
                    idx = int(src)
                    if idx != dest:
                        row = df.loc[idx].copy()
                        df.drop(index=idx, inplace=True)
                        df.reset_index(drop=True, inplace=True)
                        top = df.iloc[:dest]
                        bottom = df.iloc[dest:]
                        df = pd.concat([top, pd.DataFrame([row]), bottom], ignore_index=True)
                        st.success(f"Fila {idx} movida a posición {dest}.")

        # Editar / Agregar Fila
        with tab_edit:
            st.divider()
            campos = df.columns.tolist()
            opciones = ['Nueva fila'] + [str(i) for i in df.index]
            choice = st.selectbox("Selecciona fila a editar o 'Nueva fila'", opciones, key="tab_edit_choice")
            inputs = {}

            if choice == 'Nueva fila':
                st.write("**Agregar nueva fila**")
                for col in campos:
                    inputs[col] = st.text_input(f"{col}", key=f"new_{col}")
                if st.button("Agregar fila", key="tab_add_row"):
                    new = {c: inputs.get(c, "") for c in campos}
                    df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
                    st.success("Nueva fila agregada.")
            else:
                idx = int(choice)
                st.write(f"**Editar fila {idx}**")
                for col in campos:
                    val = df.at[idx, col]
                    val_str = '' if pd.isna(val) else str(val)
                    inputs[col] = st.text_input(f"{col}", value=val_str, key=f"edit_{col}_{idx}")
                if st.button("Guardar cambios", key="tab_save_row"):
                    for col in campos:
                        if inputs[col] != ('' if pd.isna(df.at[idx, col]) else str(df.at[idx, col])):
                            df.at[idx, col] = inputs[col]
                    st.success(f"Fila {idx} actualizada.")

        # Eliminar Filas
        with tab_delete:
            st.divider()
            opts = [str(i) for i in df.index]
            to_del = st.multiselect("Selecciona filas a eliminar", opts, key="tab_delete_rows")
            if st.button("Eliminar filas", key="tab_delete_btn"):
                df = eliminar_fila(df, to_del)

    # --- EDITAR COLUMNAS ---
    with tab_cols:
        col_tabs = st.tabs(["Renombrar Cols", "Eliminar Cols", "Vaciar Cols", "Agregar Cols"])
        tab_ren, tab_del, tab_clear_col, tab_add = col_tabs

        with tab_ren:
            st.divider()
            cols = df.columns.tolist()
            src = st.selectbox("Columna a renombrar", cols, key="tab_ren_src")
            new = st.text_input("Nuevo nombre", value=src, key="tab_ren_new")
            if st.button("Renombrar", key="tab_ren_btn"):
                if not new:
                    st.warning("El nombre no puede estar vacío.")
                elif new in df.columns:
                    st.error(f"'{new}' ya existe.")
                else:
                    df.rename(columns={src: new}, inplace=True)
                    st.success(f"{src} renombrada a {new}.")

        with tab_del:
            st.divider()
            opts = df.columns.tolist()
            to_del_cols = st.multiselect("Columnas a eliminar", opts, key="tab_del_cols")
            if st.button("Eliminar cols", key="tab_del_btn"):
                for c in to_del_cols:
                    df = eliminar_columna(df, c)

        with tab_clear_col:
            st.divider()
            opts = df.columns.tolist()
            to_clear_cols = st.multiselect("Columnas a vaciar", opts, key="tab_clear_cols")
            if st.button("Vaciar cols", key="tab_clear_cols_btn"):
                for c in to_clear_cols:
                    df[c] = ""
                st.success(f"Columnas vaciadas: {', '.join(to_clear_cols)}")

        with tab_add:
            st.divider()
            name = st.text_input("Nombre nueva columna", key="tab_add_name")
            if st.button("Agregar col", key="tab_add_btn"):
                if name and name not in df.columns:
                    df[name] = ["" for _ in range(len(df))]
                    st.success(f"Columna '{name}' agregada.")
                else:
                    st.warning("Nombre inválido o ya existe.")

    # 4) Guardar o limpiar persistencia manual
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Guardar tabla CSV", key="save_tabla_csv"):
            try:
                df.to_json(STORAGE_FILE, orient="table", force_ascii=False)
                st.session_state['tabla_last_save'] = time.time()

                buf = BytesIO()
                df.to_csv(buf, index=False, encoding="utf-8")
                buf.seek(0)

                csv_key = STORAGE_FILE.replace(".json", ".csv")
                update_file(csv_key, buf.getvalue())

                st.success("✅ Datos guardados y subidos a S3 como CSV")
            except Exception as e:
                st.error(f"Error guardando: {e}")

    with col2:
        if st.button("🗑️ Limpiar tabla", key="clear_tabla"):
            if os.path.exists(STORAGE_FILE):
                os.remove(STORAGE_FILE)
            df = df.iloc[0:0]
            st.success("Tabla limpiada. Refresca la página para reiniciar completamente.")

    # 5) Auto-guardado cada 60s (JSON local + CSV a S3)
    now = time.time()
    last = st.session_state.get('tabla_last_save', None)
    if last is None:
        st.session_state['tabla_last_save'] = now
    elif now - last > 60:
        try:
            df.to_json(STORAGE_FILE, orient="table", force_ascii=False)
            st.session_state['tabla_last_save'] = time.time()
            buf = BytesIO()
            df.to_csv(buf, index=False, encoding="utf-8")
            buf.seek(0)
            csv_key = STORAGE_FILE.replace(".json", ".csv")
            update_file(csv_key, buf.getvalue())
            st.info("Auto-guardado: JSON local y CSV subido a S3 ✅")
        except Exception:
            st.warning("No se pudo auto-guardar en S3")

    # 6) Retornar df siempre
    return df
