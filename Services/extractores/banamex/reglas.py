import re


# ============================================================
# NORMALIZACIÓN
# ============================================================

def normalizar(texto):
    """
    Normaliza texto para facilitar las comparaciones.
    """

    texto = str(texto).lower().strip()

    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
    }

    for original, nuevo in reemplazos.items():

        texto = texto.replace(
            original,
            nuevo
        )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto


# ============================================================
# DETECTAR BANCANET
# ============================================================

def es_bancanet(texto):
    """
    Determina si el comprobante corresponde
    a una operación BancaNet de Banamex.
    """

    texto = normalizar(
        texto
    )

    indicadores = 0

    if "pago interbancario" in texto:
        indicadores += 1

    if "cuenta de retiro" in texto:
        indicadores += 1

    if "cuenta de deposito" in texto:
        indicadores += 1

    if "clave de rastreo" in texto:
        indicadores += 1

    if "tipo de persona" in texto:
        indicadores += 1

    return indicadores >= 2


# ============================================================
# AUTORIZACIÓN
# ============================================================

def extraer_autorizacion(texto):

    texto = normalizar(
        texto
    )

    patron = (
        r"numero\s+de\s+autorizacion"
        r"\s*[:\-]?\s*"
        r"(\d+)"
    )

    resultado = re.search(
        patron,
        texto
    )

    if resultado:

        return resultado.group(
            1
        )

    return None


# ============================================================
# MONTO
# ============================================================

def es_monto(texto):

    texto = str(
        texto
    ).strip()

    patron = (
        r"^\$?\s*"
        r"[\d,]+"
        r"(?:\.\d{1,2})?"
        r"(?:\s*(?:MXN|USD|EUR))?$"
    )

    return bool(
        re.fullmatch(
            patron,
            texto,
            re.IGNORECASE
        )
    )


# ============================================================
# CLAVE DE RASTREO
# ============================================================

def es_clave_rastreo(texto):

    numeros = re.sub(
        r"\D",
        "",
        str(texto)
    )

    return bool(
        re.fullmatch(
            r"\d{18}",
            numeros
        )
    )


# ============================================================
# FECHA
# ============================================================

def es_fecha(texto):

    texto = str(
        texto
    ).strip()

    patrones = [

        r"\d{1,2}/\d{1,2}/\d{2,4}",

        r"\d{1,2}\s+[A-Za-z]{3,}\s+\d{4}",

        r"\d{1,2}\s+de\s+[A-Za-z]+\s+de\s+\d{4}",

    ]

    return any(
        re.search(
            patron,
            texto,
            re.IGNORECASE
        )
        for patron in patrones
    )


# ============================================================
# HORA
# ============================================================

def es_hora(texto):

    return bool(
        re.fullmatch(
            r"\d{1,2}:\d{2}(?::\d{2})?",
            str(texto).strip()
        )
    )


# ============================================================
# REFERENCIA NUMÉRICA
# ============================================================

def es_referencia(texto):

    numeros = re.sub(
        r"\D",
        "",
        str(texto)
    )

    return bool(
        re.fullmatch(
            r"\d{4,10}",
            numeros
        )
    )


# ============================================================
# TIPO DE CUENTA
# ============================================================

def es_tipo_cuenta(texto):

    texto = normalizar(
        texto
    )

    valores = [

        "clabe",

        "cuenta",

        "tarjeta",

    ]

    return any(
        valor in texto
        for valor in valores
    )


# ============================================================
# TIPO DE PERSONA
# ============================================================

def es_tipo_persona(texto):

    texto = normalizar(
        texto
    )

    return (

        "persona fisica" in texto

        or

        "persona moral" in texto

    )


# ============================================================
# CONCEPTO
# ============================================================

def es_concepto(texto):

    texto = str(
        texto
    ).strip()

    if len(texto) < 3:
        return False

    if texto.isdigit():
        return False

    if es_monto(texto):
        return False

    if es_fecha(texto):
        return False

    if es_hora(texto):
        return False

    return True