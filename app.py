import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from groq import Groq

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="SGI Risk Analytics",
    page_icon="⚠️",
    layout="wide"
)

# ============================================================
# FUNCIONES DE RIESGO
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
    puntaje = nivel * impacto_estrategico

    if puntaje >= 80:
        return "Crítica"
    elif puntaje >= 50:
        return "Alta"
    elif puntaje >= 25:
        return "Media"
    else:
        return "Baja"


# ============================================================
# FUNCIÓN GROQ AI
# ============================================================

def generar_informe_ia(df):

    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        return (
            "ERROR: No se encontró GROQ_API_KEY.\n\n"
            "Configure la clave en .streamlit/secrets.toml "
            "o en los Secrets de Streamlit Community Cloud."
        )

    try:

        cliente = Groq(api_key=api_key)

        # ----------------------------------------------------
        # Preparar información para la IA
        # ----------------------------------------------------

        riesgos_texto = ""

        for _, riesgo in df.iterrows():

            riesgos_texto += f"""
ID: {riesgo['ID']}
Proceso: {riesgo['Proceso']}
Tipo: {riesgo['Tipo']}
Descripción: {riesgo['Descripción']}
Causa: {riesgo['Causa']}
Consecuencia: {riesgo['Consecuencia']}
Probabilidad: {riesgo['Probabilidad']}/5
Impacto: {riesgo['Impacto']}/5
Nivel de riesgo: {riesgo['Nivel de Riesgo']}
Clasificación: {riesgo['Clasificación']}
Impacto estratégico: {riesgo['Impacto Estratégico']}/5
Puntaje estratégico: {riesgo['Puntaje Estratégico']}
Prioridad: {riesgo['Prioridad']}
--------------------------------------------------
"""

        # ----------------------------------------------------
        # Prompt profesional
        # ----------------------------------------------------

        prompt = f"""
Actúa como un consultor senior especializado en gestión integral
del riesgo y sistemas de gestión organizacional.

Estás analizando los resultados de una matriz corporativa de riesgos.

La metodología utilizada por la herramienta es:

- Probabilidad: escala de 1 a 5.
- Impacto: escala de 1 a 5.
- Nivel de riesgo = Probabilidad × Impacto.
- Impacto estratégico: escala de 1 a 5.
- Puntaje estratégico = Nivel de riesgo × Impacto estratégico.

Tu función NO es modificar ni recalcular los valores proporcionados.
Debes interpretar los resultados y generar recomendaciones para
la toma de decisiones.

A continuación se encuentran los riesgos registrados:

{riesgos_texto}

Genera un INFORME EJECUTIVO DE PRIORIZACIÓN Y TRATAMIENTO DE RIESGOS.

El informe debe estar estructurado de la siguiente manera:

# 1. Resumen ejecutivo

Explica brevemente el estado general del perfil de riesgo.

Indica:
- cantidad total de riesgos,
- principales niveles de exposición,
- presencia de riesgos críticos,
- presencia de riesgos con alto impacto estratégico.

# 2. Lectura del mapa de calor

Interpreta la distribución de los riesgos considerando:

- probabilidad,
- impacto,
- concentración de riesgos,
- zonas de mayor exposición.

Identifica los riesgos ubicados en las zonas de mayor criticidad.

# 3. Riesgos prioritarios

Identifica los riesgos que deberían recibir atención prioritaria.

Considera especialmente:

- Nivel de riesgo.
- Clasificación.
- Impacto estratégico.
- Puntaje estratégico.
- Consecuencias potenciales.

Presenta una tabla conceptual con:

Riesgo | Proceso | Nivel | Impacto estratégico | Prioridad | Justificación

# 4. Prioridades de tratamiento

Propón un orden de atención:

PRIORIDAD 1:
Riesgos que requieren intervención inmediata.

PRIORIDAD 2:
Riesgos que requieren tratamiento de corto plazo.

PRIORIDAD 3:
Riesgos que requieren seguimiento y fortalecimiento de controles.

PRIORIDAD 4:
Riesgos que pueden mantenerse bajo monitoreo.

# 5. Recomendaciones de tratamiento

Para los riesgos de mayor prioridad propone acciones concretas.

Las recomendaciones deben orientarse a:

- evitar,
- reducir,
- controlar,
- transferir,
- aceptar,
- monitorear,

según corresponda.

No inventes controles existentes. Si no existe información suficiente,
indica que se requiere validación por parte del responsable del proceso.

# 6. Impacto estratégico

Explica cómo los riesgos con impacto estratégico alto pueden afectar:

- objetivos institucionales,
- continuidad operativa,
- cumplimiento,
- recursos financieros,
- reputación,
- calidad del servicio,
- seguridad,
- desempeño organizacional.

# 7. Recomendaciones para la dirección

Entrega máximo 5 recomendaciones ejecutivas.

Deben ser concretas, accionables y orientadas a la toma de decisiones.

# 8. Conclusión ejecutiva

Finaliza con una conclusión breve sobre el nivel general de exposición
y las acciones que deberían priorizarse.

IMPORTANTE:

1. No cambies los valores de probabilidad.
2. No cambies los valores de impacto.
3. No cambies la clasificación calculada.
4. No cambies el impacto estratégico.
5. No inventes riesgos.
6. No inventes datos.
7. Diferencia claramente entre datos calculados y recomendaciones.
8. Utiliza lenguaje profesional y ejecutivo.
9. Enfoca el análisis en la gestión y tratamiento del riesgo.
10. El informe debe ser comprensible para líderes de procesos y alta dirección.
"""

        # ----------------------------------------------------
        # Consulta a Groq
        # ----------------------------------------------------

        respuesta = cliente.chat.completions.create(
            #model="llama-3.3-70b-versatile",
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un consultor senior en gestión integral "
                        "del riesgo. Generas análisis ejecutivos claros, "
                        "estructurados y orientados a la toma de decisiones."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=6000
        )

        return respuesta.choices[0].message.content

    except Exception as e:

        return f"""
### Error al consultar Groq AI

No fue posible generar el informe.

Detalle técnico:

{str(e)}

Verifique:

1. Que la API Key de Groq sea válida.
2. Que GROQ_API_KEY esté correctamente configurada.
3. Que la aplicación tenga acceso a Internet.
4. Que el modelo utilizado esté disponible.
"""


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
    Herramienta analítica para apoyar la gestión integral del riesgo
    mediante valoración cuantitativa, mapa de calor corporativo,
    análisis estratégico e inteligencia artificial.
    """
)

st.divider()


# ============================================================
# MENÚ
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
        "🤖 Informe IA",
        "📋 Registro de riesgos"
    ]
)


# ============================================================
# INICIO
# ============================================================

if opcion == "🏠 Inicio":

    st.header("Gestión Integral del Riesgo")

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

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total de riesgos",
        total_riesgos
    )

    col2.metric(
        "Riesgos altos o superiores",
        altos
    )

    col3.metric(
        "Riesgos críticos",
        criticos
    )

    col4.metric(
        "Impacto estratégico alto",
        estrategicos
    )

    st.divider()

    st.markdown(
        """
        ### 🔄 Ciclo de gestión del riesgo

        **Identificación → Evaluación → Análisis → Priorización → Tratamiento**

        La herramienta transforma los datos de riesgo en información
        útil para apoyar la toma de decisiones.
        """
    )

    st.info(
        "La valoración utiliza una escala de 1 a 5 para probabilidad, "
        "impacto e impacto estratégico."
    )


# ============================================================
# IDENTIFICAR RIESGO
# ============================================================

elif opcion == "➕ Identificar riesgo":

    st.header("➕ Identificación y valoración del riesgo")

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
                "Descripción del riesgo"
            )

        with col2:

            causa = st.text_area(
                "Causa"
            )

            consecuencia = st.text_area(
                "Consecuencia"
            )

        st.subheader("Valoración")

        col1, col2, col3 = st.columns(3)

        with col1:

            probabilidad = st.slider(
                "Probabilidad",
                1,
                5,
                3
            )

        with col2:

            impacto = st.slider(
                "Impacto",
                1,
                5,
                3
            )

        with col3:

            impacto_estrategico = st.slider(
                "Impacto estratégico",
                1,
                5,
                3
            )

        enviar = st.form_submit_button(
            "💾 Registrar riesgo",
            use_container_width=True
        )

    if enviar:

        if not proceso or not descripcion:

            st.error(
                "Debe diligenciar como mínimo el proceso y la descripción."
            )

        else:

            nivel = probabilidad * impacto

            clasificacion = clasificar_riesgo(
                nivel
            )

            puntaje_estrategico = (
                nivel * impacto_estrategico
            )

            prioridad = prioridad_riesgo(
                nivel,
                impacto_estrategico
            )

            nuevo_id = (
                f"R-{len(st.session_state.riesgos) + 1:03d}"
            )

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
            "Aún no existen riesgos registrados."
        )

    else:

        df = st.session_state.riesgos.copy()

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
            yaxis_title="Número de riesgos"
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
        "Ubicación de los riesgos según probabilidad e impacto."
    )

    matriz_texto = []

    for impacto in range(5, 0, -1):

        fila = []

        for probabilidad in range(1, 6):

            nivel = probabilidad * impacto

            riesgos_celda = st.session_state.riesgos[
                (
                    st.session_state.riesgos["Probabilidad"]
                    == probabilidad
                )
                &
                (
                    st.session_state.riesgos["Impacto"]
                    == impacto
                )
            ]

            ids = riesgos_celda["ID"].tolist()

            if ids:

                texto = (
                    f"{nivel}<br>"
                    + ", ".join(ids)
                )

            else:

                texto = str(nivel)

            fila.append(texto)

        matriz_texto.append(fila)

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
            text=matriz_texto,
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

    st.info(
        "Los códigos R-XXX representan los riesgos registrados "
        "en cada posición del mapa."
    )


# ============================================================
# PRIORIZACIÓN
# ============================================================

elif opcion == "🎯 Priorización":

    st.header("🎯 Priorización estratégica")

    st.markdown(
        """
        **Puntaje estratégico = Nivel de riesgo × Impacto estratégico**

        Esta combinación permite identificar riesgos que requieren
        atención prioritaria desde una perspectiva operativa y estratégica.
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

        st.subheader(
            "Top de riesgos prioritarios"
        )

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
            yaxis_title="Riesgo"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# INFORME IA
