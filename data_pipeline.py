# data_pipeline.py
import pandas as pd
from convertir_fechas import convertir_fechas
from time_utils import calcular_tiempo_operacion_vectorizado, calcular_dia_live, calcular_tiempo_dr
from calculos_tabla_principal import (
    calcular_profit_operacion, calcular_porcentaje_profit_op, calcular_profit_total,
    calcular_dd_max, calcular_dd_up, calcular_profit_t, calcular_profit_alcanzado_vectorizado,
    calcular_profit_media_vectorizado
)
from eliminar_columnas_duplicadas_contador import limpiar_columnas
from operations import procesar_deposito_retiro

def preprocess(df):
    df = limpiar_columnas(df)
    df = convertir_fechas(
        df, 
        cols=['Fecha / Hora', 'Fecha / Hora de Cierre'],
        dayfirst=True, 
        yearfirst=False
    )
    df['Día'] = df['Fecha / Hora'].dt.weekday.map({
        0: 'Lu', 1: 'Ma', 2: 'Mi', 3: 'Ju', 
        4: 'Vi', 5: 'Sa', 6: 'Do'
    })
    df = calcular_tiempo_operacion_vectorizado(df)
    if '% Profit. Op' in df.columns and not pd.api.types.is_string_dtype(df['% Profit. Op']):
        df['% Profit. Op'] = df['% Profit. Op'].astype(str)
    df = calcular_dia_live(df)
    df = calcular_tiempo_dr(df)
    df = calcular_profit_operacion(df)
    df = calcular_porcentaje_profit_op(df)
    df = procesar_deposito_retiro(df)
    df = calcular_profit_total(df)
    df = calcular_dd_max(df)
    df = calcular_dd_up(df)
    df = calcular_profit_alcanzado_vectorizado(df)
    df = calcular_profit_media_vectorizado(df)
    df = calcular_profit_t(df)
    return df 