# ============================================================
# EXTRACTOR OCR - CLARO PAY
# ============================================================
#
# Banco:
#   Claro Pay
#
# Campos:
#   - fecha
#   - monto
#   - cuenta_origen
#   - cuenta_destino
#   - concepto
#   - referencia
#   - clave_rastreo
#
# ============================================================

import re


# ============================================================
# CONFIGURACIÓN
# ============================================================

BANCO = "Claro Pay"

TIPO = "TRANSFERENCIA_CLARO_PAY"


# ============================================================
# UTILIDADES
# ============================================================

def obtener_detecciones(datos_json):
    """
    Obtiene la lista de detecciones OCR.

    Compatible con el formato:

        {
            "detecciones": [...]
        }

    También permite recibir directamente una lista.
    """

    if isinstance(datos_json, list):
        return datos_json

    if not isinstance(datos_json, dict):
        return []

    detecciones = datos_json.get(
        "detecciones",
        []
    )

    if isinstance(detecciones, list):
        return detecciones

    return []


# ============================================================
# TEXTO
# ============================================================

def texto_deteccion(deteccion):
    """
    Obtiene y limpia el texto de una detección.
    """

    if not isinstance(deteccion, dict):
        return ""

    texto = deteccion.get(
        "texto",
        ""
    )

    if texto is None:
        return ""

    return str(texto).strip()


# ============================================================
# COORDENADAS
# ============================================================

def coordenada_x(deteccion):
    try:
        return float(
            deteccion.get(
                "x",
                0
            )
        )
    except (
        TypeError,
        ValueError
    ):
        return 0.0


def coordenada_y(deteccion):
    try:
        return float(
            deteccion.get(
                "y",
                0
            )
        )
    except (
        TypeError,
        ValueError
    ):
        return 0.0


def confianza(deteccion):
    try:
        return float(
            deteccion.get(
                "confianza",
                1.0
            )
        )
    except (
        TypeError,
        ValueError
    ):
        return 1.0


# ============================================================
# NORMALIZAR TEXTO
# ============================================================

def normalizar_texto(texto):
    """
    Normalización ligera.

    No elimina caracteres importantes del valor.
    """

    texto = str(
        texto or ""
    )

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


# ============================================================
# BUSCAR DETECCIÓN
# ============================================================

def buscar_deteccion(
    detecciones,
    patron
):
    """
    Busca la primera detección cuyo texto
    coincida con el patrón.
    """

    regex = re.compile(
        patron,
        re.IGNORECASE
    )

    for deteccion in detecciones:

        texto = texto_deteccion(
            deteccion
        )

        if not texto:
            continue

        if regex.search(texto):
            return deteccion

    return None


# ============================================================
# BUSCAR ÍNDICE
# ============================================================

def buscar_indice(
    detecciones,
    patron
):
    """
    Devuelve el índice de la primera detección
    que coincida con el patrón.
    """

    regex = re.compile(
        patron,
        re.IGNORECASE
    )

    for indice, deteccion in enumerate(
        detecciones
    ):

        texto = texto_deteccion(
            deteccion
        )

        if not texto:
            continue

        if regex.search(texto):
            return indice

    return None


# ============================================================
# BUSCAR DETECCIÓN POSTERIOR
# ============================================================

def siguiente_deteccion(
    detecciones,
    indice,
    limite=6
):
    """
    Busca la siguiente detección útil después
    de una etiqueta.
    """

    inicio = indice + 1

    fin = min(
        indice + limite + 1,
        len(detecciones)
    )

    for i in range(
        inicio,
        fin
    ):

        texto = texto_deteccion(
            detecciones[i]
        )

        if not texto:
            continue

        return detecciones[i]

    return None


# ============================================================
# FECHA
# ============================================================

