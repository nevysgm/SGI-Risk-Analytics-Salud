import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from groq import Groq
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)
from reportlab.lib.units import cm


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="SGI Risk Analytics",
    page_icon="⚠️",
    layout="wide"
)


# ============================================================
# FUNCIONES DE RIESGO
# ============================================================

def calcular_nivel(probabilidad, impacto):
    return int(probabilidad) * int(impacto)


def clasificar_riesgo(probabilidad, impacto):
    """
    Clasificación basada en la matriz corporativa suministrada.

    Se mantiene la escala de valoración 1 a 5.

    La clasificación visual sigue la matriz:
    Verde      = Bajo
    Amarillo   = Moderado
    Naranja    = Alto
    Rojo       = Crítico
    Gris       = Muy bajo
    """

    p = int(probabilidad)
    i = int(impacto)

    # MUY BAJO - GRIS
    if p >= 4 and i == 1:
        return "Muy Bajo"

    # BAJO - VERDE
    if (p <= 3 and i == 1) or (p <= 2 and i <= 3):
        return "Bajo"

    # MODERADO - AMARILLO
    if (
        (p >= 3 and i == 2)
        or (p == 3 and i == 3)
        or (p <= 2 and i == 4)
        or (p == 1 and i == 5)
    ):
        return "Moderado"

    # ALTO - NARANJA
    if (
        (p >= 4 and i in [3, 4])
        or (p == 3 and i in [4, 5])
        or (p == 2 and i == 5)
    ):
        return "Alto"

    # CRÍTICO - ROJO
    if (
        (p >= 4 and i == 5)
    ):
        return "Crítico"

    return "Moderado"


