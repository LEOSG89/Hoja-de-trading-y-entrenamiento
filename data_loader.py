# data_loader.py
import os, json, pandas as pd
from io import BytesIO
import botocore
import streamlit as st
from gestor_archivos_s3 import s3, BUCKET, entry_prefix, load_file_df
from settings import SELECT_FILE  # donde defines el nombre JSON de activo


def init_session(config):
    """Inicializa st.session_state con columnas, dimensiones y activo seleccionado."""
    # 1) Columnas del DataFrame
    if os.path.exists(config.COL_FILE):
        try:
            with open(config.COL_FILE, 'r') as f:
                cols = json.load(f)
        except:
            cols = config.FIXED_COLS
    else:
        cols = config.FIXED_COLS

    # 2) DataFrame vacío en sesión si no existe
    if 'datos' not in st.session_state or st.session_state.datos is None:
        st.session_state.datos = pd.DataFrame(columns=cols)

    # 3) Dimensiones de la vista (h, w)
    if 'h' not in st.session_state or 'w' not in st.session_state:
        if os.path.exists(config.TABLE_FILE):
            try:
                with open(config.TABLE_FILE, 'r') as f:
                    cfg = json.load(f)
                st.session_state.h = cfg.get('height', 400)
                st.session_state.w = cfg.get('width', 800)
            except:
                st.session_state.h, st.session_state.w = 400, 800
        else:
            st.session_state.h, st.session_state.w = 400, 800

    # 4) Activo seleccionado
    if 'selected_asset' not in st.session_state:
        if os.path.exists(SELECT_FILE):
            try:
                with open(SELECT_FILE, 'r') as f:
                    sel = json.load(f)
                st.session_state.selected_asset = sel if sel in config.ASSETS else config.ASSETS[0]
            except:
                st.session_state.selected_asset = config.ASSETS[0]
        else:
            st.session_state.selected_asset = config.ASSETS[0]


def cargar_archivo():
    """Callback para cargar CSV/XLSX o JSON desde S3 en st.session_state.datos."""
    choice = st.session_state.selector_archivo
    if choice == "↑ Subir nuevo ↑":
        st.session_state.json_name = None
        return
    base = os.path.splitext(choice)[0]
    st.session_state.json_name = f"{base}.json"
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=f"{entry_prefix}{st.session_state.json_name}")
        df = pd.read_json(BytesIO(obj["Body"].read()), orient="table")
    except botocore.exceptions.ClientError:
        df = load_file_df(choice)
    if df is not None:
        st.session_state.datos = df 