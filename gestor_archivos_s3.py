import streamlit as st
import boto3
import botocore
import pandas as pd
import json
from io import BytesIO, StringIO

# ✅ Función para crear cliente y credenciales
def crear_cliente_s3():
    AWS_KEY = st.secrets["AWS"]["ACCESS_KEY_ID"]
    AWS_SECRET = st.secrets["AWS"]["SECRET_ACCESS_KEY"]
    REGION = st.secrets["AWS"].get("REGION", "us-east-1")
    BUCKET = st.secrets["AWS"]["BUCKET_NAME"]
    PREFIX = st.secrets["AWS"].get("PREFIX", "")
    
    session = boto3.session.Session(
        aws_access_key_id=AWS_KEY,
        aws_secret_access_key=AWS_SECRET,
        region_name=REGION,
    )
    s3 = session.client("s3")
    return s3, BUCKET, PREFIX

# ✅ Solo una definición de init_storage
def init_storage():
    s3, BUCKET, _ = crear_cliente_s3()
    try:
        s3.head_bucket(Bucket=BUCKET)
    except botocore.exceptions.ClientError as err:
        st.warning(f"No se pudo verificar el bucket: {err}")

def list_saved_files() -> list[dict]:
    s3, BUCKET, entry_prefix = crear_cliente_s3()
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
    s3, BUCKET, entry_prefix = crear_cliente_s3()
    key = f"{entry_prefix}{uploaded_file.name}"
    s3.put_object(Bucket=BUCKET, Key=key, Body=uploaded_file.getvalue())

def load_file_df(name: str) -> pd.DataFrame:
    s3, BUCKET, entry_prefix = crear_cliente_s3()
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
    s3, BUCKET, entry_prefix = crear_cliente_s3()
    key = f"{entry_prefix}{name}"
    s3.delete_object(Bucket=BUCKET, Key=key)

def update_file(name: str, data: bytes) -> None:
    s3, BUCKET, entry_prefix = crear_cliente_s3()
    key = f"{entry_prefix}{name}"
    s3.put_object(Bucket=BUCKET, Key=key, Body=data)

def delete_json_state(name: str) -> None:
    s3, BUCKET, entry_prefix = crear_cliente_s3()
    key = f"{entry_prefix}{name}"
    s3.delete_object(Bucket=BUCKET, Key=key)

def load_json_state(name: str) -> dict:
    s3, BUCKET, entry_prefix = crear_cliente_s3()
    key = f"{entry_prefix}{name}"
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=key)
        data = obj['Body'].read()
        return json.loads(data)
    except botocore.exceptions.ClientError:
        return {}
