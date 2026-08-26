import re
import unicodedata
from datetime import datetime


# ============================================================
# CONFIGURACIÓN
# ============================================================

BANCO = "OXXO"
TIPO = "PAGO_OXXO"


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
        "NFD",
        texto
    )

    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(
            caracter
        ) != "Mn"
    )

    return texto.lower().strip()


def campo_encontrado(
    valor,
    metodo="OCR_DIRECTO",
    confianza=1.0
):

    valor = normalizar_texto(
        valor
    )

    if not valor:
        return campo_no_encontrado()

    return {
        "valor": valor,
        "metodo": metodo,
        "confianza": confianza
    }


def campo_no_encontrado():

    return {
        "valor": "NO ENCONTRADO",
        "metodo": "NO ENCONTRADO",
        "confianza": 0.0
    }


# ============================================================
# OBTENER TEXTO OCR
# ============================================================

def obtener_lineas(datos_json):

    if not isinstance(
        datos_json,
        dict
    ):
        return []

    # --------------------------------------------------------
    # OPCIÓN 1: lineas
    # --------------------------------------------------------

    lineas = datos_json.get(
        "lineas",
        []
    )

    if isinstance(
        lineas,
        list
    ):

        resultado = []

        for linea in lineas:

            # Puede ser string
            if isinstance(
                linea,
                str
            ):

                texto = normalizar_texto(
                    linea
                )

                if texto:
                    resultado.append(
                        texto
                    )

                continue

            # Puede ser diccionario
            if isinstance(
                linea,
                dict
            ):

                texto = (
                    linea.get("texto")
                    or linea.get("text")
                    or ""
                )

                texto = normalizar_texto(
                    texto
                )

                if texto:
                    resultado.append(
                        texto
                    )

        if resultado:
            return resultado

    # --------------------------------------------------------
    # OPCIÓN 2: detecciones
    # --------------------------------------------------------

    detecciones = datos_json.get(
        "detecciones",
        []
    )

    resultado = []

    if isinstance(
        detecciones,
        list
    ):

        for deteccion in detecciones:

            if isinstance(
                deteccion,
                str
            ):

                texto = normalizar_texto(
                    deteccion
                )

            elif isinstance(
                deteccion,
                dict
            ):

                texto = (
                    deteccion.get("texto")
                    or deteccion.get("text")
                    or ""
                )

                texto = normalizar_texto(
                    texto
                )

            else:

                continue

            if texto:
                resultado.append(
                    texto
                )

    return resultado


# ============================================================
# FECHA
# ============================================================

def fecha_valida(
    dia,
    mes,
    anio,
    hora,
    minuto
):

    try:

        datetime(
            int(anio),
            int(mes),
            int(dia),
            int(hora),
            int(minuto)
        )

        return True

    except (
        ValueError,
        TypeError
    ):

        return False


def extraer_fecha(lineas):

    patrones = [

        # 06/07/2026 09:37
        r"\b(\d{2})/(\d{2})/(\d{4})\s+(\d{1,2}):(\d{2})\b",

        # 06/07/2026|09:37
        r"\b(\d{2})/(\d{2})/(\d{4})\s*[|I]\s*(\d{1,2}):(\d{2})\b",

        # 06/07/2026 09:37:00
        r"\b(\d{2})/(\d{2})/(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})\b",

        # OCR puede separar ligeramente la fecha
        r"\b(\d{2})/(\d{2})/(\d{4})\D+(\d{1,2}):(\d{2})\b",
    ]

    for linea in lineas:

        for patron in patrones:

            match = re.search(
                patron,
                linea
            )

            if not match:
                continue

            grupos = match.groups()

            dia = grupos[0]
            mes = grupos[1]
            anio = grupos[2]
            hora = grupos[3]
            minuto = grupos[4]

            if not fecha_valida(
                dia,
                mes,
                anio,
                hora,
                minuto
            ):
                # No corregimos una fecha dudosa.
                continue

            return (
                f"{dia}/{mes}/{anio} "
                f"{hora}:{minuto}"
            )

    return None


# ============================================================
# MONTO
# ============================================================

def obtener_montos(linea):

    return re.findall(
        r"\$\s*[\d,]+(?:\.\d{1,2})?",
        linea
    )