# ============================================================

elif opcion == "🤖 Informe IA":

    st.header("🤖 Informe ejecutivo de riesgos con IA")

    st.markdown(
        """
        La inteligencia artificial analiza los riesgos registrados,
        su ubicación en el mapa de calor, el nivel de exposición y
        el impacto estratégico para generar recomendaciones de
        priorización y tratamiento.
        """
    )

    if st.session_state.riesgos.empty:

        st.warning(
            "Debe registrar al menos un riesgo antes de generar el informe."
        )

    else:

        df = st.session_state.riesgos.copy()

        # ----------------------------------------------------
        # Resumen previo
        # ----------------------------------------------------

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Riesgos registrados",
            len(df)
        )

        col2.metric(
            "Riesgos críticos",
            len(df[df["Clasificación"] == "Crítico"])
        )

        col3.metric(
            "Prioridad crítica",
            len(df[df["Prioridad"] == "Crítica"])
        )

        col4.metric(
            "Impacto estratégico ≥ 4",
            len(df[df["Impacto Estratégico"] >= 4])
        )

        st.divider()

        st.subheader(
            "Riesgos que serán analizados"
        )

        df_ordenado = df.sort_values(
            by="Puntaje Estratégico",
            ascending=False
        )

        st.dataframe(
            df_ordenado[
                [
                    "ID",
                    "Proceso",
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

        if st.button(
            "🤖 Generar informe ejecutivo con Groq AI",
            type="primary",
            use_container_width=True
        ):

            with st.spinner(
                "La IA está analizando el mapa de calor y priorizando los riesgos..."
            ):

                informe = generar_informe_ia(
                    df_ordenado
                )

            st.session_state.informe_ia = informe

        if "informe_ia" in st.session_state:

            st.divider()

            st.subheader(
                "📄 Informe ejecutivo"
            )

            st.markdown(
                st.session_state.informe_ia
            )

            st.divider()

            st.download_button(
                label="⬇️ Descargar informe TXT",
                data=st.session_state.informe_ia,
                file_name="informe_ejecutivo_riesgos_IA.txt",
                mime="text/plain",
                use_container_width=True
            )


# ============================================================
# REGISTRO
# ============================================================

elif opcion == "📋 Registro de riesgos":

    st.header("📋 Registro consolidado de riesgos")

    if st.session_state.riesgos.empty:

        st.info(
            "No existen riesgos registrados."
        )

    else:

        st.dataframe(
            st.session_state.riesgos,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        csv = (
            st.session_state.riesgos
            .to_csv(index=False)
            .encode("utf-8")
        )

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

            if "informe_ia" in st.session_state:
                del st.session_state.informe_ia

            st.rerun()