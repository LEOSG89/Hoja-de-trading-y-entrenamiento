import streamlit as st

# Configuración inicial
st.set_page_config(page_title="Test S3", layout="wide")
st.title("🔍 Prueba de conexión S3")

# Paso 1: Importar correctamente el cliente
try:
    from gestor_archivos_s3 import crear_cliente_s3, init_storage
    st.success("✅ Módulo 'gestor_archivos_s3' importado correctamente.")
except Exception as e:
    st.error(f"❌ Error al importar gestor_archivos_s3: {e}")
    st.stop()

# Paso 2: Probar la creación del cliente S3
try:
    s3, bucket, prefix = crear_cliente_s3()
    st.success(f"✅ Cliente S3 creado con éxito. Bucket: {bucket}, Prefijo: {prefix}")
except Exception as e:
    st.error(f"❌ Error al crear cliente S3: {e}")
    st.stop()

# Paso 3: Probar init_storage (verifica el bucket)
try:
    init_storage()
    st.success("✅ init_storage() ejecutado correctamente (bucket verificado o manejado).")
except Exception as e:
    st.error(f"❌ Error en init_storage(): {e}")
