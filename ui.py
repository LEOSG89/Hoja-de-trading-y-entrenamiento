import streamlit as st
st.set_page_config(page_title="Hoja de Trading", page_icon="📈", layout="wide")
st.write("🚀 App iniciando correctamente (hasta este punto)")
import pandas as pd
import os, json
import config

from data_pipeline import preprocess
from data_loader import init_session, cargar_archivo  
from gestor_archivos_s3 import init_storage, update_file
from sidebar_files import file_manager_sidebar
from sidebar_settings import settings_sidebar
from copia_tabla import copiar_datos_a_tabla
from botones import crear_botones_trading, crear_botones_iv_rank
from operations import agregar_operacion, procesar_deposito_retiro
from inversion import mostrar_sidebar_inversion
from riesgo_beneficio import render_riesgo_beneficio
from aciertos_beneficios import render_aciertos_beneficios
from capital import render_tabla_capital
from Op_ganadoras_perdedoras import render_operaciones_ganadoras_perdedoras
from esperanza_matematica import render_esperanza_matematica
from comparativos_graficos_barras import mostrar_profit_interactivo
from comparativos_graficos_linea import mostrar_profit_trend_interactivo
from comparativo_mostrar_dd_max import mostrar_dd_max
from comparativo_profit_area import mostrar_profit_area
from comparativo_profit_puntos import mostrar_profit_puntos
from comparativos_tiempo_puntos import mostrar_tiempo_puntos
from comparativo_call_put_linea import comparativo_call_put_linea
from Comparativo_call_barra import comparativo_call_barra
from comparativo_put_barra import comparativo_put_barra
from comparativo_dias_linea import comparativo_dias_linea
from comparativo_trade_diario_apilado import comparativo_trade_diario_apilado
from comparativo_profit_dia_semana import comparativo_profit_dia_semana
from comparativo_dona_call_put import comparativo_dona_call_put
from time_utils import calcular_tiempo_operacion_vectorizado, calcular_dia_live, calcular_tiempo_dr
from aplicar_color_general import aplicar_color_general
from tabla_ganancia_contratos_calculos import tabla_ganancia_contratos_calculos
from comparativo_histograma_profit_call_put import histograma_profit_call_put
from comparativo_racha_operaciones_dd_max import comparativo_racha_dd_max
from comparativo_mapa_calor_tiempo import mostrar_heatmaps_dia_hora
from comparativo_calendario import mostrar_calendario
from convertir_fechas import convertir_fechas
from calculos_tabla_principal import (
    calcular_profit_operacion, calcular_porcentaje_profit_op, calcular_profit_total,
    calcular_dd_max, calcular_dd_up, calcular_profit_t, calcular_profit_alcanzado_vectorizado,
    calcular_profit_media_vectorizado
)
from eliminar_columnas_duplicadas_contador import limpiar_columnas
from tabla_editable_eliminar_renombrar_limpiar_columnas import tabla_editable_eliminar_renombrar_limpiar_columnas

try:
    rerun = st.experimental_rerun
except AttributeError:
    from streamlit.runtime.scriptrunner.script_runner import RerunException, get_script_run_ctx
    def rerun():
        raise RerunException(get_script_run_ctx())


SELECT_FILE = 'selected_asset.json'



init_session(config)
#init_storage()
# ⚠️ Temporalmente desactivado para test
# init_storage()
st.write("✅ init_storage() desactivado temporalmente para prueba")

# ————— Inicialización de flags que usa sidebar_files.py —————
if 'loaded_file_name' not in st.session_state:
    st.session_state.loaded_file_name = None

if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = False

if 'pintar_colores' not in st.session_state:
    st.session_state.pintar_colores = False

file_manager_sidebar(rerun)

settings_sidebar(config, SELECT_FILE, tabla_editable_eliminar_renombrar_limpiar_columnas)

# Asegurarnos de que siempre haya un DataFrame en session_state.datos
if st.session_state.get("datos") is None:
    init_session()

df = preprocess(st.session_state.datos.copy())
st.session_state.datos = df

# STEP 4: auto-guardar estado completo en JSON (solo si json_name está definido)
if st.session_state.get("json_name"):
    buf_json = st.session_state.datos.to_json(
        orient="table", force_ascii=False
    ).encode("utf-8")

    update_file(st.session_state.json_name, buf_json)


render_riesgo_beneficio(df)
render_aciertos_beneficios(df)
render_operaciones_ganadoras_perdedoras(df)
render_tabla_capital(df)
mostrar_sidebar_inversion(df)
render_esperanza_matematica(df)

with st.sidebar.expander("Ganancia por Contratos", expanded=False):
    tabla_ganancia_contratos_calculos()

with st.expander("Modo de entrenamiento", expanded=True):
    if 'pintar_colores' not in st.session_state:
        st.session_state.pintar_colores = True
    st.session_state.pintar_colores = st.checkbox(
        "Aplicar colores en la tabla",
        value=st.session_state.pintar_colores
    )
    crear_botones_trading()
    crear_botones_iv_rank()

if st.session_state.get('pintar_colores_disable_pending', False):
    st.session_state.pintar_colores = False
    st.session_state.pintar_colores_disable_pending = False

tab_vista, tab_edicion = st.tabs(["Vista", "Edición"])