def extraer_fecha(
    detecciones
):
    """
    Extrae la fecha y hora de Claro Pay.

    Formato esperado:

        DD/MM/YY HH:MM

    PaddleOCR puede entregar:

        DD/MM/YYHH:MM

    Ejemplos reales:

        29/06/2612:05
        08/06/2610:53
        09/07/2612:16
        07/07/2613:36

    IMPORTANTE:
    Cuando fecha y hora vienen pegadas, el año siempre
    corresponde a los dos dígitos posteriores al segundo '/'.

    Por ejemplo:

        29/06/2612:05
              ^^ ^^
              año hora
               26  12

    Se evita que la expresión interprete "261" como año
    y "2" como hora.
    """

    # --------------------------------------------------------
    # FORMATO PRINCIPAL
    #
    # DD/MM/YY HH:MM
    # DD/MM/YYHH:MM
    #
    # El año se fija a 2 dígitos.
    # --------------------------------------------------------

    patron = re.compile(
        r"(?<!\d)"
        r"(\d{1,2})"
        r"/"
        r"(\d{1,2})"
        r"/"
        r"(\d{2})"
        r"\s*"
        r"(\d{1,2})"
        r":"
        r"(\d{2})"
        r"(?!\d)"
    )

    for deteccion in detecciones:

        texto = texto_deteccion(
            deteccion
        )

        if not texto:
            continue

        match = patron.search(
            texto
        )

        if not match:
            continue

        dia = match.group(1)
        mes = match.group(2)
        anio = match.group(3)
        hora = match.group(4)
        minuto = match.group(5)

        # ----------------------------------------------------
        # Validaciones básicas
        # ----------------------------------------------------

        dia_int = int(dia)
        mes_int = int(mes)
        hora_int = int(hora)
        minuto_int = int(minuto)

        if not 1 <= dia_int <= 31:
            continue

        if not 1 <= mes_int <= 12:
            continue

        if not 0 <= hora_int <= 23:
            continue

        if not 0 <= minuto_int <= 59:
            continue

        return (
            f"{dia_int:02d}/"
            f"{mes_int:02d}/"
            f"{anio} "
            f"{hora_int:02d}:"
            f"{minuto_int:02d}"
        )

    return None


# ============================================================
# MONTO
# ============================================================

def extraer_monto(
    detecciones
):
    """
    Prioridad:

    1. Monto ubicado después de 'Monto enviado:'
    2. Monto principal del comprobante.
    """

    patron_monto = re.compile(
        r"\$\s*"
        r"\d{1,3}"
        r"(?:,\d{3})*"
        r"(?:\.\d{2})?"
    )

    # --------------------------------------------------------
    # PRIMERO: Monto enviado
    # --------------------------------------------------------

    indice = buscar_indice(
        detecciones,
        r"monto\s+enviado"
    )

    if indice is not None:

        for i in range(
            indice + 1,
            min(
                indice + 5,
                len(detecciones)
            )
        ):

            texto = texto_deteccion(
                detecciones[i]
            )

            match = patron_monto.search(
                texto
            )

            if match:
                return match.group(0)

    # --------------------------------------------------------
    # SEGUNDO: cualquier monto
    # --------------------------------------------------------

    for deteccion in detecciones:

        texto = texto_deteccion(
            deteccion
        )

        match = patron_monto.search(
            texto
        )

        if match:
            return match.group(0)

    return None


# ============================================================
# CUENTA DESTINO
# ============================================================

def extraer_cuenta_destino(
    detecciones
):
    """
    Claro Pay:

        Envio a: mnet

    El OCR actual entrega directamente:

        Envio a: mnet

    Por lo tanto se extrae únicamente el dato
    que realmente está presente en OCR.
    """

    for deteccion in detecciones:

        texto = texto_deteccion(
            deteccion
        )

        if not texto:
            continue

        match = re.search(
            r"env[ií]o\s+a\s*:\s*(.+)",
            texto,
            re.IGNORECASE
        )

        if match:

            valor = normalizar_texto(
                match.group(1)
            )

            if valor:
                return valor

    # --------------------------------------------------------
    # Respaldo
    # --------------------------------------------------------

    indice = buscar_indice(
        detecciones,
        r"env[ií]o\s+a"
    )

    if indice is not None:

        siguiente = siguiente_deteccion(
            detecciones,
            indice,
            limite=3
        )

        if siguiente is not None:

            valor = texto_deteccion(
                siguiente
            )

            if valor:
                return valor

    return None