def prioridad_riesgo(nivel, impacto_estrategico):
    """
    Priorización basada en nivel de riesgo e impacto estratégico.
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


def color_clasificacion(clasificacion):

    colores = {
        "Muy Bajo": "#E7E7E7",
        "Bajo": "#92D050",
        "Moderado": "#FFFF00",
        "Alto": "#ED7D31",
        "Crítico": "#E61919"
    }

    return colores.get(clasificacion, "#FFFFFF")


# ============================================================
# COLUMNAS ESTÁNDAR
# ============================================================

COLUMNAS = [
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


# ============================================================
# CREAR DATAFRAME VACÍO
# ============================================================

def dataframe_vacio():

    return pd.DataFrame(columns=COLUMNAS)


# ============================================================
# NORMALIZAR NOMBRES DE COLUMNAS DEL EXCEL
# ============================================================

def normalizar_nombre_columna(nombre):

    nombre = str(nombre).strip().lower()

    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n"
    }

    for original, nuevo in reemplazos.items():
        nombre = nombre.replace(original, nuevo)

    nombre = (
        nombre
        .replace(" ", "_")
        .replace("-", "_")
    )

    return nombre


def importar_excel(archivo):

    df = pd.read_excel(archivo)

    # Normalizar nombres
    columnas_originales = df.columns.tolist()

    df.columns = [
        normalizar_nombre_columna(col)
        for col in df.columns
    ]

    # Diccionario de equivalencias
    equivalencias = {

        "id": "ID",
        "codigo": "ID",
        "codigo_riesgo": "ID",
        "id_del_riesgo": "ID",

        "proceso": "Proceso",
        "proceso_asociado": "Proceso",

        "tipo": "Tipo",
        "tipo_de_riesgo": "Tipo",

        "descripcion": "Descripción",
        "descripcion_del_riesgo": "Descripción",
        "riesgo": "Descripción",

        "causa": "Causa",
        "causas": "Causa",

        "consecuencia": "Consecuencia",
        "consecuencias": "Consecuencia",

        "probabilidad": "Probabilidad",
        "prob": "Probabilidad",

        "impacto": "Impacto",

        "impacto_estrategico": "Impacto Estratégico",
        "impacto_estratégico": "Impacto Estratégico",
        "impacto_estrategico_1_5": "Impacto Estratégico"
    }

    nuevas_columnas = {}

    for columna in df.columns:

        if columna in equivalencias:
            nuevas_columnas[columna] = equivalencias[columna]

    df = df.rename(columns=nuevas_columnas)

    # --------------------------------------------------------
    # Validación
    # --------------------------------------------------------

    obligatorias = [
        "Probabilidad",
        "Impacto"
    ]

    faltantes = [
        col for col in obligatorias
        if col not in df.columns
    ]

    if faltantes:

        raise ValueError(
            "El Excel no contiene las columnas obligatorias: "
            + ", ".join(faltantes)
        )

    # --------------------------------------------------------
    # Crear columnas faltantes
    # --------------------------------------------------------

    columnas_texto = [
        "Proceso",
        "Tipo",
        "Descripción",
        "Causa",
        "Consecuencia"
    ]

    for columna in columnas_texto:

        if columna not in df.columns:
            df[columna] = ""

    if "ID" not in df.columns:
        df["ID"] = [
            f"R-{i:03d}"
            for i in range(1, len(df) + 1)
        ]

    if "Impacto Estratégico" not in df.columns:

        df["Impacto Estratégico"] = 3

    # --------------------------------------------------------
    # Convertir valores numéricos
    # --------------------------------------------------------

    df["Probabilidad"] = pd.to_numeric(
        df["Probabilidad"],
        errors="coerce"
    )

    df["Impacto"] = pd.to_numeric(
        df["Impacto"],
        errors="coerce"
    )

    df["Impacto Estratégico"] = pd.to_numeric(
        df["Impacto Estratégico"],
        errors="coerce"
    ).fillna(3)

    # --------------------------------------------------------
    # Validar escala 1 - 5
    # --------------------------------------------------------

    if (
        df["Probabilidad"].isna().any()
        or
        df["Impacto"].isna().any()
    ):

        raise ValueError(
            "Probabilidad e Impacto deben contener valores numéricos de 1 a 5."
        )

    if (
        (df["Probabilidad"] < 1).any()
        or
        (df["Probabilidad"] > 5).any()
        or
        (df["Impacto"] < 1).any()
        or
        (df["Impacto"] > 5).any()
        or
        (df["Impacto Estratégico"] < 1).any()
        or
        (df["Impacto Estratégico"] > 5).any()
    ):

        raise ValueError(
            "Los valores de Probabilidad, Impacto e Impacto Estratégico "
            "deben estar entre 1 y 5."
        )

    # --------------------------------------------------------
    # Calcular resultados
    # --------------------------------------------------------

    df["Probabilidad"] = df["Probabilidad"].astype(int)
    df["Impacto"] = df["Impacto"].astype(int)
    df["Impacto Estratégico"] = (
        df["Impacto Estratégico"].astype(int)
    )

    df["Nivel de Riesgo"] = df.apply(
        lambda fila: calcular_nivel(
            fila["Probabilidad"],
            fila["Impacto"]
        ),
        axis=1
    )

    df["Clasificación"] = df.apply(
        lambda fila: clasificar_riesgo(
            fila["Probabilidad"],
            fila["Impacto"]
        ),
        axis=1
    )

    df["Puntaje Estratégico"] = (
        df["Nivel de Riesgo"]
        *
        df["Impacto Estratégico"]
    )

    df["Prioridad"] = df.apply(
        lambda fila: prioridad_riesgo(
            fila["Nivel de Riesgo"],
            fila["Impacto Estratégico"]
        ),
        axis=1
    )

    return df[COLUMNAS]


# ============================================================
# GROQ AI
# ============================================================

def generar_informe_ia(df):

    try:

        api_key = st.secrets["GROQ_API_KEY"]

    except Exception:

        return (
            "ERROR: No se encontró GROQ_API_KEY. "
            "Configure la clave en los Secrets de Streamlit."
        )

    try:

        cliente = Groq(
            api_key=api_key
        )

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

        prompt = f"""