def extraer_monto(lineas):

    # --------------------------------------------------------
    # PRIORIDAD 1:
    # Buscar una línea que contenga MONTO.
    #
    # Importante:
    # NO tomar PAGO TOTAL.
    # NO tomar COMISION.
    # --------------------------------------------------------

    for linea in lineas:

        texto = normalizar_texto(
            linea
        )

        texto_busqueda = normalizar_busqueda(
            texto
        )

        if "monto" not in texto_busqueda:
            continue

        montos = obtener_montos(
            texto
        )

        if not montos:
            continue

        # ----------------------------------------------------
        # Si aparecen varios montos en la misma línea,
        # intentamos elegir el que está inmediatamente
        # relacionado con MONTO.
        # ----------------------------------------------------

        posicion_monto = texto_busqueda.find(
            "monto"
        )

        candidatos = []

        for match in re.finditer(
            r"\$\s*[\d,]+(?:\.\d{1,2})?",
            texto
        ):

            candidatos.append(
                (
                    match.start(),
                    match.group(0).strip()
                )
            )

        if candidatos:

            # Primer monto después de la palabra MONTO.
            posteriores = [
                candidato
                for candidato in candidatos
                if candidato[0] >= posicion_monto
            ]

            if posteriores:

                return posteriores[0][1]

            return candidatos[0][1]

    # --------------------------------------------------------
    # PRIORIDAD 2:
    # Algunos OCR destruyen la palabra MONTO.
    #
    # Buscamos una cantidad en líneas que NO sean:
    # - PAGO TOTAL
    # - COMISION
    # - COMISIÓN
    # --------------------------------------------------------

    for linea in lineas:

        texto = normalizar_texto(
            linea
        )

        texto_busqueda = normalizar_busqueda(
            texto
        )

        if (
            "pago total" in texto_busqueda
            or "comision" in texto_busqueda
        ):
            continue

        montos = obtener_montos(
            texto
        )

        if len(montos) == 1:

            return montos[0].strip()

    return None


# ============================================================
# REFERENCIA
# ============================================================

def limpiar_referencia(
    valor
):

    valor = normalizar_texto(
        valor
    )

    if not valor:
        return None

    # --------------------------------------------------------
    # Eliminar espacios
    # --------------------------------------------------------

    valor = re.sub(
        r"\s+",
        "",
        valor
    )

    # --------------------------------------------------------
    # Referencia normal:
    #
    # ************2278
    # ****2278
    #
    # Aceptamos basura OCR ANTES de los asteriscos,
    # pero no números arbitrarios después.
    # --------------------------------------------------------

    match = re.search(
        r"(\*{2,}\d{4})(?!\d)",
        valor
    )

    if match:

        return match.group(
            1
        )

    # --------------------------------------------------------
    # Variante donde OCR metió caracteres antes de los *.
    # --------------------------------------------------------

    match = re.search(
        r"\D*(\*{2,}\d{4})(?!\d)",
        valor
    )

    if match:

        return match.group(
            1
        )

    # --------------------------------------------------------
    # Si solamente quedaron los últimos 4 dígitos,
    # NO inventamos los asteriscos.
    # --------------------------------------------------------

    match = re.fullmatch(
        r"\d{4}",
        valor
    )

    if match:

        return match.group(
            0
        )

    return None


def extraer_referencia(lineas):

    for indice, linea in enumerate(lineas):

        texto = normalizar_texto(
            linea
        )

        texto_busqueda = normalizar_busqueda(
            texto
        )

        if "referencia" not in texto_busqueda:
            continue

        # ----------------------------------------------------
        # Buscar después de REFERENCIA
        # ----------------------------------------------------

        match = re.search(
            r"referencia\s*:?\s*(.*)$",
            texto,
            flags=re.IGNORECASE
        )

        if match:

            valor = match.group(
                1
            )

            resultado = limpiar_referencia(
                valor
            )

            if resultado:
                return resultado

        # ----------------------------------------------------
        # Si la referencia está en la línea siguiente
        # ----------------------------------------------------

        if indice + 1 < len(lineas):

            resultado = limpiar_referencia(
                lineas[indice + 1]
            )

            if resultado:
                return resultado

    return None


# ============================================================
# AUTORIZACIÓN
# ============================================================

