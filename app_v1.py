import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SGI Risk Analytics",
    page_icon="⚠️",
    layout="wide"
)

# ============================================================
# FUNCIONES
# ============================================================

def clasificar_riesgo(nivel):
    if nivel <= 4:
        return "Bajo"
    elif nivel <= 9:
        return "Moderado"
    elif nivel <= 14:
        return "Alto"
    elif nivel <= 19:
        return "Muy Alto"
    else:
        return "Crítico"


def prioridad_riesgo(nivel, impacto_estrategico):
    """
    La prioridad considera:
    - Nivel de riesgo = Probabilidad x Impacto
    - Impacto estratégico de 1 a 5
    """

    puntaje = nivel * impacto_estrategico

    if puntaje >= 80:
        return "Crítica"
    elif puntaje >= 50:
        return "Alta"
    elif puntaje >= 25:
        return "Media"
    else:
        return "Baja"


def color_riesgo(nivel):
    if nivel <= 4:
        return "#2E7D32"       # Verde
    elif nivel <= 9:
        return "#F9A825"       # Amarillo
    elif nivel <= 14:
        return "#EF6C00"       # Naranja
    elif nivel <= 19:
        return "#C62828"       # Rojo
    else:
        return "#6A1B9A"       # Morado


# ============================================================
# DATOS INICIALES
# ============================================================

if "riesgos" not in st.session_state:

    st.session_state.riesgos = pd.DataFrame(
        columns=[
            "ID",
            "Proceso",
            "Tipo",
            "Descripción",
            "Causa",
            "Consecuencia",
            "Probabilidad",
            "Impacto",
            "Nivel de Riesgo",
            "Clasificación",
            "Impacto Estratégico",
            "Puntaje Estratégico",
            "Prioridad"
        ]
    )


# ============================================================
# ENCABEZADO
# ============================================================

st.title("⚠️ SGI Risk Analytics")

st.subheader(
    "Sistema de identificación, evaluación, análisis y priorización de riesgos"
)

st.markdown(
    """
    Esta herramienta permite gestionar los riesgos del **Sistema de Gestión Integrado (SGI)**,
    considerando la valoración de **probabilidad, impacto e impacto estratégico** en una
    escala de **1 a 5**.
    """
)

st.divider()


# ============================================================
# MENÚ LATERAL
# ============================================================

st.sidebar.title("Navegación")

opcion = st.sidebar.radio(
    "Seleccione una opción:",
    [
        "🏠 Inicio",
        "➕ Identificar riesgo",
        "📊 Evaluación y análisis",
        "🔥 Mapa de calor",
        "🎯 Priorización",
        "📋 Registro de riesgos"
    ]
)


# ============================================================
# INICIO
# ============================================================

if opcion == "🏠 Inicio":

    st.header("Gestión Integral del Riesgo")

    col1, col2, col3, col4 = st.columns(4)

    total_riesgos = len(st.session_state.riesgos)

    if total_riesgos > 0:
        altos = len(
            st.session_state.riesgos[
                st.session_state.riesgos["Nivel de Riesgo"] >= 10
            ]
        )

        criticos = len(
            st.session_state.riesgos[
                st.session_state.riesgos["Nivel de Riesgo"] >= 20
            ]
        )

        estrategicos = len(
            st.session_state.riesgos[
                st.session_state.riesgos["Impacto Estratégico"] >= 4
            ]
        )
    else:
        altos = 0
        criticos = 0
        estrategicos = 0

    col1.metric("Total de riesgos", total_riesgos)
    col2.metric("Riesgos altos o superiores", altos)
    col3.metric("Riesgos críticos", criticos)
    col4.metric("Impacto estratégico alto", estrategicos)

    st.divider()

    st.markdown(
        """
        ### 🔄 Ciclo de gestión del riesgo

        **1. Identificación → 2. Evaluación → 3. Análisis → 4. Priorización → 5. Tratamiento**

        El objetivo de la herramienta es transformar la información de los riesgos en
        información útil para la toma de decisiones.
        """
    )

    st.info(
        "La valoración utiliza una escala de 1 a 5 para probabilidad, impacto e impacto estratégico."
    )


# ============================================================
# IDENTIFICACIÓN
# ============================================================

