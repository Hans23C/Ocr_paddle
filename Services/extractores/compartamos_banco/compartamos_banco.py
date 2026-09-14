import re


# ============================================================
# CONSTANTES
# ============================================================

BANCO = "Compartamos Banco"
TIPO = "TRANSFERENCIA_COMPARTAMOS_BANCO"


# ============================================================
# UTILIDADES
# ============================================================

def obtener_detecciones(datos):

    return datos.get(
        "detecciones",
        []
    )


def normalizar_texto(texto):

    if texto is None:
        return ""

    texto = str(texto)

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


def confianza(deteccion):

    try:

        return float(
            deteccion.get(
                "confianza",
                0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return 0.0


def crear_campo(
    valor,
    metodo,
    conf
):

    return {

        "valor": valor,

        "metodo": metodo,

        "confianza":
            round(
                float(conf),
                4
            )
    }


def buscar_etiqueta(
    detecciones,
    patron
):

    expresion = re.compile(
        patron,
        re.IGNORECASE
    )

    for i, deteccion in enumerate(
        detecciones
    ):

        texto = normalizar_texto(
            deteccion.get(
                "texto",
                ""
            )
        )

        if expresion.search(texto):

            return i, deteccion

    return None, None


# ============================================================
# BANCO
# ============================================================

def extraer_banco(
    datos
):

    detecciones = obtener_detecciones(
        datos
    )

    # --------------------------------------------------------
    # Buscar "Compartamos"
    # --------------------------------------------------------

    for deteccion in detecciones:

        texto = normalizar_texto(
            deteccion.get(
                "texto",
                ""
            )
        )

        if re.fullmatch(
            r"Compartamos",
            texto,
            re.IGNORECASE
        ):

            return crear_campo(
                BANCO,
                "OCR_DIRECTO",
                confianza(
                    deteccion
                )
            )

    # --------------------------------------------------------
    # Respaldo
    # --------------------------------------------------------

    for deteccion in detecciones:

        texto = normalizar_texto(
            deteccion.get(
                "texto",
                ""
            )
        )

        if "compartamos" in texto.lower():

            return crear_campo(
                BANCO,
                "OCR_DIRECTO",
                confianza(
                    deteccion
                )
            )

    return crear_campo(
        BANCO,
        "METADATO",
        1.0
    )


# ============================================================
# BANCO DESTINO
# ============================================================

def extraer_destino(
    datos
):

    detecciones = obtener_detecciones(
        datos
    )

    indice, etiqueta = buscar_etiqueta(
        detecciones,
        r"^Banco\s+destino\s*:?\s*$"
    )

    if indice is None:

        return crear_campo(
            None,
            "NO_ENCONTRADO",
            0.0
        )

    x_etiqueta = float(
        etiqueta.get(
            "x",
            0
        )
    )

    y_etiqueta = float(
        etiqueta.get(
            "y",
            0
        )
    )

    candidatos = []

    # --------------------------------------------------------
    # Buscar HSBC a la derecha
    # --------------------------------------------------------

    for deteccion in detecciones:

        texto = normalizar_texto(
            deteccion.get(
                "texto",
                ""
            )
        )

        if not re.fullmatch(
            r"HSBC",
            texto,
            re.IGNORECASE
        ):

            continue

        x = float(
            deteccion.get(
                "x",
                0
            )
        )

        y = float(
            deteccion.get(
                "y",
                0
            )
        )

        if x <= x_etiqueta:

            continue

        if abs(
            y - y_etiqueta
        ) > 35:

            continue

        candidatos.append(
            deteccion
        )

    if candidatos:

        candidatos.sort(
            key=lambda d:
            abs(
                float(
                    d.get(
                        "y",
                        0
                    )
                )
                - y_etiqueta
            )
        )

        seleccionado = candidatos[0]

        return crear_campo(
            "HSBC",
            "BBOX_DERECHA",
            confianza(
                seleccionado
            )
        )

    return crear_campo(
        None,
        "NO_ENCONTRADO",
        0.0
    )


# ============================================================
# BENEFICIARIO
# ============================================================

def extraer_beneficiario(
    datos
):

    detecciones = obtener_detecciones(
        datos
    )

    indice, etiqueta = buscar_etiqueta(
        detecciones,
        r"^Alias\s*/\s*Nombre\s*:?\s*$"
    )

    if indice is None:

        return crear_campo(
            None,
            "NO_ENCONTRADO",
            0.0
        )

    x_etiqueta = float(
        etiqueta.get(
            "x",
            0
        )
    )

    y_etiqueta = float(
        etiqueta.get(
            "y",
            0
        )
    )

    candidatos = []

    # --------------------------------------------------------
    # Buscar a la derecha de Alias / Nombre
    # --------------------------------------------------------

    for deteccion in detecciones:

        if deteccion is etiqueta:

            continue

        texto = normalizar_texto(
            deteccion.get(
                "texto",
                ""
            )
        )

        if not texto:

            continue

        x = float(
            deteccion.get(
                "x",
                0
            )
        )

        y = float(
            deteccion.get(
                "y",
                0
            )
        )

        # ----------------------------------------------------
        # Debe estar a la derecha de la etiqueta
        # ----------------------------------------------------

        if x <= x_etiqueta:

            continue

        # ----------------------------------------------------
        # El beneficiario comienza en la misma zona vertical
        # o debajo de la etiqueta.
        # ----------------------------------------------------

        if y < y_etiqueta:

            continue

        if y - y_etiqueta > 100:

            continue

        # ----------------------------------------------------
        # No tomar montos como parte del beneficiario
        # ----------------------------------------------------

        if re.fullmatch(
            r"\$\s*[\d,]+(?:\.\d{2})?",
            texto
        ):

            continue

        # ----------------------------------------------------
        # Evitar etiquetas de campos posteriores
        # ----------------------------------------------------

        if re.search(
            r"^(Monto|Concepto|Referencia|Clave\s+de\s+rastreo|Fecha\s+y\s+hora)\s*:?",
            texto,
            re.IGNORECASE
        ):

            continue

        candidatos.append(
            deteccion
        )

    if not candidatos:

        return crear_campo(
            None,
            "NO_ENCONTRADO",
            0.0
        )

    # --------------------------------------------------------
    # Ordenar por posición vertical
    # --------------------------------------------------------

    candidatos.sort(
        key=lambda d: (
            float(
                d.get(
                    "y",
                    0
                )
            ),
            float(
                d.get(
                    "x",
                    0
                )
            )
        )
    )

    partes = []

    confianzas = []

    ultimo_y = None

    for deteccion in candidatos:

        texto = normalizar_texto(
            deteccion.get(
                "texto",
                ""
            )
        )

        if not texto:

            continue

        y = float(
            deteccion.get(
                "y",
                0
            )
        )

        # ----------------------------------------------------
        # Primera detección
        # ----------------------------------------------------

        if ultimo_y is None:

            partes.append(
                texto
            )

            confianzas.append(
                confianza(
                    deteccion
                )
            )

            ultimo_y = y

            continue

        # ----------------------------------------------------
        # Continuación del beneficiario
        # ----------------------------------------------------

        if y - ultimo_y > 55:

            break

        partes.append(
            texto
        )

        confianzas.append(
            confianza(
                deteccion
            )
        )

        ultimo_y = y

    if not partes:

        return crear_campo(
            None,
            "NO_ENCONTRADO",
            0.0
        )

    valor = " ".join(
        partes
    )

    valor = normalizar_texto(
        valor
    )

    return crear_campo(
        valor,
        "BBOX_DERECHA_MULTILINEA",
        min(
            confianzas
        )
    )


# ============================================================
# MONTO
# ============================================================

def extraer_monto(
    datos
):

    detecciones = obtener_detecciones(
        datos
    )

    patron = re.compile(
        r"^\$\s*[\d,]+(?:\.\d{2})?$"
    )

    for deteccion in detecciones:

        texto = normalizar_texto(
            deteccion.get(
                "texto",
                ""
            )
        )

        if patron.fullmatch(
            texto
        ):

            return crear_campo(
                texto,
                "OCR_DIRECTO",
                confianza(
                    deteccion
                )
            )

    return crear_campo(
        None,
        "NO_ENCONTRADO",
        0.0
    )


# ============================================================
# CONCEPTO
# ============================================================

def extraer_concepto(
    datos
):

    detecciones = obtener_detecciones(
        datos
    )

    indice, etiqueta = buscar_etiqueta(
        detecciones,
        r"^Concepto\s*:?\s*$"
    )

    if indice is None:

        return crear_campo(
            None,
            "NO_ENCONTRADO",
            0.0
        )

    x_etiqueta = float(
        etiqueta.get(
            "x",
            0
        )
    )

    y_etiqueta = float(
        etiqueta.get(
            "y",
            0
        )
    )

    candidatos = []

    # --------------------------------------------------------
    # Buscar valor a la derecha
    # --------------------------------------------------------

    for deteccion in detecciones:

        texto = normalizar_texto(
            deteccion.get(
                "texto",
                ""
            )
        )

        if not texto:

            continue

        x = float(
            deteccion.get(
                "x",
                0
            )
        )

        y = float(
            deteccion.get(
                "y",
                0
            )
        )

        if x <= x_etiqueta:

            continue

        # ----------------------------------------------------
        # Tolerancia vertical
        # ----------------------------------------------------

        diferencia_y = y - y_etiqueta

        if diferencia_y < -25:

            continue

        if diferencia_y > 45:

            continue

        # ----------------------------------------------------
        # Evitar etiquetas posteriores
        # ----------------------------------------------------

        if re.search(
            r"^(Referencia|Clave\s+de\s+rastreo|Fecha\s+y\s+hora|Monto|Concepto)\s*:?",
            texto,
            re.IGNORECASE
        ):

            continue

        candidatos.append(
            deteccion
        )

    if candidatos:

        candidatos.sort(
            key=lambda d:
            abs(
                float(
                    d.get(
                        "y",
                        0
                    )
                )
                - y_etiqueta
            )
        )

        seleccionado = candidatos[0]

        return crear_campo(
            normalizar_texto(
                seleccionado.get(
                    "texto",
                    ""
                )
            ),
            "BBOX_DERECHA",
            confianza(
                seleccionado
            )
        )

    return crear_campo(
        None,
        "NO_ENCONTRADO",
        0.0
    )


# ============================================================
# REFERENCIA
# ============================================================

def extraer_referencia(
    datos
):

    detecciones = obtener_detecciones(
        datos
    )

    indice, etiqueta = buscar_etiqueta(
        detecciones,
        r"^Referencia\s*:?\s*$"
    )

    if indice is None:

        return crear_campo(
            None,
            "NO_ENCONTRADO",
            0.0
        )

    x_etiqueta = float(
        etiqueta.get(
            "x",
            0
        )
    )

    y_etiqueta = float(
        etiqueta.get(
            "y",
            0
        )
    )

    candidatos = []

    # --------------------------------------------------------
    # Buscar referencia numérica a la derecha
    # --------------------------------------------------------

    for deteccion in detecciones:

        texto = normalizar_texto(
            deteccion.get(
                "texto",
                ""
            )
        )

        if not re.fullmatch(
            r"\d+",
            texto
        ):

            continue

        x = float(
            deteccion.get(
                "x",
                0
            )
        )

        y = float(
            deteccion.get(
                "y",
                0
            )
        )

        if x <= x_etiqueta:

            continue

        diferencia_y = y - y_etiqueta

        if diferencia_y < -25:

            continue

        if diferencia_y > 45:

            continue

        candidatos.append(
            deteccion
        )

    if candidatos:

        candidatos.sort(
            key=lambda d:
            abs(
                float(
                    d.get(
                        "y",
                        0
                    )
                )
                - y_etiqueta
            )
        )

        seleccionado = candidatos[0]

        return crear_campo(
            normalizar_texto(
                seleccionado.get(
                    "texto",
                    ""
                )
            ),
            "BBOX_DERECHA",
            confianza(
                seleccionado
            )
        )

    return crear_campo(
        None,
        "NO_ENCONTRADO",
        0.0
    )


# ============================================================
# CLAVE DE RASTREO
# ============================================================

def extraer_clave_rastreo(
    datos
):

    detecciones = obtener_detecciones(
        datos
    )

    indice, etiqueta = buscar_etiqueta(
        detecciones,
        r"^Clave\s+de\s+rastreo\s*:?\s*$"
    )

    if indice is None:

        return crear_campo(
            None,
            "NO_ENCONTRADO",
            0.0
        )

    x_etiqueta = float(
        etiqueta.get(
            "x",
            0
        )
    )

    y_etiqueta = float(
        etiqueta.get(
            "y",
            0
        )
    )

    candidatos = []

    # --------------------------------------------------------
    # Buscar fragmentos posteriores
    # --------------------------------------------------------

    for deteccion in detecciones:

        texto = normalizar_texto(
            deteccion.get(
                "texto",
                ""
            )
        )

        if not re.fullmatch(
            r"[A-Za-z0-9]+",
            texto
        ):

            continue

        x = float(
            deteccion.get(
                "x",
                0
            )
        )

        y = float(
            deteccion.get(
                "y",
                0
            )
        )

        if y < y_etiqueta:

            continue

        if y - y_etiqueta > 70:

            continue

        if x <= x_etiqueta:

            continue

        candidatos.append(
            deteccion
        )

    if not candidatos:

        return crear_campo(
            None,
            "NO_ENCONTRADO",
            0.0
        )

    # --------------------------------------------------------
    # Ordenar por posición
    # --------------------------------------------------------

    candidatos.sort(
        key=lambda d: (
            float(
                d.get(
                    "y",
                    0
                )
            ),
            float(
                d.get(
                    "x",
                    0
                )
            )
        )
    )

    partes = []

    confianzas = []

    ultimo_y = None

    for deteccion in candidatos:

        texto = normalizar_texto(
            deteccion.get(
                "texto",
                ""
            )
        )

        y = float(
            deteccion.get(
                "y",
                0
            )
        )

        if ultimo_y is None:

            partes.append(
                texto
            )

            confianzas.append(
                confianza(
                    deteccion
                )
            )

            ultimo_y = y

            continue

        if y - ultimo_y <= 45:

            partes.append(
                texto
            )

            confianzas.append(
                confianza(
                    deteccion
                )
            )

            ultimo_y = y

        else:

            break

    if not partes:

        return crear_campo(
            None,
            "NO_ENCONTRADO",
            0.0
        )

    valor = "".join(
        partes
    )

    return crear_campo(
        valor,
        "BBOX_DERECHA_MULTILINEA",
        min(
            confianzas
        )
    )


# ============================================================
# FECHA
# ============================================================

def extraer_fecha(
    datos
):

    detecciones = obtener_detecciones(
        datos
    )

    # --------------------------------------------------------
    # IMPORTANTE:
    #
    # Compartamos puede entregar:
    #
    # 03/07/2026 09:17:55
    #
    # o:
    #
    # 03/07/202609:17:55
    #
    # Por eso se permite \s* entre fecha y hora.
    # --------------------------------------------------------

    patron = re.compile(
        r"\b"
        r"(\d{1,2}/\d{1,2}/\d{4})"
        r"\s*"
        r"(\d{1,2}:\d{2}:\d{2})"
        r"\b"
    )

    # --------------------------------------------------------
    # Buscar directamente
    # --------------------------------------------------------

    for deteccion in detecciones:

        texto = normalizar_texto(
            deteccion.get(
                "texto",
                ""
            )
        )

        encontrado = patron.search(
            texto
        )

        if encontrado:

            fecha = encontrado.group(
                1
            )

            hora = encontrado.group(
                2
            )

            valor = (
                f"{fecha} {hora}"
            )

            return crear_campo(
                valor,
                "OCR_DIRECTO",
                confianza(
                    deteccion
                )
            )

    # --------------------------------------------------------
    # Respaldo:
    #
    # Fecha y hora:
    # 03/07/202609:17:55
    #
    # o:
    #
    # Fecha y hora:
    # 03/07/2026 09:17:55
    # --------------------------------------------------------

    indice, etiqueta = buscar_etiqueta(
        detecciones,
        r"^Fecha\s+y\s+hora\s*:?\s*$"
    )

    if indice is not None:

        y_etiqueta = float(
            etiqueta.get(
                "y",
                0
            )
        )

        x_etiqueta = float(
            etiqueta.get(
                "x",
                0
            )
        )

        candidatos = []

        for deteccion in detecciones:

            texto = normalizar_texto(
                deteccion.get(
                    "texto",
                    ""
                )
            )

            encontrado = patron.search(
                texto
            )

            if not encontrado:

                continue

            x = float(
                deteccion.get(
                    "x",
                    0
                )
            )

            y = float(
                deteccion.get(
                    "y",
                    0
                )
            )

            if x <= x_etiqueta:

                continue

            if abs(
                y - y_etiqueta
            ) > 45:

                continue

            candidatos.append(
                deteccion
            )

        if candidatos:

            # ------------------------------------------------
            # Seleccionar el más cercano verticalmente
            # ------------------------------------------------

            candidatos.sort(
                key=lambda d:
                abs(
                    float(
                        d.get(
                            "y",
                            0
                        )
                    )
                    - y_etiqueta
                )
            )

            seleccionado = candidatos[0]

            texto = normalizar_texto(
                seleccionado.get(
                    "texto",
                    ""
                )
            )

            encontrado = patron.search(
                texto
            )

            fecha = encontrado.group(
                1
            )

            hora = encontrado.group(
                2
            )

            valor = (
                f"{fecha} {hora}"
            )

            return crear_campo(
                valor,
                "BBOX_DERECHA",
                confianza(
                    seleccionado
                )
            )

    return crear_campo(
        None,
        "NO_ENCONTRADO",
        0.0
    )


# ============================================================
# EXTRACTOR PRINCIPAL
# ============================================================

class CompartamosBancoExtractor:

    def __init__(self):

        self.banco = BANCO

        self.tipo = TIPO

    def extraer(
        self,
        datos
    ):

        return {

            "banco":
                self.banco,

            "tipo":
                self.tipo,

            "campos": {

                "banco":
                    extraer_banco(
                        datos
                    ),

                "destino":
                    extraer_destino(
                        datos
                    ),

                "beneficiario":
                    extraer_beneficiario(
                        datos
                    ),

                "monto":
                    extraer_monto(
                        datos
                    ),

                "concepto":
                    extraer_concepto(
                        datos
                    ),

                "referencia":
                    extraer_referencia(
                        datos
                    ),

                "clave_rastreo":
                    extraer_clave_rastreo(
                        datos
                    ),

                "fecha":
                    extraer_fecha(
                        datos
                    )
            }
        }

    def extract(
        self,
        datos
    ):

        return self.extraer(
            datos
        )

    def extraer_datos(
        self,
        datos
    ):

        return self.extraer(
            datos
        )


# ============================================================
# FACTORY
# ============================================================

def crear_extractor():

    return CompartamosBancoExtractor()


# ============================================================
# FUNCIÓN PÚBLICA
# ============================================================

def extraer(
    datos
):

    extractor = CompartamosBancoExtractor()

    return extractor.extraer(
        datos
    )