def extraer_autorizacion(lineas):

    for indice, linea in enumerate(lineas):

        texto = normalizar_texto(
            linea
        )

        texto_busqueda = normalizar_busqueda(
            texto
        )

        # ----------------------------------------------------
        # Variantes OCR:
        #
        # AUTORIZACION
        # AUTORIZACIÓN
        # AUTORINACION
        # AUTORLZACION
        #
        # Buscamos la raíz AUTORI.
        # ----------------------------------------------------

        if "autori" not in texto_busqueda:
            continue

        # ----------------------------------------------------
        # Número en la misma línea
        # ----------------------------------------------------

        match = re.search(
            r"autori\w*\s*:?\s*(\d{4,8})",
            texto,
            flags=re.IGNORECASE
        )

        if match:

            return match.group(
                1
            )

        # ----------------------------------------------------
        # Si hay texto intermedio debido al OCR:
        #
        # AUTORIZACION ... : 052674
        # ----------------------------------------------------

        posicion = texto_busqueda.find(
            "autori"
        )

        if posicion >= 0:

            resto = texto[
                posicion:
            ]

            match = re.search(
                r"\b(\d{4,8})\b",
                resto
            )

            if match:

                return match.group(
                    1
                )

        # ----------------------------------------------------
        # Número en línea siguiente
        # ----------------------------------------------------

        if indice + 1 < len(lineas):

            siguiente = normalizar_texto(
                lineas[indice + 1]
            )

            match = re.fullmatch(
                r"\D*(\d{4,8})\D*",
                siguiente
            )

            if match:

                return match.group(
                    1
                )

    return None


# ============================================================
# FOLIO DE VENTA
# ============================================================

def extraer_folio_venta(lineas):

    for indice, linea in enumerate(lineas):

        texto = normalizar_texto(
            linea
        )

        # ----------------------------------------------------
        # Normalización especial para errores comunes OCR:
        #
        # JENTA -> VENTA
        # VENTA -> VENTA
        #
        # NO sustituimos números.
        # ----------------------------------------------------

        texto_busqueda = normalizar_busqueda(
            texto
        )

        texto_busqueda = re.sub(
            r"folio\s+de\s+jenta",
            "folio de venta",
            texto_busqueda
        )

        # ----------------------------------------------------
        # FOLIO DE VENTA: 1844594
        # FOLIO DE JENTA: 1844594
        # ----------------------------------------------------

        match = re.search(
            r"folio\s+de\s+[vj]enta\s*:?\s*(\d{4,10})",
            texto_busqueda
        )

        if match:

            return match.group(
                1
            )

        # ----------------------------------------------------
        # Buscar número después de la frase,
        # incluso si OCR metió texto intermedio.
        # ----------------------------------------------------

        posicion = texto_busqueda.find(
            "folio de venta"
        )

        if posicion >= 0:

            resto = texto_busqueda[
                posicion + len("folio de venta"):
            ]

            match = re.search(
                r"\b(\d{4,10})\b",
                resto
            )

            if match:

                return match.group(
                    1
                )

        # ----------------------------------------------------
        # FOLIO EN LA SIGUIENTE LÍNEA
        # ----------------------------------------------------

        if (
            "folio de venta" in texto_busqueda
            or "folio de jenta" in texto_busqueda
        ):

            if indice + 1 < len(lineas):

                siguiente = normalizar_texto(
                    lineas[indice + 1]
                )

                match = re.fullmatch(
                    r"\D*(\d{4,10})\D*",
                    siguiente
                )

                if match:

                    return match.group(
                        1
                    )

    return None


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def extraer(
    datos_json
):

    lineas = obtener_lineas(
        datos_json
    )

    campos = {

        "fecha": campo_encontrado(
            extraer_fecha(
                lineas
            )
        ),

        "monto": campo_encontrado(
            extraer_monto(
                lineas
            )
        ),

        "numero_referencia":
            campo_encontrado(
                extraer_referencia(
                    lineas
                )
            ),

        "autorizacion":
            campo_encontrado(
                extraer_autorizacion(
                    lineas
                )
            ),

        "folio_venta":
            campo_encontrado(
                extraer_folio_venta(
                    lineas
                )
            ),
    }

    return {

        "banco": BANCO,

        "tipo": TIPO,

        "campos": campos
    }


# ============================================================
# CLASE DE COMPATIBILIDAD
# ============================================================

class OxxoExtractor:

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

    return OxxoExtractor()