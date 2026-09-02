import re
import unicodedata


# ============================================================
# CONFIGURACIÓN
# ============================================================

BANCO = "REVOLUT"

CAMPOS = [
    "banco",
    "fecha",
    "titular",
    "clabe_spei",
    "codigo_swift",
    "clabe_swift",
    "identificacion",
    "banco_beneficiario",
    "monto",
    "beneficiario",
    "clabe_beneficiario",
    "concepto",
]


# ============================================================
# UTILIDADES
# ============================================================

def normalizar_texto(texto):

    if texto is None:
        return ""

    texto = str(texto)
    texto = texto.replace("\n", " ")
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def normalizar_busqueda(texto):

    texto = normalizar_texto(texto)

    if not texto:
        return ""

    # Reparar mojibake si aparece
    if any(x in texto for x in ("Ã", "Â", "â")):

        try:
            texto = (
                texto
                .encode("latin1")
                .decode("utf-8")
            )

        except (
            UnicodeEncodeError,
            UnicodeDecodeError
        ):
            pass

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    return texto.lower().strip()


def campo_encontrado(
    valor,
    metodo="OCR_DIRECTO",
    confianza=1.0
):

    valor = normalizar_texto(valor)

    if not valor:

        return campo_no_encontrado()

    return {

        "valor": valor,

        "metodo": metodo,

        "confianza": confianza,

    }


def campo_no_encontrado():

    return {

        "valor": "NO ENCONTRADO",

        "metodo": "NO ENCONTRADO",

        "confianza": 0.0,

    }


# ============================================================
# OBTENER DETECCIONES
# ============================================================

def obtener_detecciones(datos):

    if not isinstance(datos, dict):

        return []

    detecciones = datos.get(
        "detecciones",
        []
    )

    resultado = []

    if isinstance(
        detecciones,
        list
    ):

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

            bbox = deteccion.get(
                "bbox",
                []
            )

            x = deteccion.get(
                "x",
                0.0
            )

            y = deteccion.get(
                "y",
                0.0
            )

            ancho = deteccion.get(
                "ancho",
                0.0
            )

            alto = deteccion.get(
                "alto",
                0.0
            )

            confianza = deteccion.get(
                "confianza",
                0.0
            )

            resultado.append({

                "texto": texto,

                "texto_norm":
                    normalizar_busqueda(
                        texto
                    ),

                "x": x,

                "y": y,

                "ancho": ancho,

                "alto": alto,

                "confianza": confianza,

                "bbox": bbox,

            })

    return resultado


# ============================================================
# OBTENER LÍNEAS
# ============================================================

def obtener_lineas(datos):

    if not isinstance(
        datos,
        dict
    ):
        return []

    lineas = datos.get(
        "lineas",
        []
    )

    resultado = []

    if isinstance(
        lineas,
        list
    ):

        for linea in lineas:

            texto = normalizar_texto(
                linea
            )

            if texto:

                resultado.append(
                    texto
                )

    if resultado:

        return resultado

    detecciones = obtener_detecciones(
        datos
    )

    return [
        d["texto"]
        for d in detecciones
    ]


# ============================================================
# BÚSQUEDA POR ETIQUETA
# ============================================================

def buscar_por_etiqueta(
    detecciones,
    etiquetas,
    max_dy=25
):

    etiquetas_norm = [

        normalizar_busqueda(
            etiqueta
        )

        for etiqueta in etiquetas

    ]

    for etiqueta in detecciones:

        texto_norm = etiqueta[
            "texto_norm"
        ]

        for etiqueta_norm in etiquetas_norm:

            if texto_norm == etiqueta_norm:

                candidatos = [

                    d

                    for d in detecciones

                    if (

                        d["x"]
                        > etiqueta["x"]

                        and

                        abs(
                            d["y"]
                            - etiqueta["y"]
                        )
                        <= max_dy

                    )
                ]

                candidatos.sort(
                    key=lambda d: (
                        abs(
                            d["y"]
                            - etiqueta["y"]
                        ),
                        d["x"]
                    )
                )

                for candidato in candidatos:

                    if (
                        candidato["texto_norm"]
                        in etiquetas_norm
                    ):
                        continue

                    return candidato

    return None