Actúa como consultor senior en gestión integral del riesgo.

Analiza el siguiente registro de riesgos corporativos:

{riesgos_texto}

La metodología utiliza:

Probabilidad: escala 1 a 5.
Impacto: escala 1 a 5.
Nivel de riesgo = Probabilidad × Impacto.
Impacto estratégico = escala 1 a 5.
Puntaje estratégico = Nivel de riesgo × Impacto estratégico.

NO debes modificar los valores calculados.

Genera un INFORME EJECUTIVO DE PRIORIZACIÓN Y TRATAMIENTO.

Estructura:

# 1. Resumen ejecutivo

Indica el estado general del perfil de riesgo.

# 2. Análisis del mapa de calor

Identifica las zonas donde existe mayor concentración de riesgos
y los riesgos ubicados en las posiciones de mayor exposición.

# 3. Riesgos prioritarios

Identifica los riesgos que requieren mayor atención.

Considera:
- Nivel de riesgo.
- Clasificación.
- Impacto estratégico.
- Puntaje estratégico.
- Consecuencias.

# 4. Prioridades de tratamiento

Organiza los riesgos en:

Prioridad 1 - Intervención inmediata.
Prioridad 2 - Tratamiento de corto plazo.
Prioridad 3 - Fortalecimiento y seguimiento.
Prioridad 4 - Monitoreo.

# 5. Recomendaciones de tratamiento

Propón acciones para:
- Evitar.
- Reducir.
- Controlar.
- Transferir.
- Aceptar.
- Monitorear.

No inventes controles existentes.

# 6. Impacto estratégico

Explica cómo los principales riesgos pueden afectar:
- objetivos institucionales,
- continuidad operativa,
- cumplimiento,
- recursos,
- reputación,
- calidad,
- seguridad.

# 7. Recomendaciones para la dirección

Máximo 5 recomendaciones ejecutivas.

# 8. Conclusión

Genera una conclusión ejecutiva breve.

REGLAS:

