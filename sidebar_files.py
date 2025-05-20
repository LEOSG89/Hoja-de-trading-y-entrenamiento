# sidebar_files.py
import streamlit as st
import pandas as pd
import os
from gestor_archivos_s3 import (
    list_saved_files, save_uploaded_file, update_file,
    delete_saved_file, delete_json_state
)
from data_loader import cargar_archivo

def file_manager_sidebar(rerun):
    with st.sidebar.expander("Archivos", expanded=True):
        saved = list_saved_files()
        nombres = [f["name"] for f in saved if f["name"].lower().endswith((".csv",".xlsx"))]
        nombres.insert(0, "↑ Subir nuevo ↑")

        if "new_file" in st.session_state:
            sel = st.session_state.pop("new_file")
            st.session_state.selector_archivo = sel
            cargar_archivo()

        st.selectbox("Archivo activo:", nombres,
                     key="selector_archivo", on_change=cargar_archivo)
        
        if st.session_state.selector_archivo == "↑ Subir nuevo ↑":
            up = st.file_uploader("Sube CSV/XLSX", type=["csv","xlsx"], key="multi_uploader")
            if up:
                save_uploaded_file(up)
                base, _ = os.path.splitext(up.name)
                df_new = pd.read_csv(up)
                buf = df_new.to_json(orient="table", force_ascii=False).encode("utf-8")
                update_file(f"{base}.json", buf)
                st.session_state.new_file = up.name
                st.success(f"📥 '{up.name}' cargado. Recargando…")
                rerun()
        else:
            if st.button("🗑️ Eliminar archivo", key="delete_file"):
                st.session_state.confirm_delete = True
            if st.session_state.confirm_delete:
                st.warning(f"¿Eliminar '{st.session_state.selector_archivo}'?")
                c1, c2 = st.columns(2)
                if c1.button("✅ Sí", key="yes"):
                    delete_saved_file(st.session_state.selector_archivo)
                    delete_json_state(st.session_state.json_name)
                    st.success("Borrado.")
                    rerun()
                if c2.button("❌ No", key="no"):
                    st.session_state.confirm_delete = False 