# ============================================================
# CUENTA ORIGEN
# ============================================================

def extraer_cuenta_origen(
    detecciones
):
    """
    Estructura real:

        Origen:
        Cuenta
        Claro-pay
        00
        NBURSA
        *******530

    o:

        Origen:
        Cuenta
        Claro- pay BURSA
        *******
        530

    Resultado normalizado:

        Claro pay *******530
    """

    indice = buscar_indice(
        detecciones,
        r"^origen\s*:?"
    )

    if indice is None:
        return None

    candidatos = []

    limite = min(
        indice + 8,
        len(detecciones)
    )

    for i in range(
        indice + 1,
        limite
    ):

        texto = texto_deteccion(
            detecciones[i]
        )

        if not texto:
            continue

        # -----------------------------------------------
        # Asteriscos + número
        # -----------------------------------------------

        if re.fullmatch(
            r"\*+\s*\d+",
            texto
        ):

            candidatos.append(
                texto
            )

            continue

        # -----------------------------------------------
        # Claro-pay
        # Claro- pay
        # Claro pay
        # -----------------------------------------------

        if re.search(
            r"claro\s*-\s*pay|claro\s+pay",
            texto,
            re.IGNORECASE
        ):

            limpio = re.sub(
                r"\bBURSA\b",
                "",
                texto,
                flags=re.IGNORECASE
            )

            # ------------------------------------------------
            # Normalizar variantes OCR:
            #
            # Claro-pay
            # Claro- pay
            # Claro pay
            #
            # a:
            #
            # Claro pay
            # ------------------------------------------------

            limpio = re.sub(
                r"claro\s*-\s*pay",
                "Claro pay",
                limpio,
                flags=re.IGNORECASE
            )

            limpio = re.sub(
                r"claro\s+pay",
                "Claro pay",
                limpio,
                flags=re.IGNORECASE
            )

            limpio = re.sub(
                r"\s+",
                " ",
                limpio
            ).strip()

            if limpio:
                candidatos.insert(
                    0,
                    limpio
                )

    if not candidatos:
        return None

    # --------------------------------------------------------
    # Separar Claro Pay y cuenta
    # --------------------------------------------------------

    claro = None
    cuenta = None

    for valor in candidatos:

        if re.search(
            r"claro\s+pay",
            valor,
            re.IGNORECASE
        ):

            claro = "Claro pay"

        elif re.fullmatch(
            r"\*+\s*\d+",
            valor
        ):

            cuenta = valor

    # --------------------------------------------------------
    # Resultado completo
    # --------------------------------------------------------

    if claro and cuenta:

        return (
            f"{claro} "
            f"{cuenta}"
        )

    if claro:
        return claro

    if cuenta:
        return (
            "Claro pay "
            f"{cuenta}"
        )

    return None


# ============================================================
# CONCEPTO
# ============================================================

def extraer_concepto(
    detecciones
):
    """
    Busca el valor posterior a:

        Concepto:

    Si no existe valor, devuelve None.

    Esto es necesario para image_716,
    donde Concepto no tiene contenido.
    """

    indice = buscar_indice(
        detecciones,
        r"^concepto\s*:?"
    )

    if indice is None:
        return None

    # --------------------------------------------------------
    # Buscar hacia adelante
    # --------------------------------------------------------

    for i in range(
        indice + 1,
        min(
            indice + 5,
            len(detecciones)
        )
    ):

        texto = texto_deteccion(
            detecciones[i]
        )

        if not texto:
            continue

        # ----------------------------------------------------
        # Si llegamos a otra etiqueta,
        # no existe concepto.
        # ----------------------------------------------------

        if re.match(
            r"^(referencia\s+num[eé]rica|"
            r"clave\s+de\s+rastreo|"
            r"autorizaci[oó]n|"
            r"origen|"
            r"env[ií]o\s+a|"
            r"monto\s+enviado)\s*:?",
            texto,
            re.IGNORECASE
        ):

            return None

        return normalizar_texto(
            texto
        )

    return None