- No inventes riesgos.
- No inventes datos.
- No cambies las valoraciones.
- No cambies la clasificación.
- No modifiques el impacto estratégico.
- Diferencia datos de recomendaciones.
- Utiliza lenguaje ejecutivo.
- Enfoca el análisis en tratamiento y priorización.
"""

        respuesta = cliente.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un consultor senior en gestión integral "
                        "del riesgo y análisis de datos."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_completion_tokens=6000
        )

        return respuesta.choices[0].message.content

    except Exception as error:

        return (
            "No fue posible generar el informe con Groq AI.\n\n"
            f"Detalle técnico: {str(error)}"
        )


# ============================================================
# GENERACIÓN DE PDF
# ============================================================

def generar_pdf(informe, df):

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=1.3 * cm,
        leftMargin=1.3 * cm,
        topMargin=1.3 * cm,
        bottomMargin=1.3 * cm
    )

    estilos = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "Titulo",
        parent=estilos["Title"],
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=15
    )

    subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=estilos["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=8
    )

    texto = ParagraphStyle(
        "Texto",
        parent=estilos["BodyText"],
        fontSize=9,
        leading=13,
        spaceAfter=7
    )

    elementos = []

    # --------------------------------------------------------
    # Título
    # --------------------------------------------------------

    elementos.append(
        Paragraph(
            "SGI RISK ANALYTICS",
            titulo
        )
    )

    elementos.append(
        Paragraph(
            "Informe Ejecutivo de Priorización y Tratamiento de Riesgos",
            subtitulo
        )
    )

    elementos.append(
        Paragraph(
            "Sistema de Gestión Integrado del Riesgo",
            texto
        )
    )

    elementos.append(
        Spacer(1, 0.3 * cm)
    )

    # --------------------------------------------------------
    # Indicadores
    # --------------------------------------------------------

    total = len(df)

    criticos = len(
        df[df["Clasificación"] == "Crítico"]
    )

    prioridad_critica = len(
        df[df["Prioridad"] == "Crítica"]
    )

    estrategicos = len(
        df[df["Impacto Estratégico"] >= 4]
    )

    resumen = [
        ["Indicador", "Resultado"],
        ["Total de riesgos", str(total)],
        ["Riesgos críticos", str(criticos)],
        ["Prioridad crítica", str(prioridad_critica)],
        ["Impacto estratégico ≥ 4", str(estrategicos)]
    ]

    tabla_resumen = Table(
        resumen,
        colWidths=[7 * cm, 4 * cm]
    )

    tabla_resumen.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#0B3D91")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "ALIGN",
                (1, 0),
                (1, -1),
                "CENTER"
            )
        ])
    )

    elementos.append(
        tabla_resumen
    )

    elementos.append(
        Spacer(1, 0.5 * cm)
    )

    # --------------------------------------------------------
    # Informe IA
    # --------------------------------------------------------

    for linea in informe.split("\n"):

        linea = linea.strip()

        if not linea:
            continue

        if linea.startswith("# "):

            elementos.append(
                Paragraph(
                    linea.replace("# ", ""),
                    subtitulo
                )
            )

        elif linea.startswith("## "):

            elementos.append(
                Paragraph(
                    linea.replace("## ", ""),
                    subtitulo
                )
            )

        else:

            linea = (
                linea
                .replace("**", "")
                .replace("*", "")
            )

            elementos.append(
                Paragraph(
                    linea,
                    texto
                )
            )

    # --------------------------------------------------------
    # Tabla de riesgos
    # --------------------------------------------------------

    elementos.append(
        PageBreak()
    )

    elementos.append(
        Paragraph(
            "Ranking de riesgos prioritarios",
            subtitulo
        )
    )

    df_pdf = df.sort_values(
        "Puntaje Estratégico",
        ascending=False
    ).head(20)

    datos = [
        [
            "ID",
            "Proceso",
            "Prob.",
            "Impacto",
            "Nivel",
            "Clasificación",
            "Imp. Estrat.",
            "Puntaje",
            "Prioridad"
        ]
    ]

    for _, fila in df_pdf.iterrows():

        datos.append([
            str(fila["ID"]),
            str(fila["Proceso"])[:25],
            str(fila["Probabilidad"]),
            str(fila["Impacto"]),
            str(fila["Nivel de Riesgo"]),
            str(fila["Clasificación"]),
            str(fila["Impacto Estratégico"]),
            str(fila["Puntaje Estratégico"]),
            str(fila["Prioridad"])
        ])

    tabla_riesgos = Table(
        datos,
        repeatRows=1,
        colWidths=[
            1.5 * cm,
            4.5 * cm,
            1.2 * cm,
            1.2 * cm,
            1.3 * cm,
            3 * cm,
            2 * cm,
            2 * cm,
            2.2 * cm
        ]
    )

    estilo_tabla = [
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.HexColor("#0B3D91")
        ),
        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            colors.white
        ),
        (
            "FONTNAME",
            (0, 0),
            (-1, 0),
            "Helvetica-Bold"
        ),
        (
            "FONTSIZE",
            (0, 0),
            (-1, -1),
            7
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.4,
            colors.grey
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE"
        ),
        (
            "ALIGN",
            (2, 1),
            (-1, -1),
            "CENTER"
        )
    ]

    # Colorear clasificación
    for numero, (_, fila) in enumerate(
        df_pdf.iterrows(),
        start=1
    ):

        color = color_clasificacion(
            fila["Clasificación"]
        )

        estilo_tabla.append(
            (
                "BACKGROUND",
                (5, numero),
                (5, numero),
                colors.HexColor(color)
            )
        )

    tabla_riesgos.setStyle(
        TableStyle(estilo_tabla)
    )

    elementos.append(
        tabla_riesgos
    )

    elementos.append(
        Spacer(1, 0.5 * cm)
    )

    elementos.append(
        Paragraph(
            "Documento generado mediante SGI Risk Analytics con apoyo de inteligencia artificial.",
            texto
        )
    )

    documento.build(elementos)

    buffer.seek(0)

    return buffer


# ============================================================
# INICIALIZAR SESIÓN
# ============================================================

if "riesgos" not in st.session_state:

    st.session_state.riesgos = dataframe_vacio()


if "informe_ia" not in st.session_state:

    st.session_state.informe_ia = ""


if "estado_cargue" not in st.session_state:

    st.session_state.estado_cargue = ""

# ============================================================
# ENCABEZADO
# ============================================================

st.title("⚠️ SGI Risk Analytics")

st.subheader(
    "Sistema de Gestión Integrado del Riesgo"
)

st.markdown(
    """
    **Identificación → Evaluación → Análisis → Priorización → Tratamiento**
    
    Plataforma analítica para apoyar la gestión integral del riesgo
    mediante valoración 1–5, mapa de calor corporativo, impacto estratégico
    e inteligencia artificial.
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
        "📥 Importar riesgos Excel",
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

    df = st.session_state.riesgos

    total = len(df)

    if total > 0:

        criticos = len(
            df[df["Clasificación"] == "Crítico"]
        )

        altos = len(
            df[
                df["Clasificación"].isin(
                    ["Alto", "Crítico"]
                )
            ]
        )

        estrategicos = len(
            df[df["Impacto Estratégico"] >= 4]
        )

        prioridad_critica = len(
            df[df["Prioridad"] == "Crítica"]
        )

    else:

        criticos = 0
        altos = 0
        estrategicos = 0
        prioridad_critica = 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total de riesgos",
        total
    )

    col2.metric(
        "Alto / Crítico",
        altos
    )

    col3.metric(
        "Impacto estratégico alto",
        estrategicos
    )

    col4.metric(
        "Prioridad crítica",
        prioridad_critica
    )

    st.divider()

    st.markdown(
        """
        ### 🔄 Ciclo de gestión

        **1. Identificación**

        Registro estructurado del evento, causa y consecuencia.

        **2. Evaluación**

        Valoración de probabilidad e impacto de 1 a 5.

        **3. Análisis**

        Ubicación del riesgo en el mapa de calor corporativo.

        **4. Priorización**

        Integración del nivel de riesgo con el impacto estratégico.

        **5. Tratamiento**

        Generación de recomendaciones apoyadas por inteligencia artificial.
        """
    )


