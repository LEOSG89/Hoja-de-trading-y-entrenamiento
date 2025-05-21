import streamlit as st
st.set_page_config(page_title="Test", layout="wide")
st.write("✅ Streamlit arrancó sin bloquearse")

try:
    from gestor_archivos_s3 import crear_cliente_s3
    st.success("✅ gestor_archivos_s3 importado sin colgarse")
except Exception as e:
    st.error(f"❌ Error al importar gestor_archivos_s3: {e}")
