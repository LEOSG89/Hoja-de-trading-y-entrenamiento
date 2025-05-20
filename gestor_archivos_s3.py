import streamlit as st
import boto3
import botocore
import pandas as pd
import json
from io import BytesIO, StringIO

# Leer claves y configuración desde st.secrets
AWS_KEY = st.secrets["AWS"]["ACCESS_KEY_ID"]
AWS_SECRET = st.secrets["AWS"]["SECRET_ACCESS_KEY"]
REGION = st.secrets["AWS"].get("REGION", "us-east-1")
BUCKET = st.secrets["AWS"]["BUCKET_NAME"]
entry_prefix = st.secrets["AWS"].get("PREFIX", "")  # opcional

# Crear sesión con credenciales
session = boto3.session.Session(
    aws_access_key_id=AWS_KEY,
    aws_secret_access_key=AWS_SECRET,
    region_name=REGION,
)
s3 = session.client("s3")



def init_storage():
    """
    Verifica que el bucket exista y, si no, lo crea.
    """
    try:
        s3.head_bucket(Bucket=BUCKET)
    except botocore.exceptions.ClientError as err:
        error_code = int(err.response['Error']['Code'])
        if error_code == 404:
            s3.create_bucket(Bucket=BUCKET)
        else:
            raise


def list_saved_files() -> list[dict]:
    """
    Lista todos los archivos en S3 bajo el prefijo especificado.
    Retorna una lista de diccionarios con 'name' y 'path'.
    """
    files = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=BUCKET, Prefix=entry_prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            name = key[len(entry_prefix):] if key.startswith(entry_prefix) else key
            if name:
                files.append({'name': name, 'path': key})
    return files


def save_uploaded_file(uploaded_file) -> None:
    """
    Guarda un archivo subido (Streamlit UploadedFile) en S3.
    """
    key = f"{entry_prefix}{uploaded_file.name}"
    s3.put_object(Bucket=BUCKET, Key=key, Body=uploaded_file.getvalue())


def load_file_df(name: str) -> pd.DataFrame:
    """
    Carga un archivo CSV, XLSX/XLS o JSON (orient="table") desde S3
    y lo retorna como DataFrame.
    """
    key = f"{entry_prefix}{name}"
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    data = obj['Body'].read()

    name_lower = name.lower()
    if name_lower.endswith('.csv'):
        return pd.read_csv(BytesIO(data))
    elif name_lower.endswith('.xlsx'):
        return pd.read_excel(BytesIO(data), engine='openpyxl')
    elif name_lower.endswith('.xls'):
        return pd.read_excel(BytesIO(data), engine='xlrd')
    elif name_lower.endswith('.json'):
        text = data.decode('utf-8')
        return pd.read_json(StringIO(text), orient='table')
    else:
        raise ValueError(f"No se reconoce la extensión del archivo: {name}")


def delete_saved_file(name: str) -> None:
    """
    Elimina el archivo especificado de S3.
    """
    key = f"{entry_prefix}{name}"
    s3.delete_object(Bucket=BUCKET, Key=key)


def update_file(name: str, data: bytes) -> None:
    """
    Sobrescribe o crea un archivo en S3 con los datos proporcionados (bytes).
    """
    key = f"{entry_prefix}{name}"
    s3.put_object(Bucket=BUCKET, Key=key, Body=data)


def delete_json_state(name: str) -> None:
    """
    Elimina el JSON asociado al nombre (p. ej. 'mis_datos.json') de S3.
    """
    key = f"{entry_prefix}{name}"
    s3.delete_object(Bucket=BUCKET, Key=key)


def load_json_state(name: str) -> dict:
    """
    Descarga el JSON asociado y lo parsea a dict.
    Si no existe retorna {}.
    """
    key = f"{entry_prefix}{name}"
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=key)
        data = obj['Body'].read()
        return json.loads(data)
    except botocore.exceptions.ClientError:
        return {}
