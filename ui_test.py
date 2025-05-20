import streamlit as st

st.set_page_config(page_title="Prueba de carga", layout="wide")
st.write("✅ Streamlit está funcionando correctamente")

# PASO 1: Probar importación de gestor_archivos_s3
try:
    from gestor_archivos_s3 import init_storage
    st.success("✅ gestor_archivos_s3 importado correctamente")
except Exception as e:
    st.error(f"❌ Error al importar gestor_archivos_s3: {e}")

# PASO 2: Probar config
try:
    import config
    st.success("✅ config.py importado correctamente")
except Exception as e:
    st.error(f"❌ Error al importar config.py: {e}")

# PASO 3: Probar init_storage
try:
    # init_storage()  ← Lo dejamos comentado por ahora
    st.info("⏳ init_storage() NO ejecutado (comentado por seguridad)")
except Exception as e:
    st.error(f"❌ Error al ejecutar init_storage(): {e}")