elif opcion == "➕ Identificar riesgo":

    st.header("➕ Identificación del riesgo")

    st.write(
        "Registre la información inicial del riesgo para posteriormente realizar su evaluación."
    )

    with st.form("formulario_riesgo"):

        col1, col2 = st.columns(2)

        with col1:

            proceso = st.text_input(
                "Proceso asociado",
                placeholder="Ejemplo: Facturación"
            )

            tipo = st.selectbox(
                "Tipo de riesgo",
                [
                    "Estratégico",
                    "Operativo",
                    "Financiero",
                    "Tecnológico",
                    "Talento Humano",
                    "Seguridad de la Información",
                    "Legal / Cumplimiento",
                    "Reputacional",
                    "Clínico / Asistencial",
                    "Otro"
                ]
            )

            descripcion = st.text_area(
                "Descripción del riesgo",
                placeholder="Describa claramente qué puede ocurrir..."
            )

        with col2:

            causa = st.text_area(
                "Causa",
                placeholder="¿Por qué podría ocurrir?"
            )

            consecuencia = st.text_area(
                "Consecuencia",
                placeholder="¿Qué podría ocurrir si el riesgo se materializa?"
            )

        st.subheader("Valoración del riesgo")

        col1, col2, col3 = st.columns(3)

        with col1:

            probabilidad = st.slider(
                "Probabilidad",
                min_value=1,
                max_value=5,
                value=3,
                help="1 = Muy baja | 5 = Muy alta"
            )

        with col2:

            impacto = st.slider(
                "Impacto",
                min_value=1,
                max_value=5,
                value=3,
                help="1 = Muy bajo | 5 = Muy alto"
            )

        with col3:

            impacto_estrategico = st.slider(
                "Impacto estratégico",
                min_value=1,
                max_value=5,
                value=3,
                help="1 = Bajo impacto estratégico | 5 = Impacto estratégico crítico"
            )

        enviar = st.form_submit_button(
            "💾 Registrar riesgo",
            use_container_width=True
        )

    if enviar:

        if not proceso or not descripcion:
            st.error(
                "Debe diligenciar como mínimo el proceso y la descripción del riesgo."
            )

        else:

            nivel = probabilidad * impacto

            clasificacion = clasificar_riesgo(nivel)

            puntaje_estrategico = nivel * impacto_estrategico

            prioridad = prioridad_riesgo(
                nivel,
                impacto_estrategico
            )

            nuevo_id = f"R-{len(st.session_state.riesgos) + 1:03d}"

            nuevo_riesgo = pd.DataFrame(
                [{
                    "ID": nuevo_id,
                    "Proceso": proceso,
                    "Tipo": tipo,
                    "Descripción": descripcion,
                    "Causa": causa,
                    "Consecuencia": consecuencia,
                    "Probabilidad": probabilidad,
                    "Impacto": impacto,
                    "Nivel de Riesgo": nivel,
                    "Clasificación": clasificacion,
                    "Impacto Estratégico": impacto_estrategico,
                    "Puntaje Estratégico": puntaje_estrategico,
                    "Prioridad": prioridad
                }]
            )

            st.session_state.riesgos = pd.concat(
                [
                    st.session_state.riesgos,
                    nuevo_riesgo
                ],
                ignore_index=True
            )

            st.success(
                f"Riesgo {nuevo_id} registrado correctamente."
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Nivel de riesgo",
                nivel
            )

            col2.metric(
                "Clasificación",
                clasificacion
            )

            col3.metric(
                "Prioridad",
                prioridad
            )


# ============================================================
# EVALUACIÓN Y ANÁLISIS
# ============================================================