# ============================================================
# IMPORTAR EXCEL
# ============================================================

elif opcion == "📥 Importar riesgos Excel":

    st.header("📥 Importar riesgos desde Excel")

    if st.session_state.estado_cargue == "CARGADO":

        st.success(
            "📥 Estado del cargue: CARGADO"
        )

    st.markdown(
        """
        Cargue un archivo **.xlsx** con los riesgos previamente
        identificados.

        La aplicación calculará automáticamente:

        - Nivel de riesgo.
        - Clasificación.
        - Puntaje estratégico.
        - Prioridad.
        """
    )

    st.info(
        "Columnas mínimas: Probabilidad e Impacto. "
        "Se recomienda incluir también ID, Proceso, Tipo, "
        "Descripción, Causa, Consecuencia e Impacto Estratégico."
    )

    archivo = st.file_uploader(
        "Seleccione el archivo Excel",
        type=["xlsx", "xls"]
    )

    if archivo is not None:

        try:

            df_importado = importar_excel(
                archivo
            )

            st.success(
                f"Archivo cargado correctamente: "
                f"{len(df_importado)} riesgos."
            )

            st.subheader(
                "Vista previa"
            )

            st.dataframe(
                df_importado,
                use_container_width=True,
                hide_index=True
            )

            st.divider()

        except Exception as error:

            st.error(
                f"No fue posible importar el archivo: {error}"
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
                "Proceso asociado"
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

        st.subheader(
            "Valoración"
        )

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
                "Debe diligenciar el proceso y la descripción."
            )

        else:

            nivel = calcular_nivel(
                probabilidad,
                impacto
            )

            clasificacion = clasificar_riesgo(
                probabilidad,
                impacto
            )

            puntaje = (
                nivel
                *
                impacto_estrategico
            )

            prioridad = prioridad_riesgo(
                nivel,
                impacto_estrategico
            )

            nuevo_id = (
                f"R-{len(st.session_state.riesgos) + 1:03d}"
            )

            nuevo = pd.DataFrame(
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
                    "Puntaje Estratégico": puntaje,
                    "Prioridad": prioridad
                }]
            )

            st.session_state.riesgos = pd.concat(
                [
                    st.session_state.riesgos,
                    nuevo
                ],
                ignore_index=True
            )

            st.session_state.informe_ia = ""

            st.success(
                f"Riesgo {nuevo_id} registrado correctamente."
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Nivel",
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
# EVALUACIÓN
# ============================================================

elif opcion == "📊 Evaluación y análisis":

    st.header("📊 Evaluación y análisis")

    df = st.session_state.riesgos

    if df.empty:

        st.warning(
            "No existen riesgos registrados."
        )

    else:

        st.dataframe(
            df[
                [
                    "ID",
                    "Proceso",
                    "Probabilidad",
                    "Impacto",
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

        conteo = (
            df["Clasificación"]
            .value_counts()
        )

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
            title="Distribución de riesgos",
            xaxis_title="Clasificación",
            yaxis_title="Cantidad"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# MAPA DE CALOR CORPORATIVO
# ============================================================

elif opcion == "🔥 Mapa de calor":

    st.header("🔥 Mapa de calor corporativo")

    st.markdown(
        """
        La matriz utiliza **Probabilidad e Impacto**, ambos en escala
        de **1 a 5**, siguiendo la estructura visual suministrada.
        """
    )

    df = st.session_state.riesgos

    # --------------------------------------------------------
    # MATRIZ DE COLORES
    # --------------------------------------------------------

    # Filas: Probabilidad 5 → 1
    # Columnas: Impacto 1 → 5

    matriz_clases = [
        [
            "Muy Bajo",
            "Moderado",
            "Alto",
            "Alto",
            "Crítico"
        ],
        [
            "Muy Bajo",
            "Moderado",
            "Alto",
            "Alto",
            "Crítico"
        ],
        [
            "Bajo",
            "Moderado",
            "Moderado",
            "Alto",
            "Alto"
        ],
        [
            "Bajo",
            "Bajo",
            "Bajo",
            "Moderado",
            "Alto"
        ],
        [
            "Bajo",
            "Bajo",
            "Bajo",
            "Moderado",
            "Moderado"
        ]
    ]

    matriz_valores = []

    for fila in matriz_clases:

        valores = []

        for clase in fila:

            valores.append(
                {
                    "Muy Bajo": 1,
                    "Bajo": 2,
                    "Moderado": 3,
                    "Alto": 4,
                    "Crítico": 5
                }[clase]
            )

        matriz_valores.append(
            valores
        )

    # --------------------------------------------------------
    # TEXTOS DE CADA CELDA
    # --------------------------------------------------------

    matriz_texto = []

    probabilidades = [5, 4, 3, 2, 1]
    impactos = [1, 2, 3, 4, 5]

    for p, fila in zip(
        probabilidades,
        matriz_clases
    ):

        fila_texto = []

        for i, clase in zip(
            impactos,
            fila
        ):

            riesgos_celda = df[
                (
                    df["Probabilidad"] == p
                )
                &
                (
                    df["Impacto"] == i
                )
            ]

            ids = riesgos_celda[
                "ID"
            ].tolist()

            if ids:

                texto = (
                    f"{clase}<br>"
                    + "<br>".join(ids)
                )

            else:

                texto = clase

            fila_texto.append(
                texto
            )

        matriz_texto.append(
            fila_texto
        )

    # --------------------------------------------------------
    # COLORES DISCRETOS
    # --------------------------------------------------------

    colores = [
        [0.00, "#E7E7E7"],
        [0.199, "#E7E7E7"],

        [0.20, "#92D050"],
        [0.399, "#92D050"],

        [0.40, "#FFFF00"],
        [0.599, "#FFFF00"],

        [0.60, "#ED7D31"],
        [0.799, "#ED7D31"],

        [0.80, "#E61919"],
        [1.00, "#E61919"]
    ]

    fig = go.Figure(
        data=go.Heatmap(
            z=matriz_valores,
            x=impactos,
            y=probabilidades,
            text=matriz_texto,
            texttemplate="%{text}",
            textfont={
                "size": 11,
                "color": "black"
            },
            colorscale=colores,
            zmin=1,
            zmax=5,
            showscale=False,
            xgap=1,
            ygap=1,
            hovertemplate=(
                "Probabilidad: %{y}<br>"
                "Impacto: %{x}<br>"
                "<extra></extra>"
            )
        )
    )

    # --------------------------------------------------------
    # EJES
    # --------------------------------------------------------

    fig.update_xaxes(
        tickmode="array",
        tickvals=[1, 2, 3, 4, 5],
        ticktext=[
            "MUY BAJO (1)",
            "BAJO (2)",
            "MODERADO (3)",
            "ALTO (4)",
            "MUY ALTO (5)"
        ],
        title_text="IMPACTO",
        side="bottom"
    )

    fig.update_yaxes(
        tickmode="array",
        tickvals=[5, 4, 3, 2, 1],
        ticktext=[
            "MUY PROBABLE (5)",
            "PROBABLE (4)",
            "MEDIANAMENTE<br>PROBABLE (3)",
            "POCO PROBABLE (2)",
            "IMPROBABLE (1)"
        ],
        title_text="PROBABILIDAD",
        autorange="reversed"
    )

    fig.update_layout(
        title={
            "text": "MAPA DE CALOR",
            "x": 0.5,
            "xanchor": "center"
        },
        height=700,
        margin=dict(
            l=130,
            r=40,
            t=70,
            b=110
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # --------------------------------------------------------
    # LEYENDA
    # --------------------------------------------------------

    st.markdown(
        """
        ### Leyenda

        ⬜ **Muy Bajo** &nbsp;&nbsp;
        🟩 **Bajo** &nbsp;&nbsp;
        🟨 **Moderado** &nbsp;&nbsp;
        🟧 **Alto** &nbsp;&nbsp;
        🟥 **Crítico**
        """
    )

    if not df.empty:

        st.divider()

        st.subheader(
            "Riesgos ubicados en el mapa"
        )

        st.dataframe(
            df[
                [
                    "ID",
                    "Proceso",
                    "Probabilidad",
                    "Impacto",
                    "Nivel de Riesgo",
                    "Clasificación"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# PRIORIZACIÓN
# ============================================================

elif opcion == "🎯 Priorización":

    st.header(
        "🎯 Priorización estratégica"
    )

    df = st.session_state.riesgos

    if df.empty:

        st.warning(
            "No existen riesgos registrados."
        )

    else:

        df_priorizado = df.sort_values(
            "Puntaje Estratégico",
            ascending=False
        )

        st.markdown(
            """
            ### Criterio de priorización

            **Puntaje estratégico = Nivel de riesgo × Impacto estratégico**

            La priorización permite identificar aquellos riesgos que,
            además de presentar exposición en el mapa de calor, pueden
            comprometer objetivos estratégicos de la organización.
            """
        )

        st.dataframe(
            df_priorizado[
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

        top = df_priorizado.head(10)

        fig = go.Figure(
            data=[
                go.Bar(
                    x=top["Puntaje Estratégico"],
                    y=top["ID"],
                    orientation="h",
                    text=top["Puntaje Estratégico"],
                    textposition="auto"
                )
            ]
        )

        fig.update_layout(
            title="Top 10 riesgos por puntaje estratégico",
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

    st.header(
        "🤖 Informe ejecutivo de priorización y tratamiento"
    )

    df = st.session_state.riesgos

    if df.empty:

        st.warning(
            "Debe cargar o registrar riesgos antes de generar el informe."
        )

    else:

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Riesgos",
            len(df)
        )

        col2.metric(
            "Críticos",
            len(
                df[
                    df["Clasificación"]
                    == "Crítico"
                ]
            )
        )

        col3.metric(
            "Prioridad crítica",
            len(
                df[
                    df["Prioridad"]
                    == "Crítica"
                ]
            )
        )

        col4.metric(
            "Impacto estratégico alto",
            len(
                df[
                    df["Impacto Estratégico"]
                    >= 4
                ]
            )
        )

        st.divider()

        st.dataframe(
            df.sort_values(
                "Puntaje Estratégico",
                ascending=False
            )[
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
            "🤖 Generar informe con Groq AI",
            type="primary",
            use_container_width=True
        ):

            with st.spinner(
                "Analizando riesgos, mapa de calor e impacto estratégico..."
            ):

                informe = generar_informe_ia(
                    df.sort_values(
                        "Puntaje Estratégico",
                        ascending=False
                    )
                )

                st.session_state.informe_ia = informe

        if st.session_state.informe_ia:

            st.divider()

            st.subheader(
                "📄 Informe generado"
            )

            st.markdown(
                st.session_state.informe_ia
            )

            # ------------------------------------------------
            # PDF
            # ------------------------------------------------

            pdf = generar_pdf(
                st.session_state.informe_ia,
                df
            )

            st.download_button(
                label="📄 Descargar informe ejecutivo en PDF",
                data=pdf,
                file_name="Informe_Ejecutivo_SGI_Risk_Analytics.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

            # ------------------------------------------------
            # TXT
            # ------------------------------------------------

            st.download_button(
                label="⬇️ Descargar informe en TXT",
                data=st.session_state.informe_ia,
                file_name="Informe_Ejecutivo_SGI_Risk_Analytics.txt",
                mime="text/plain",
                use_container_width=True
            )


# ============================================================
# REGISTRO
# ============================================================

elif opcion == "📋 Registro de riesgos":

    st.header(
        "📋 Registro consolidado de riesgos"
    )

    df = st.session_state.riesgos

    if df.empty:

        st.info(
            "No existen riesgos registrados."
        )

    else:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        # CSV

        csv = (
            df.to_csv(
                index=False
            )
            .encode("utf-8")
        )

        st.download_button(
            label="⬇️ Descargar registro CSV",
            data=csv,
            file_name="registro_riesgos_sgi.csv",
            mime="text/csv",
            use_container_width=True
        )

        # Excel

        buffer_excel = BytesIO()

        with pd.ExcelWriter(
            buffer_excel,
            engine="openpyxl"
        ) as writer:

            df.to_excel(
                writer,
                index=False,
                sheet_name="Riesgos"
            )

        buffer_excel.seek(0)

        st.download_button(
            label="📊 Descargar registro Excel",
            data=buffer_excel,
            file_name="registro_riesgos_sgi.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True
        )

        st.divider()

        if st.button(
            "🗑️ Limpiar todos los riesgos",
            use_container_width=True
        ):

            st.session_state.riesgos = (
                dataframe_vacio()
            )

            st.session_state.informe_ia = ""

            st.rerun()