with tab_vista:
    df_vista = df.copy()
    if 'Contador' in df_vista.columns:
        df_vista = df_vista.drop(columns=['Contador'])
    styled_df_vista = aplicar_color_general(df_vista)

    if styled_df_vista is not None:
        st.dataframe(styled_df_vista, width=st.session_state.w, height=st.session_state.h)
    else:
        st.dataframe(df_vista, width=st.session_state.w, height=st.session_state.h)

    opciones_graficos = {
        "Barras": mostrar_profit_interactivo,
        "Líneas": mostrar_profit_trend_interactivo,
        "DD/Max": mostrar_dd_max,
        "Área": mostrar_profit_area,
        "Puntos": mostrar_profit_puntos,
        "Tiempo": mostrar_tiempo_puntos,
        "CALL vs PUT Línea": comparativo_call_put_linea,
        "CALL Barras": comparativo_call_barra,
        "PUT Barras": comparativo_put_barra,
        "Días Línea": comparativo_dias_linea,
        "CALL/PUT por Día (Apilado)": comparativo_trade_diario_apilado,
        "Profit por Día de Semana": comparativo_profit_dia_semana,
        "Porcentaje Aciertos CALL PUT (Dona)": comparativo_dona_call_put,
        "Histograma Profit CALL/PUT": histograma_profit_call_put,
        "Racha Operaciones DD/Max": comparativo_racha_dd_max,
        "Mapa de calor Tiempo": mostrar_heatmaps_dia_hora,
        "Calendario": mostrar_calendario,
    }

    secciones = [
        ("", "rango_col1", "rango_col2"),
        (" Secundarios", "rango_col3", "rango_col4")
    ]
    for seccion, rango1, rango2 in secciones:
        expanded = True if seccion == "" else False
        with st.expander(f"Gráficos Comparativos{seccion}", expanded=expanded):
            select_col1, select_col2 = st.columns(2, gap="medium")

            with select_col1:
                grafico_col1 = st.selectbox(
                    f"Gráfico Columna 1{seccion}",
                    list(opciones_graficos.keys()),
                    index=list(opciones_graficos.keys()).index(
                        "Racha Operaciones DD/Max" if seccion == "" else "Porcentaje Aciertos CALL PUT (Dona)"
                    ),
                    key=f"grafico_1{seccion}"
                )

            with select_col2:
                grafico_col2 = st.selectbox(
                    f"Gráfico Columna 2{seccion}",
                    list(opciones_graficos.keys()),
                    index=list(opciones_graficos.keys()).index(
                        "CALL vs PUT Línea" if seccion == "" else "DD/Max"
                    ),
                    key=f"grafico_2{seccion}"
                )

            # COLUMNAS DE GRÁFICOS CORREGIDAS
            col1, col2 = st.columns(2, gap="small")

            with col1:
                if grafico_col1 == "Calendario":
                    mostrar_calendario(
                        df,
                        chart_key=f"chart_1_{grafico_col1}{seccion}"
                    )
                else:
                    opciones_graficos[grafico_col1](
                        df.iloc[
                            st.session_state[rango1][0]
                            :st.session_state[rango1][1] + 1
                        ],
                        chart_key=f"chart_1_{grafico_col1}{seccion}"
                    )

            with col2:
                if grafico_col2 == "Calendario":
                    mostrar_calendario(
                        df,
                        chart_key=f"chart_2_{grafico_col2}{seccion}"
                    )
                else:
                    opciones_graficos[grafico_col2](
                        df.iloc[
                            st.session_state[rango2][0]
                            :st.session_state[rango2][1] + 1
                        ],
                        chart_key=f"chart_2_{grafico_col2}{seccion}"
                    )

with tab_edicion:
    df_ed = df.reset_index(drop=True).copy()
    df_ed.insert(0, 'Contador', df_ed.index)
    df_ed['Eliminar'] = False
    df_ed.drop(columns=[''], inplace=True, errors='ignore')

    numeric_cols = ['#Cont', 'STRK Buy', 'STRK Sell', 'Deposito', 'Retiro', 'Profit']
    for col in numeric_cols:
        if col in df_ed.columns:
            df_ed[col] = pd.to_numeric(df_ed[col], errors='coerce')

    for txt in ['T. Op', 'Tiempo D/R', '% Profit. Op', 'Profit Tot.', 'Profit Alcanzado', 'Profit Media']:
        if txt in df_ed.columns:
            df_ed[txt] = df_ed[txt].fillna('').astype(str)

    col_config = {'Contador': st.column_config.NumberColumn("Contador", disabled=True)}
    for col in df_ed.columns[2:]:
        if pd.api.types.is_bool_dtype(df_ed[col]):
            continue
        elif pd.api.types.is_numeric_dtype(df_ed[col]):
            col_config[col] = st.column_config.NumberColumn(col)
        elif pd.api.types.is_datetime64_any_dtype(df_ed[col]):
            col_config[col] = st.column_config.DatetimeColumn(col)
        else:
            col_config[col] = st.column_config.TextColumn(col)

    edited = st.data_editor(
        df_ed,
        column_config=col_config,
        hide_index=True,
        width=st.session_state.w,
        height=st.session_state.h,
        num_rows="dynamic"
    )
    filtered = edited[edited['Eliminar'] == False]
    filtered = filtered.drop(columns=['Contador', 'Eliminar']).reset_index(drop=True)
    st.session_state.datos = filtered
    
