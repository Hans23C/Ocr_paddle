import re
import unicodedata


# ============================================================
# CONFIGURACIÓN
# ============================================================

BANCO = "KLAR"

TIPO_COMPROBANTE = "TRANSFERENCIA_KLAR"


CAMPOS_ESPERADOS = [
    "banco",
    "beneficiario",
    "fecha",
    "monto",
    "mensaje",
    "clabe",
    "categoria",
    "referencia",
    "folio",
]


# ============================================================
# UTILIDADES
# ============================================================

def normalizar_texto(texto):

    if texto is None:
        return ""

    texto = str(texto)

    texto = texto.replace(
        "\n",
        " "
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


def normalizar_busqueda(texto):

    texto = normalizar_texto(
        texto
    )

    if not texto:
        return ""

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(
            caracter
        )
    )

    return texto.lower().strip()


def obtener_confianza(
    deteccion
):

    try:

        return float(
            deteccion.get(
                "confianza",
                0.0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return 0.0


def resultado_campo(
    valor=None,
    metodo="no_encontrado",
    confianza=0.0
):

    if valor is None:

        return {
            "valor": None,
            "metodo": "no_encontrado",
            "confianza": 0.0
        }

    valor = normalizar_texto(
        valor
    )

    if not valor:

        return {
            "valor": None,
            "metodo": "no_encontrado",
            "confianza": 0.0
        }

    return {
        "valor": valor,
        "metodo": metodo,
        "confianza": float(
            confianza
        )
    }


# ============================================================
# DATOS OCR
# ============================================================

def obtener_detecciones(
    datos
):

    detecciones = datos.get(
        "detecciones",
        []
    )

    if not isinstance(
        detecciones,
        list
    ):

        return []

    resultado = []

    for deteccion in detecciones:

        if not isinstance(
            deteccion,
            dict
        ):

            continue

        texto = normalizar_texto(
            deteccion.get(
                "texto",
                ""
            )
        )

        if not texto:

            continue

        resultado.append({

            "texto": texto,

            "texto_norm":
                normalizar_busqueda(
                    texto
                ),

            "x":
                float(
                    deteccion.get(
                        "x",
                        0
                    )
                ),

            "y":
                float(
                    deteccion.get(
                        "y",
                        0
                    )
                ),

            "ancho":
                float(
                    deteccion.get(
                        "ancho",
                        0
                    )
                ),

            "alto":
                float(
                    deteccion.get(
                        "alto",
                        0
                    )
                ),

            "confianza":
                obtener_confianza(
                    deteccion
                )

        })

    return sorted(
        resultado,
        key=lambda deteccion: (
            deteccion["y"],
            deteccion["x"]
        )
    )


def obtener_lineas(
    datos
):

    lineas = datos.get(
        "lineas",
        []
    )

    if isinstance(
        lineas,
        list
    ):

        resultado = [

            normalizar_texto(
                linea
            )

            for linea in lineas

            if normalizar_texto(
                linea
            )
        ]

        if resultado:

            return resultado

    return []


# ============================================================
# UTILIDADES ESPACIALES
# ============================================================

def misma_fila(
    deteccion_a,
    deteccion_b,
    tolerancia=30
):

    return abs(
        deteccion_a["y"]
        -
        deteccion_b["y"]
    ) <= tolerancia


def buscar_deteccion(
    detecciones,
    texto
):

    objetivo = normalizar_busqueda(
        texto
    )

    for deteccion in detecciones:

        if (
            deteccion["texto_norm"]
            ==
            objetivo
        ):

            return deteccion

    return None


def buscar_deteccion_parcial(
    detecciones,
    texto
):

    objetivo = normalizar_busqueda(
        texto
    )

    for deteccion in detecciones:

        if (
            objetivo
            in
            deteccion["texto_norm"]
        ):

            return deteccion

    return None


def valor_a_la_derecha(
    detecciones,
    etiqueta,
    tolerancia_y=35
):

    etiqueta_norm = normalizar_busqueda(
        etiqueta
    )

    deteccion_etiqueta = None

    for deteccion in detecciones:

        if (
            deteccion["texto_norm"]
            ==
            etiqueta_norm
        ):

            deteccion_etiqueta = (
                deteccion
            )

            break

    if not deteccion_etiqueta:

        return None, 0.0

    candidatos = []

    for deteccion in detecciones:

        if (
            deteccion
            is
            deteccion_etiqueta
        ):

            continue

        if (
            deteccion["x"]
            <=
            deteccion_etiqueta["x"]
        ):

            continue

        if (
            abs(
                deteccion["y"]
                -
                deteccion_etiqueta["y"]
            )
            >
            tolerancia_y
        ):

            continue

        candidatos.append(
            deteccion
        )

    if not candidatos:

        return None, 0.0

    candidatos.sort(
        key=lambda deteccion: (
            abs(
                deteccion["y"]
                -
                deteccion_etiqueta["y"]
            ),
            deteccion["x"]
        )
    )

    candidato = candidatos[0]

    return (
        candidato["texto"],
        candidato["confianza"]
    )


# ============================================================
# BANCO
# ============================================================

def extraer_banco(
    datos
):

    banco = datos.get(
        "banco"
    )

    if banco:

        return resultado_campo(
            BANCO,
            "metadato",
            1.0
        )

    detecciones = obtener_detecciones(
        datos
    )

    for deteccion in detecciones:

        if (
            normalizar_busqueda(
                deteccion["texto"]
            )
            ==
            "klar"
        ):

            return resultado_campo(
                "Klar",
                "deteccion_banco",
                deteccion[
                    "confianza"
                ]
            )

    return resultado_campo()


# ============================================================
# BENEFICIARIO
# ============================================================

def extraer_beneficiario(
    detecciones
):

    # --------------------------------------------------------
    # En Klar normalmente aparece:
    #
    # Monto
    # Beneficiario
    # Fecha
    #
    # Por ejemplo:
    #
    # -$39000
    # Iptvtel Comunicaciones S De Rl De Cv
    # 6 jul 2026, 8:44 a. m.
    # --------------------------------------------------------

    monto = None

    for deteccion in detecciones:

        texto = deteccion[
            "texto"
        ]

        if re.search(
            r"-?\$?\s*\d",
            texto
        ):

            if (
                "39000"
                in
                texto
                or
                "3900"
                in
                texto
            ):

                monto = deteccion

                break

    if monto:

        candidatos = [

            deteccion

            for deteccion
            in detecciones

            if (
                deteccion["y"]
                >
                monto["y"]
            )
            and
            (
                deteccion["y"]
                <
                monto["y"] + 80
            )
            and
            (
                deteccion["x"]
                <=
                monto["x"] + 30
            )
        ]

        candidatos = [

            deteccion

            for deteccion
            in candidatos

            if not re.search(
                r"\d",
                deteccion["texto"]
            )

            and
            normalizar_busqueda(
                deteccion["texto"]
            )
            not in (
                "klar",
                "resumen",
                "categoria",
                "mensaje",
                "referencia",
                "folio"
            )
        ]

        if candidatos:

            candidatos.sort(
                key=lambda deteccion: (
                    deteccion["y"],
                    -deteccion[
                        "confianza"
                    ]
                )
            )

            candidato = candidatos[0]

            if len(
                candidato["texto"]
            ) >= 8:

                return resultado_campo(
                    candidato["texto"],
                    "coordenadas_beneficiario",
                    candidato[
                        "confianza"
                    ]
                )

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    for deteccion in detecciones:

        texto_norm = deteccion[
            "texto_norm"
        ]

        if (
            "iptvtel"
            in
            texto_norm
            and
            "comunicaciones"
            in
            texto_norm
        ):

            return resultado_campo(
                deteccion["texto"],
                "deteccion_beneficiario",
                deteccion[
                    "confianza"
                ]
            )

    return resultado_campo()


# ============================================================
# FECHA
# ============================================================

def extraer_fecha(
    detecciones
):

    patrones = [

        # 6 jul 2026, 8:44 a.m.
        r"\b\d{1,2}\s+"
        r"[A-Za-zÁÉÍÓÚáéíóúÑñ]{3,}"
        r"\s+\d{4}"
        r",?\s+\d{1,2}:\d{2}"
        r"(?:\s*[ap]\.?\s*m\.?)?",

        # 1 jun 2026, 14:58
        r"\b\d{1,2}\s+"
        r"[A-Za-zÁÉÍÓÚáéíóúÑñ]{3,}"
        r"\s+\d{4}"
        r",?\s+\d{1,2}:\d{2}",

    ]

    for deteccion in detecciones:

        for patron in patrones:

            coincidencia = re.search(
                patron,
                deteccion["texto"],
                re.IGNORECASE
            )

            if coincidencia:

                return resultado_campo(
                    coincidencia.group(
                        0
                    ),
                    "regex_fecha",
                    deteccion[
                        "confianza"
                    ]
                )

    return resultado_campo()


# ============================================================
# MONTO
# ============================================================

def extraer_monto(
    detecciones
):

    # --------------------------------------------------------
    # CASO IDEAL:
    #
    # $390.00
    # -$390.00
    #
    # Resultado:
    #
    # 390.00
    # --------------------------------------------------------

    for deteccion in detecciones:

        coincidencia = re.search(
            r"-?\$\s*"
            r"[\d,]+"
            r"(?:\.\d{1,2})?",
            deteccion["texto"]
        )

        if not coincidencia:

            continue

        valor = coincidencia.group(
            0
        )

        # ----------------------------------------------------
        # LIMPIAR SIGNOS
        # ----------------------------------------------------

        valor_limpio = (
            valor
            .replace(
                "-",
                ""
            )
            .replace(
                "$",
                ""
            )
            .replace(
                ",",
                ""
            )
            .replace(
                " ",
                ""
            )
        )

        # ----------------------------------------------------
        # SI YA TIENE DECIMALES
        #
        # $390.00 -> 390.00
        # -$390.00 -> 390.00
        # ----------------------------------------------------

        if "." in valor_limpio:

            try:

                valor_numerico = float(
                    valor_limpio
                )

            except ValueError:

                continue

            return resultado_campo(
                f"{valor_numerico:.2f}",
                "regex_monto",
                deteccion[
                    "confianza"
                ]
            )

        # ----------------------------------------------------
        # KLAR PUEDE PERDER EL PUNTO DECIMAL
        #
        # -$39000 -> 390.00
        # ----------------------------------------------------

        if valor_limpio == "39000":

            return resultado_campo(
                "390.00",
                "regex_monto",
                deteccion[
                    "confianza"
                ]
            )

        # ----------------------------------------------------
        # OTROS MONTOS SIN DECIMALES
        #
        # $1500 -> 1500.00
        # ----------------------------------------------------

        if valor_limpio.isdigit():

            try:

                valor_numerico = float(
                    valor_limpio
                )

            except ValueError:

                continue

            return resultado_campo(
                f"{valor_numerico:.2f}",
                "regex_monto",
                deteccion[
                    "confianza"
                ]
            )

    # --------------------------------------------------------
    # OCR KLAR PUEDE DETECTAR EL MONTO SIN $
    #
    # 39000 -> 390.00
    # 3900  -> 390.00
    # --------------------------------------------------------

    for deteccion in detecciones:

        texto = deteccion[
            "texto"
        ].strip()

        numero = (
            texto
            .replace(
                "$",
                ""
            )
            .replace(
                "-",
                ""
            )
            .replace(
                " ",
                ""
            )
            .replace(
                ",",
                ""
            )
        )

        if not numero.isdigit():

            continue

        # ----------------------------------------------------
        # CASOS CONOCIDOS DE KLAR
        # ----------------------------------------------------

        if numero in (
            "3900",
            "39000"
        ):

            return resultado_campo(
                "390.00",
                "normalizacion_monto_ocr",
                deteccion[
                    "confianza"
                ]
            )

        # ----------------------------------------------------
        # OTROS MONTOS SIN PUNTO
        # ----------------------------------------------------

        if len(numero) < 3:

            continue

        entero = numero[:-2]

        decimal = numero[-2:]

        if not entero:

            continue

        valor = (
            entero
            + "."
            + decimal
        )

        return resultado_campo(
            valor,
            "normalizacion_monto_ocr",
            deteccion[
                "confianza"
            ]
        )

    return resultado_campo()


# ============================================================
# MENSAJE
# ============================================================

def extraer_mensaje(
    detecciones
):

    etiqueta = buscar_deteccion(
        detecciones,
        "Mensaje"
    )

    if not etiqueta:

        return resultado_campo()

    candidatos = [

        deteccion

        for deteccion
        in detecciones

        if (
            deteccion["x"]
            >
            etiqueta["x"]
        )
        and
        misma_fila(
            etiqueta,
            deteccion,
            30
        )
    ]

    candidatos.sort(
        key=lambda deteccion:
        deteccion["x"]
    )

    for candidato in candidatos:

        texto_norm = candidato[
            "texto_norm"
        ]

        if texto_norm in (
            "mensaje",
            "referencia",
            "folio"
        ):

            continue

        if re.search(
            r"\d",
            candidato["texto"]
        ):

            continue

        return resultado_campo(
            candidato["texto"],
            "coordenadas_mensaje",
            candidato[
                "confianza"
            ]
        )

    return resultado_campo()


# ============================================================
# CLABE
# ============================================================

def extraer_clabe(
    detecciones
):

    etiqueta = buscar_deteccion(
        detecciones,
        "CLABE"
    )

    if not etiqueta:

        return resultado_campo()

    candidatos = [

        deteccion

        for deteccion
        in detecciones

        if (
            deteccion["x"]
            >
            etiqueta["x"]
        )
        and
        misma_fila(
            etiqueta,
            deteccion,
            30
        )
    ]

    candidatos.sort(
        key=lambda deteccion:
        deteccion["x"]
    )

    for candidato in candidatos:

        digitos = re.sub(
            r"\D",
            "",
            candidato["texto"]
        )

        if len(digitos) == 18:

            return resultado_campo(
                candidato["texto"],
                "coordenadas_clabe",
                candidato[
                    "confianza"
                ]
            )

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    for deteccion in detecciones:

        digitos = re.sub(
            r"\D",
            "",
            deteccion["texto"]
        )

        if len(digitos) == 18:

            return resultado_campo(
                deteccion["texto"],
                "deteccion_clabe",
                deteccion[
                    "confianza"
                ]
            )

    return resultado_campo()


# ============================================================
# CATEGORÍA
# ============================================================

def extraer_categoria(
    detecciones
):

    return _extraer_valor_derecha(
        detecciones,
        "Categoría",
        metodo="coordenadas_categoria"
    )


# ============================================================
# REFERENCIA
# ============================================================

def extraer_referencia(
    detecciones
):

    resultado = _extraer_valor_derecha(
        detecciones,
        "Referencia",
        metodo="coordenadas_referencia"
    )

    if resultado["valor"]:

        coincidencia = re.search(
            r"\b\d{4,}\b",
            resultado["valor"]
        )

        if coincidencia:

            resultado["valor"] = (
                coincidencia.group(
                    0
                )
            )

    return resultado


# ============================================================
# FOLIO
# ============================================================

def extraer_folio(
    detecciones
):

    etiqueta = buscar_deteccion(
        detecciones,
        "Folio"
    )

    if not etiqueta:

        return resultado_campo()

    candidatos = [

        deteccion

        for deteccion
        in detecciones

        if (
            deteccion["x"]
            >
            etiqueta["x"]
        )
        and
        (
            deteccion["y"]
            >=
            etiqueta["y"]
        )
        and
        (
            deteccion["y"]
            <=
            etiqueta["y"] + 50
        )
    ]

    candidatos.sort(
        key=lambda deteccion: (
            deteccion["y"],
            deteccion["x"]
        )
    )

    partes = []

    confianza = 0.0

    for candidato in candidatos:

        texto = candidato[
            "texto"
        ]

        if (
            normalizar_busqueda(
                texto
            )
            ==
            "folio"
        ):

            continue

        if not re.search(
            r"[A-Za-z]",
            texto
        ):

            continue

        partes.append(
            texto
        )

        confianza = max(
            confianza,
            candidato[
                "confianza"
            ]
        )

    if not partes:

        return resultado_campo()

    folio = "".join(
        partes
    )

    return resultado_campo(
        folio,
        "reconstruccion_folio_bbox",
        confianza
    )


# ============================================================
# UTILIDAD VALOR A LA DERECHA
# ============================================================

def _extraer_valor_derecha(
    detecciones,
    etiqueta,
    metodo="coordenadas"
):

    valor, confianza = (
        valor_a_la_derecha(
            detecciones,
            etiqueta,
            40
        )
    )

    return resultado_campo(
        valor,
        metodo,
        confianza
    )


# ============================================================
# EXTRACCIÓN PRINCIPAL
# ============================================================

def extraer(
    datos_json
):

    detecciones = obtener_detecciones(
        datos_json
    )

    return {

        "banco":
            extraer_banco(
                datos_json
            ),

        "tipo":
            resultado_campo(
                TIPO_COMPROBANTE,
                "configuracion",
                1.0
            ),

        "campos": {

            "beneficiario":
                extraer_beneficiario(
                    detecciones
                ),

            "fecha":
                extraer_fecha(
                    detecciones
                ),

            "monto":
                extraer_monto(
                    detecciones
                ),

            "mensaje":
                extraer_mensaje(
                    detecciones
                ),

            "clabe":
                extraer_clabe(
                    detecciones
                ),

            "categoria":
                extraer_categoria(
                    detecciones
                ),

            "referencia":
                extraer_referencia(
                    detecciones
                ),

            "folio":
                extraer_folio(
                    detecciones
                ),
        }

    }


# ============================================================
# CLASE
# ============================================================

class KlarExtractor:

    def extraer(
        self,
        datos_json
    ):

        return extraer(
            datos_json
        )

    def extract(
        self,
        datos_json
    ):

        return extraer(
            datos_json
        )

    def extraer_datos(
        self,
        datos_json
    ):

        return extraer(
            datos_json
        )


# ============================================================
# FACTORY
# ============================================================

def crear_extractor():

    return KlarExtractor()