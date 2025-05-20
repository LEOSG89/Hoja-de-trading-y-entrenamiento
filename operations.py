import streamlit as st
import pandas as pd
from datetime import datetime
import config
from combertir_hora_local import obtener_hora_local

def agregar_operacion(porcentaje: float, tipo_op: str) -> None:
    """
    Agrega una operación CALL, PUT, DEP o RET con timestamp y día local correcto.
    Modifica directamente st.session_state.datos.
    """
    # Partir del DataFrame actual
    df = st.session_state.datos.copy()

    # Timestamp y día
    ahora = obtener_hora_local()  # por defecto: America/New_York
    dias = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa', 'Do']
    dia_sem = dias[ahora.weekday()]

    # Asset y valor de input
    asset = st.session_state.get('selected_asset', '')
    val = float(st.session_state.get('input_valor', 0) or 0)

    # Construir nueva fila con las columnas fijas
    row = {col: None for col in config.FIXED_COLS}
    row['Activo'] = asset
    row['Fecha / Hora'] = ahora.strftime('%Y-%m-%d %H:%M:%S')
    row['Fecha / Hora de Cierre'] = ahora.strftime('%Y-%m-%d %H:%M:%S')
    row['Día'] = dia_sem

    if asset == 'DEP':
        row['Deposito'] = val
        row['Profit'] = val
    elif asset == 'RET':
        row['Retiro'] = -val
        row['Profit'] = -val
    else:
        row['C&P'] = tipo_op
        row['D'] = '3d'
        strike_buy = st.session_state.get('monto_invertir', 0.0)
        row['#Cont'] = 1
        row['STRK Buy'] = strike_buy
        row['STRK Sell'] = strike_buy * (1 + porcentaje / 100)
        row['Profit'] = (row['STRK Sell'] - row['STRK Buy']) * row['#Cont']

    nueva = pd.DataFrame([row])

    # Convertir strings de fecha a datetime
    for col in ['Fecha / Hora', 'Fecha / Hora de Cierre']:
        nueva[col] = pd.to_datetime(nueva[col], errors='coerce')

    # Concatenar al DataFrame existente, omitiendo filas totalmente nulas
    df0 = df.dropna(how='all')
    df_final = pd.concat([df0, nueva], ignore_index=True)

    # Actualizar la sesión
    st.session_state.datos = df_final


def procesar_deposito_retiro(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajusta las columnas de depósito/retiro y profit según corresponda.
    """
    df = df.copy()

    df['Deposito'] = pd.to_numeric(df['Deposito'], errors='coerce')
    df['Retiro']   = pd.to_numeric(df['Retiro'], errors='coerce')

    dep_num = df['Deposito']
    ret_num = df['Retiro']

    mask_dep = dep_num > 0
    mask_ret = ret_num.notna()

    df.loc[mask_dep, 'Profit'] = dep_num[mask_dep]
    df.loc[mask_dep, 'Activo'] = 'DEP'
    df.loc[mask_ret, 'Profit'] = -ret_num[mask_ret].abs()
    df.loc[mask_ret, 'Activo'] = 'RET'

    cols_limpieza = ['C&P', 'D', '#Cont', 'STRK Buy', 'STRK Sell']
    for col in cols_limpieza:
        if col in df.columns:
            df.loc[mask_dep | mask_ret, col] = pd.NA

    return df


def agregar_iv_rank(rank_str: str) -> None:
    """
    Asigna el valor de IV Rank a la última fila del DataFrame.
    Modifica directamente st.session_state.datos.
    """
    df = st.session_state.datos.copy()
    if not df.empty:
        last_idx = df.index[-1]
        df.at[last_idx, 'IV Rank'] = rank_str

    st.session_state.datos = df