# ============================================================
# BANCO
# ============================================================

def extraer_banco(
    detecciones
):

    for d in detecciones:

        if (
            d["texto_norm"]
            == "revolut"
        ):

            return (
                "REVOLUT",
                d["confianza"]
            )

    return (
        BANCO,
        1.0
    )


# ============================================================
# FECHA
# ============================================================

def extraer_fecha(
    detecciones
):

    patron = (
        r"\b\d{1,2}\s+"
        r"[A-Za-zÁÉÍÓÚáéíóúÑñ]+"
        r"\s+\d{4}\b"
    )

    # --------------------------------------------------------
    # Primero buscar la fecha de la transacción.
    # --------------------------------------------------------

    for d in detecciones:

        if (
            d["texto_norm"]
            == "fecha"
        ):

            candidatos = [

                x

                for x in detecciones

                if (

                    x["x"]
                    >= d["x"]

                    and

                    x["y"]
                    >= d["y"] - 10

                    and

                    x["y"]
                    <= d["y"] + 50

                )
            ]

            candidatos.sort(
                key=lambda x: (
                    abs(
                        x["y"]
                        - d["y"]
                    ),
                    x["x"]
                )
            )

            for candidato in candidatos:

                match = re.search(
                    patron,
                    candidato["texto"],
                    re.IGNORECASE
                )

                if match:

                    return (
                        match.group(0),
                        candidato["confianza"]
                    )

    # --------------------------------------------------------
    # Fallback general.
    # --------------------------------------------------------

    for d in detecciones:

        match = re.search(
            patron,
            d["texto"],
            re.IGNORECASE
        )

        if match:

            # Evitar "Generado el..."
            if (
                "generado"
                in d["texto_norm"]
            ):
                continue

            return (
                match.group(0),
                d["confianza"]
            )

    return (
        None,
        0.0
    )


# ============================================================
# TITULAR
# ============================================================

def extraer_titular(
    detecciones
):

    # En el comprobante el titular aparece
    # antes de "CLABE para SPEI".

    for d in detecciones:

        texto = d["texto"]

        if (
            "CLABE para SPEI"
            in texto
        ):

            # No se utiliza esta detección directamente
            # porque el titular está en otra detección.
            pass

    # Buscar texto que tenga apariencia de nombre
    # y que esté en la zona superior izquierda.

    candidatos = [

        d

        for d in detecciones

        if (

            d["x"] < 400

            and

            180 <= d["y"] <= 250

            and

            not re.search(
                r"\d",
                d["texto"]
            )

            and

            d["texto_norm"]
            not in (
                "revolut",
                "transaccion",
            )

        )
    ]

    if candidatos:

        candidato = min(
            candidatos,
            key=lambda d: d["y"]
        )

        return (
            candidato["texto"],
            candidato["confianza"]
        )

    return (
        None,
        0.0
    )


# ============================================================
# CLABE SPEI
# ============================================================

def extraer_clabe_spei(
    detecciones
):

    for d in detecciones:

        if (
            "clabe para spei"
            in d["texto_norm"]
        ):

            match = re.search(
                r"\b\d{18}\b",
                d["texto"]
            )

            if match:

                return (
                    match.group(0),
                    d["confianza"]
                )

            candidato = buscar_por_etiqueta(
                detecciones,
                ["CLABE para SPEI"],
                20
            )

            if candidato:

                match = re.search(
                    r"\b\d{18}\b",
                    candidato["texto"]
                )

                if match:

                    return (
                        match.group(0),
                        candidato["confianza"]
                    )

    return (
        None,
        0.0
    )