elif opcion == "📊 Evaluación y análisis":

    st.header("📊 Evaluación y análisis")

    if st.session_state.riesgos.empty:

        st.warning(
            "Aún no existen riesgos registrados. Registre primero un riesgo."
        )

    else:

        df = st.session_state.riesgos.copy()

        st.subheader("Resultado de la evaluación")

        columnas = [
            "ID",
            "Proceso",
            "Probabilidad",
            "Impacto",
            "Nivel de Riesgo",
            "Clasificación",
            "Impacto Estratégico",
            "Prioridad"
        ]

        st.dataframe(
            df[columnas],
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader("Distribución de riesgos")

        conteo = df["Clasificación"].value_counts()

        fig = go.Figure(
            data=[
                go.Bar(
                    x=conteo.index,
                    y=conteo.values,
                    text=conteo.values,
                    textposition="auto"
                )
            ]
        )

        fig.update_layout(
            xaxis_title="Clasificación",
            yaxis_title="Número de riesgos",
            height=400
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# MAPA DE CALOR
# ============================================================

elif opcion == "🔥 Mapa de calor":

    st.header("🔥 Mapa de calor corporativo")

    st.write(
        "Ubicación de los riesgos según la combinación de probabilidad e impacto."
    )

    matriz = []

    for impacto in range(5, 0, -1):

        fila = []

        for probabilidad in range(1, 6):

            nivel = probabilidad * impacto

            riesgos_celda = st.session_state.riesgos[
                (st.session_state.riesgos["Probabilidad"] == probabilidad)
                &
                (st.session_state.riesgos["Impacto"] == impacto)
            ]

            ids = riesgos_celda["ID"].tolist()

            if ids:
                texto = f"{nivel}<br>" + ", ".join(ids)
            else:
                texto = str(nivel)

            fila.append(texto)

        matriz.append(fila)

    fig = go.Figure(
        data=go.Heatmap(
            z=[
                [5, 10, 15, 20, 25],
                [4, 8, 12, 16, 20],
                [3, 6, 9, 12, 15],
                [2, 4, 6, 8, 10],
                [1, 2, 3, 4, 5]
            ],
            x=[1, 2, 3, 4, 5],
            y=[5, 4, 3, 2, 1],
            text=matriz,
            texttemplate="%{text}",
            hovertemplate=(
                "Probabilidad: %{x}<br>"
                "Impacto: %{y}<br>"
                "Nivel: %{z}<extra></extra>"
            ),
            showscale=False
        )
    )

    fig.update_layout(
        xaxis_title="Probabilidad",
        yaxis_title="Impacto",
        height=600
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.caption(
        "Los números representan el nivel de riesgo resultante de Probabilidad × Impacto. "
        "Los códigos R-XXX identifican los riesgos registrados en cada posición."
    )


# ============================================================
# PRIORIZACIÓN
# ============================================================

elif opcion == "🎯 Priorización":

    st.header("🎯 Priorización estratégica de riesgos")

    st.markdown(
        """
        La priorización combina el **nivel de riesgo** con el **impacto estratégico**.
        
        **Puntaje estratégico = Nivel de riesgo × Impacto estratégico**
        
        Esto permite diferenciar riesgos que pueden tener un nivel similar en el mapa
        de calor, pero que generan consecuencias estratégicas diferentes para la organización.
        """
    )

    if st.session_state.riesgos.empty:

        st.warning(
            "Aún no existen riesgos registrados."
        )

    else:

        df = st.session_state.riesgos.copy()

        df = df.sort_values(
            by="Puntaje Estratégico",
            ascending=False
        )

        st.subheader("Ranking de riesgos")

        st.dataframe(
            df[
                [
                    "ID",
                    "Proceso",
                    "Tipo",
                    "Nivel de Riesgo",
                    "Clasificación",
                    "Impacto Estratégico",
                    "Puntaje Estratégico",
                    "Prioridad"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader("Top de riesgos prioritarios")

        top_riesgos = df.head(10)

        fig = go.Figure(
            data=[
                go.Bar(
                    x=top_riesgos["Puntaje Estratégico"],
                    y=top_riesgos["ID"],
                    orientation="h",
                    text=top_riesgos["Puntaje Estratégico"],
                    textposition="auto"
                )
            ]
        )

        fig.update_layout(
            xaxis_title="Puntaje estratégico",
            yaxis_title="Riesgo",
            height=450
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# REGISTRO DE RIESGOS
# ============================================================

elif opcion == "📋 Registro de riesgos":

    st.header("📋 Registro consolidado de riesgos")

    if st.session_state.riesgos.empty:

        st.info(
            "No existen riesgos registrados actualmente."
        )

    else:

        st.dataframe(
            st.session_state.riesgos,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        csv = st.session_state.riesgos.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="⬇️ Descargar registro en CSV",
            data=csv,
            file_name="registro_riesgos_sgi.csv",
            mime="text/csv",
            use_container_width=True
        )

        if st.button(
            "🗑️ Limpiar todos los riesgos",
            use_container_width=True
        ):

            st.session_state.riesgos = pd.DataFrame(
                columns=[
                    "ID",
                    "Proceso",
                    "Tipo",
                    "Descripción",
                    "Causa",
                    "Consecuencia",
                    "Probabilidad",
                    "Impacto",
                    "Nivel de Riesgo",
                    "Clasificación",
                    "Impacto Estratégico",
                    "Puntaje Estratégico",
                    "Prioridad"
                ]
            )

            st.rerun()