# ============================================================
# REFERENCIA
# ============================================================

def extraer_referencia(
    detecciones
):
    """
    Busca:

        Referencia numérica:
        2906202
    """

    indice = buscar_indice(
        detecciones,
        r"referencia\s+num[eé]rica"
    )

    if indice is None:
        return None

    for i in range(
        indice + 1,
        min(
            indice + 5,
            len(detecciones)
        )
    ):

        texto = texto_deteccion(
            detecciones[i]
        )

        if not texto:
            continue

        if re.fullmatch(
            r"\d+",
            texto
        ):

            return texto

    return None


# ============================================================
# CLAVE DE RASTREO
# ============================================================

def extraer_clave_rastreo(
    detecciones
):
    """
    Busca específicamente claves:

        036CLAR...

    Esto evita confundirla con:

        - autorización
        - referencia
        - monto
        - otros números
    """

    patron = re.compile(
        r"036\s*CLAR[A-Za-z0-9]+",
        re.IGNORECASE
    )

    # --------------------------------------------------------
    # PRIMERO: cerca de la etiqueta
    # --------------------------------------------------------

    indice = buscar_indice(
        detecciones,
        r"clave\s+de\s+rastreo"
    )

    if indice is not None:

        for i in range(
            indice + 1,
            min(
                indice + 5,
                len(detecciones)
            )
        ):

            texto = texto_deteccion(
                detecciones[i]
            )

            if not texto:
                continue

            match = patron.search(
                texto
            )

            if match:

                valor = re.sub(
                    r"\s+",
                    "",
                    match.group(0)
                )

                return valor.upper()

    # --------------------------------------------------------
    # SEGUNDO: búsqueda global
    # --------------------------------------------------------

    for deteccion in detecciones:

        texto = texto_deteccion(
            deteccion
        )

        match = patron.search(
            texto
        )

        if match:

            valor = re.sub(
                r"\s+",
                "",
                match.group(0)
            )

            return valor.upper()

    return None


# ============================================================
# DETECTAR BANCO
# ============================================================

def extraer_banco(
    datos_json,
    detecciones
):
    """
    Primero utiliza el campo banco del JSON.
    Después busca Claro Pay en OCR.
    """

    if isinstance(
        datos_json,
        dict
    ):

        banco_json = datos_json.get(
            "banco"
        )

        if banco_json:

            banco_json = normalizar_texto(
                banco_json
            )

            if re.search(
                r"claro\s*pay",
                banco_json,
                re.IGNORECASE
            ):

                return BANCO

    for deteccion in detecciones:

        texto = texto_deteccion(
            deteccion
        )

        if re.search(
            r"claro\s*[- ]?\s*pay",
            texto,
            re.IGNORECASE
        ):

            return BANCO

    return BANCO


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def extraer(
    datos_json
):
    """
    Función principal del extractor.
    """

    detecciones = obtener_detecciones(
        datos_json
    )

    return {
        "banco": extraer_banco(
            datos_json,
            detecciones
        ),

        "tipo": TIPO,

        "campos": {

            "fecha":
                extraer_fecha(
                    detecciones
                ),

            "monto":
                extraer_monto(
                    detecciones
                ),

            "cuenta_origen":
                extraer_cuenta_origen(
                    detecciones
                ),

            "cuenta_destino":
                extraer_cuenta_destino(
                    detecciones
                ),

            "concepto":
                extraer_concepto(
                    detecciones
                ),

            "referencia":
                extraer_referencia(
                    detecciones
                ),

            "clave_rastreo":
                extraer_clave_rastreo(
                    detecciones
                ),
        }
    }


# ============================================================
# CLASE DE COMPATIBILIDAD
# ============================================================

class ClaroPayExtractor:

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

    return ClaroPayExtractor()