# ============================================================
# CÓDIGO SWIFT
# ============================================================

def extraer_codigo_swift(
    detecciones
):

    for d in detecciones:

        if (
            d["texto_norm"]
            == "codigo swift"
        ):

            candidato = buscar_por_etiqueta(
                detecciones,
                ["Código SWIFT"],
                20
            )

            if candidato:

                match = re.search(
                    r"\b[A-Z0-9]{8,11}\b",
                    candidato["texto"],
                    re.IGNORECASE
                )

                if match:

                    return (
                        match.group(0),
                        candidato["confianza"]
                    )

    # Fallback
    for d in detecciones:

        match = re.search(
            r"\b[A-Z]{6}[A-Z0-9]{2,5}\b",
            d["texto"],
            re.IGNORECASE
        )

        if match:

            return (
                match.group(0),
                d["confianza"]
            )

    return (
        None,
        0.0
    )


# ============================================================
# CLABE SWIFT
# ============================================================

def extraer_clabe_swift(
    detecciones
):

    for d in detecciones:

        if (
            "clabe para swift"
            in d["texto_norm"]
        ):

            match = re.search(
                r"\b\d{18}\b",
                d["texto"]
            )

            if match:

                return (
                    match.group(0),
                    d["confianza"]
                )

    return (
        None,
        0.0
    )


# ============================================================
# IDENTIFICACIÓN
# ============================================================

def extraer_identificacion(
    detecciones
):

    for d in detecciones:

        if (
            "identificacion:"
            in d["texto_norm"]
        ):

            match = re.search(
                r"[0-9a-fA-F]{8}"
                r"-[0-9a-fA-F]{4}"
                r"-[0-9a-fA-F]{4}"
                r"-[0-9a-fA-F]{4}"
                r"-[0-9a-fA-F]{12}",
                d["texto"]
            )

            if match:

                return (
                    match.group(0),
                    d["confianza"]
                )

    return (
        None,
        0.0
    )


# ============================================================
# BANCO BENEFICIARIO
# ============================================================



# ============================================================
# MONTO
# ============================================================

def extraer_monto(
    detecciones
):

    # Prioridad: detección asociada a
    # "Dinero saliente".

    for d in detecciones:

        if (
            d["texto_norm"]
            == "dinero saliente"
        ):

            candidatos = [

                x

                for x in detecciones

                if (

                    x["x"]
                    >= d["x"]

                    and

                    x["y"]
                    > d["y"]

                    and

                    x["y"]
                    <= d["y"] + 60

                )
            ]

            candidatos.sort(
                key=lambda x: (
                    abs(
                        x["y"]
                        - d["y"]
                    ),
                    x["x"]
                )
            )

            for candidato in candidatos:

                match = re.search(
                    r"\$\s*[\d,]+"
                    r"(?:\.\d{1,2})?",
                    candidato["texto"]
                )

                if match:

                    return (
                        match.group(0),
                        candidato["confianza"]
                    )

    # Fallback general.

    for d in detecciones:

        match = re.search(
            r"\$\s*[\d,]+"
            r"(?:\.\d{1,2})?",
            d["texto"]
        )

        if match:

            return (
                match.group(0),
                d["confianza"]
            )

    return (
        None,
        0.0
    )


# ============================================================
# BENEFICIARIO Y CLABE
# ============================================================

def extraer_beneficiario(
    detecciones
):

    for d in detecciones:

        texto_norm = d[
            "texto_norm"
        ]

        if (
            texto_norm.startswith(
                "a iptvtel"
            )
            or
            texto_norm.startswith(
                "a "
            )
        ):

            texto = d["texto"]

            match = re.search(
                r"^A\s+(.+?),\s*(\d{18})\s*$",
                texto,
                re.IGNORECASE
            )

            if match:

                return (

                    match.group(1).strip(),

                    match.group(2),

                    d["confianza"]

                )

    # Fallback: cualquier detección
    # que contenga una CLABE de 18 dígitos.

    for d in detecciones:

        match = re.search(
            r"^A\s+(.+?),\s*(\d{18})\s*$",
            d["texto"],
            re.IGNORECASE
        )

        if match:

            return (

                match.group(1).strip(),

                match.group(2),

                d["confianza"]

            )

    return (
        None,
        None,
        0.0
    )


