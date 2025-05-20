# sidebar_settings.py
import streamlit as st
import json

def settings_sidebar(config, SELECT_FILE, tabla_editable_func):
    with st.sidebar.expander("Cargar y Ajustes", expanded=True):
        # sliders h, w
        st.slider("Alto Vista", 200, 1200, st.session_state.h, key='h')
        st.slider("Ancho Vista", 200, 2000, st.session_state.w, key='w')
        
        # rangos de gráficos (tab1..4)
        st.markdown("### Ajustar Rangos de Gráficos")
        total_filas = len(st.session_state.datos) - 1
        tab1, tab2, tab3, tab4 = st.tabs(["Columna 1", "Columna 2", "Columna 3", "Columna 4"])

        for i, tab in enumerate([tab1, tab2, tab3, tab4], start=1):
            with tab:
                rows = len(st.session_state.datos)
                max_idx = rows - 1
                if max_idx > 0:
                    preset = st.radio(
                        "Preset",
                        [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 150, 200, 250, 'ALL'],
                        index=1, horizontal=True,
                        key=f"preset_col{i}"
                    )
                    filas_default = max_idx if preset == 'ALL' else min(int(preset), max_idx)
                    start = max(0, max_idx - filas_default)
                    end = max_idx
                    rango_slider = st.slider(
                        f"Rango de filas Gráfico Columna {i}",
                        min_value=0,
                        max_value=max_idx,
                        value=(start, end),
                        key=f"filas_col{i}"
                    )
                else:
                    st.info("No hay suficientes filas para seleccionar un rango.")
                    rango_slider = (0, max_idx if max_idx >= 0 else 0)

                st.session_state[f"rango_col{i}"] = rango_slider
                st.caption(
                    f"Mostrando filas desde **{rango_slider[0]}** hasta **{rango_slider[1]}** de **{max_idx if max_idx>=0 else 0}** filas."
                )

        # selector activo y valor
        sel = st.selectbox(
            "Selecciona Activo",
            config.ASSETS,
            index=config.ASSETS.index(st.session_state.selected_asset),
            key='selected_asset'
        )
        st.number_input("Valor (solo DEP/RET)", value=0.0, key='input_valor')

        # tabla editable
        st.session_state.datos = tabla_editable_func(st.session_state.datos)

        # persistir h,w y selected_asset
        with open(config.TABLE_FILE, 'w') as f:
            json.dump({'height': st.session_state.h, 'width': st.session_state.w}, f)
        with open(SELECT_FILE, 'w') as f:
            json.dump(sel, f) 