# ============================================================
# CONCEPTO
# ============================================================

def extraer_concepto(
    detecciones
):

    for d in detecciones:

        if (
            d["texto_norm"]
            .startswith(
                "concepto:"
            )
        ):

            texto = d["texto"]

            match = re.search(
                r"Concepto\s*:\s*(.+)",
                texto,
                re.IGNORECASE
            )

            if match:

                return (
                    match.group(1).strip(),
                    d["confianza"]
                )

    return (
        None,
        0.0
    )


# ============================================================
# EXTRACCIÓN COMPLETA
# ============================================================

def extraer_revolut(
    detecciones
):

    banco, conf_banco = (
        extraer_banco(
            detecciones
        )
    )

    fecha, conf_fecha = (
        extraer_fecha(
            detecciones
        )
    )

    titular, conf_titular = (
        extraer_titular(
            detecciones
        )
    )

    clabe_spei, conf_clabe_spei = (
        extraer_clabe_spei(
            detecciones
        )
    )

    codigo_swift, conf_swift = (
        extraer_codigo_swift(
            detecciones
        )
    )

    clabe_swift, conf_clabe_swift = (
        extraer_clabe_swift(
            detecciones
        )
    )

    identificacion, conf_identificacion = (
        extraer_identificacion(
            detecciones
        )
    )


    monto, conf_monto = (
        extraer_monto(
            detecciones
        )
    )

    beneficiario, clabe_beneficiario, conf_beneficiario = (
        extraer_beneficiario(
            detecciones
        )
    )

    concepto, conf_concepto = (
        extraer_concepto(
            detecciones
        )
    )

    return {

        "banco":
            campo_encontrado(
                banco,
                "OCR_DIRECTO",
                conf_banco
            ),

        "fecha":
            campo_encontrado(
                fecha,
                "REGEX_FECHA",
                conf_fecha
            ),

        "titular":
            campo_encontrado(
                titular,
                "BBOX_DIRECTO",
                conf_titular
            ),

        "clabe_spei":
            campo_encontrado(
                clabe_spei,
                "REGEX_CLABE",
                conf_clabe_spei
            ),

        "codigo_swift":
            campo_encontrado(
                codigo_swift,
                "BBOX_DERECHA",
                conf_swift
            ),

        "clabe_swift":
            campo_encontrado(
                clabe_swift,
                "REGEX_CLABE",
                conf_clabe_swift
            ),

        "identificacion":
            campo_encontrado(
                identificacion,
                "REGEX_UUID",
                conf_identificacion
            ),

        "monto":
            campo_encontrado(
                monto,
                "BBOX_DERECHA",
                conf_monto
            ),

        "beneficiario":
            campo_encontrado(
                beneficiario,
                "REGEX_DESCRIPCION",
                conf_beneficiario
            ),

        "clabe_beneficiario":
            campo_encontrado(
                clabe_beneficiario,
                "REGEX_CLABE",
                conf_beneficiario
            ),

        "concepto":
            campo_encontrado(
                concepto,
                "BBOX_DIRECTO",
                conf_concepto
            ),

    }


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def extraer(
    datos_json
):

    detecciones = obtener_detecciones(
        datos_json
    )

    return {

        "banco":
            BANCO,

        "tipo":
            "TRANSFERENCIA_SPEI_REVOLUT",

        "campos":
            extraer_revolut(
                detecciones
            )

    }


# ============================================================
# COMPATIBILIDAD
# ============================================================

class RevolutExtractor:

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

    return RevolutExtractor()