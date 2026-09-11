import re


# ============================================================
# CONSTANTES
# ============================================================

BANCO = "BanBajio"


# ============================================================
# UTILIDADES
# ============================================================

def normalizar_texto(texto):
    if texto is None:
        return ""

    texto = str(texto)

    texto = (
        texto
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("\t", " ")
    )

    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def obtener_detecciones(datos):
    detecciones = datos.get("detecciones", [])

    if not isinstance(detecciones, list):
        return []

    return detecciones


def obtener_lineas(datos):
    lineas = datos.get("lineas", [])

    if not isinstance(lineas, list):
        return []

    resultado = []

    for linea in lineas:

        if isinstance(linea, str):

            texto = normalizar_texto(linea)

            if texto:
                resultado.append(texto)

        elif isinstance(linea, dict):

            texto = (
                linea.get("texto")
                or linea.get("text")
                or linea.get("value")
                or ""
            )

            texto = normalizar_texto(texto)

            if texto:
                resultado.append(texto)

    return resultado


def obtener_texto_completo(datos):

    texto = datos.get(
        "texto_completo",
        ""
    )

    if texto:
        return normalizar_texto(texto)

    lineas = obtener_lineas(datos)

    return " ".join(lineas)


def buscar_linea(lineas, patrones):

    for linea in lineas:

        texto = normalizar_texto(linea)

        for patron in patrones:

            if re.search(
                patron,
                texto,
                re.IGNORECASE
            ):
                return texto

    return None


def valor_despues_de_dos_puntos(linea):

    if not linea:
        return None

    if ":" not in linea:
        return None

    valor = linea.split(
        ":",
        1
    )[1].strip()

    return valor if valor else None


def valor_despues_de_patron(
    linea,
    patrones
):

    if not linea:
        return None

    for patron in patrones:

        resultado = re.search(
            patron,
            linea,
            re.IGNORECASE
        )

        if resultado:

            valor = resultado.group(1).strip()

            if valor:
                return valor

    return None


def limpiar_valor(valor):

    if valor is None:
        return None

    valor = normalizar_texto(valor)

    return valor if valor else None


# ============================================================
# BANCO
# ============================================================

def extraer_banco(datos):

    texto_completo = obtener_texto_completo(
        datos
    )

    if re.search(
        r"\bBanBaj[ií]o\b",
        texto_completo,
        re.IGNORECASE
    ):
        return BANCO

    if re.search(
        r"\bBaj[ií]oNet\b",
        texto_completo,
        re.IGNORECASE
    ):
        return BANCO

    return BANCO


# ============================================================
# FECHA
# ============================================================

def extraer_fecha(datos):

    texto_completo = obtener_texto_completo(
        datos
    )

    patrones = [
        r"\b\d{1,2}[-/](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[-/]\d{4}\b",
        r"\b\d{1,2}[-/](?:Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic)[-/]\d{4}\b",
        r"\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b",
    ]

    for patron in patrones:

        resultado = re.search(
            patron,
            texto_completo,
            re.IGNORECASE
        )

        if resultado:
            return resultado.group(0)

    return None


# ============================================================
# CUENTA ORIGEN
# ============================================================

def extraer_cuenta_origen(datos):

    lineas = obtener_lineas(datos)

    # --------------------------------------------------------
    # FORMATO ESPECIAL BANBAJIO
    #
    # CUENTA CONECTA BANBAJIO -
    # Cuenta Origen:
    # ********0201
    #
    # Resultado:
    # CUENTA CONECTA BANBAJIO - ********0201
    # --------------------------------------------------------

    detecciones = obtener_detecciones(
        datos
    )

    for i, deteccion in enumerate(detecciones):

        texto = normalizar_texto(
            deteccion.get(
                "texto",
                ""
            )
        )

        if not re.search(
            r"^Cuenta\s+Origen\s*:?\s*$",
            texto,
            re.IGNORECASE
        ):
            continue

        x_origen = float(
            deteccion.get(
                "x",
                0
            )
        )

        y_origen = float(
            deteccion.get(
                "y",
                0
            )
        )

        # ----------------------------------------------------
        # BUSCAR EL NÚMERO DE CUENTA
        # DEBAJO DE "Cuenta Origen"
        # ----------------------------------------------------

        numero_cuenta = None

        for candidato in detecciones:

            texto_candidato = normalizar_texto(
                candidato.get(
                    "texto",
                    ""
                )
            )

            if not re.fullmatch(
                r"\*+\d+",
                texto_candidato
            ):
                continue

            x_candidato = float(
                candidato.get(
                    "x",
                    0
                )
            )

            y_candidato = float(
                candidato.get(
                    "y",
                    0
                )
            )

            if (
                y_candidato > y_origen
                and y_candidato - y_origen <= 60
                and x_candidato >= x_origen + 100
            ):
                numero_cuenta = texto_candidato
                break

        if numero_cuenta:

            # ------------------------------------------------
            # BUSCAR EL TIPO DE CUENTA
            #
            # CUENTA CONECTA BANBAJIO -
            #
            # Está arriba de "Cuenta Origen".
            # ------------------------------------------------

            cuenta_conecta = None

            for candidato in detecciones:

                texto_candidato = normalizar_texto(
                    candidato.get(
                        "texto",
                        ""
                    )
                )

                if not re.search(
                    r"^CUENTA\s+CONECTA\s+BANBAJIO\s*-$",
                    texto_candidato,
                    re.IGNORECASE
                ):
                    continue

                x_candidato = float(
                    candidato.get(
                        "x",
                        0
                    )
                )

                y_candidato = float(
                    candidato.get(
                        "y",
                        0
                    )
                )

                if (
                    abs(y_candidato - y_origen) <= 30
                    or (
                        y_candidato < y_origen
                        and y_origen - y_candidato <= 40
                    )
                ):
                    cuenta_conecta = texto_candidato
                    break

            if cuenta_conecta:

                return (
                    f"{cuenta_conecta} "
                    f"{numero_cuenta}"
                )

    # --------------------------------------------------------
    # FORMATO ESPECIAL image_649
    #
    # Cuenta origen
    # Cuenta Nómina
    # ********2101
    # Nómina 1
    #
    # Resultado:
    # Cuenta Nómina ********2101
    #
    # IMPORTANTE:
    # Se utiliza la posición de las detecciones OCR para
    # evitar tomar "Nómina 1" como parte de la cuenta.
    # --------------------------------------------------------

    for i, deteccion in enumerate(detecciones):

        texto = normalizar_texto(
            deteccion.get(
                "texto",
                ""
            )
        )

        if not re.fullmatch(
            r"Cuenta\s+origen",
            texto,
            re.IGNORECASE
        ):
            continue

        x_origen = float(
            deteccion.get(
                "x",
                0
            )
        )

        y_origen = float(
            deteccion.get(
                "y",
                0
            )
        )

        tipo_cuenta = None
        numero_cuenta = None

        # ----------------------------------------------------
        # BUSCAR "Cuenta Nómina"
        # ----------------------------------------------------

        for candidato in detecciones:

            texto_candidato = normalizar_texto(
                candidato.get(
                    "texto",
                    ""
                )
            )

            if not re.fullmatch(
                r"Cuenta\s+Nómina",
                texto_candidato,
                re.IGNORECASE
            ):
                continue

            x_candidato = float(
                candidato.get(
                    "x",
                    0
                )
            )

            y_candidato = float(
                candidato.get(
                    "y",
                    0
                )
            )

            if (
                y_candidato >= y_origen
                and y_candidato - y_origen <= 80
                and x_candidato >= x_origen + 400
            ):
                tipo_cuenta = texto_candidato
                break

        # ----------------------------------------------------
        # BUSCAR ********2101
        # ----------------------------------------------------

        for candidato in detecciones:

            texto_candidato = normalizar_texto(
                candidato.get(
                    "texto",
                    ""
                )
            )

            if not re.fullmatch(
                r"\*+\d+",
                texto_candidato
            ):
                continue

            x_candidato = float(
                candidato.get(
                    "x",
                    0
                )
            )

            y_candidato = float(
                candidato.get(
                    "y",
                    0
                )
            )

            if (
                y_candidato > y_origen
                and y_candidato - y_origen <= 100
                and x_candidato >= x_origen + 500
            ):
                numero_cuenta = texto_candidato
                break

        if tipo_cuenta and numero_cuenta:

            return (
                f"{tipo_cuenta} "
                f"{numero_cuenta}"
            )

    # --------------------------------------------------------
    # FORMATO ESPECIAL:
    #
    # Cuenta origen
    # Cuenta Nómina
    # ********2101
    #
    # Se conserva para image_649.
    # --------------------------------------------------------

    for i, linea in enumerate(lineas):

        if re.fullmatch(
            r"Cuenta\s+origen",
            linea,
            re.IGNORECASE
        ):

            if i + 2 < len(lineas):

                tipo_cuenta = limpiar_valor(
                    lineas[i + 1]
                )

                numero_cuenta = limpiar_valor(
                    lineas[i + 2]
                )

                if (
                    tipo_cuenta
                    and numero_cuenta
                    and re.search(
                        r"\*+\d+",
                        numero_cuenta
                    )
                ):
                    return (
                        f"{tipo_cuenta} "
                        f"{numero_cuenta}"
                    )

    # --------------------------------------------------------
    # LÓGICA EXISTENTE
    # --------------------------------------------------------

    patrones = [
        r"^Cuenta\s+Origen\s*:\s*(.+)$",
        r"^Cuenta\s+Orgen\s*:\s*(.+)$",
        r"^Cuenta\s+origen\s+(.+)$",
    ]

    for linea in lineas:

        valor = valor_despues_de_patron(
            linea,
            patrones
        )

        if valor:
            return limpiar_valor(
                valor
            )

    for i, linea in enumerate(lineas):

        if re.search(
            r"^Cuenta\s+Origen\s*:?$",
            linea,
            re.IGNORECASE
        ):

            if i + 1 < len(lineas):

                siguiente = limpiar_valor(
                    lineas[i + 1]
                )

                if siguiente:
                    return siguiente

        if re.search(
            r"^Cuenta\s+Orgen\s*:?$",
            linea,
            re.IGNORECASE
        ):

            if i + 1 < len(lineas):

                siguiente = limpiar_valor(
                    lineas[i + 1]
                )

                if siguiente:
                    return siguiente

    return None


# ============================================================
# NOMBRE DEL ORDENANTE
# ============================================================

def extraer_nombre_ordenante(datos):

    lineas = obtener_lineas(datos)

    patrones = [
        r"^Nombre\s+del\s+Ordenante\s*:\s*(.+)$",
        r"^Nombre\s+del\s+Ordenante\s+(.+)$",
        r"^Ordenante\s+(.+)$",
    ]

    for linea in lineas:

        valor = valor_despues_de_patron(
            linea,
            patrones
        )

        if valor:
            return limpiar_valor(
                valor
            )

    for i, linea in enumerate(lineas):

        if re.search(
            r"^Nombre\s+del\s+Ordenante\s*:?$",
            linea,
            re.IGNORECASE
        ):

            if i + 1 < len(lineas):

                return limpiar_valor(
                    lineas[i + 1]
                )

        if re.fullmatch(
            r"Ordenante",
            linea,
            re.IGNORECASE
        ):

            if i + 1 < len(lineas):

                return limpiar_valor(
                    lineas[i + 1]
                )

    return None


# ============================================================
# CUENTA DESTINO
# ============================================================

def extraer_cuenta_destino(datos):

    lineas = obtener_lineas(datos)

    patrones = [
        r"^Cuenta\s+Destino\s*:\s*(.+)$",
        r"^Cuenta\s+Destino\s+(.+)$",
    ]

    for i, linea in enumerate(lineas):

        valor = valor_despues_de_patron(
            linea,
            patrones
        )

        if valor:

            valor = limpiar_valor(
                valor
            )

            if i + 1 < len(lineas):

                siguiente = lineas[i + 1]

                if (
                    re.fullmatch(
                        r"[*\d\s]+",
                        siguiente
                    )
                    and not re.search(
                        r"Banco|Nombre|Concepto|Referencia|Comisi[oó]n|Clave",
                        siguiente,
                        re.IGNORECASE
                    )
                ):

                    valor = (
                        f"{valor} {siguiente}"
                        .strip()
                    )

            return valor

    return None


# ============================================================
# BANCO DESTINO
# ============================================================

def extraer_banco_destino(datos):

    lineas = obtener_lineas(datos)

    patrones = [
        r"^Banco\s+Destino\s*:\s*(.+)$",
        r"^Banco\s+Destino\s+(.+)$",
        r"^Banoo\s+Destino\s*:\s*(.+)$",
        r"^Banoo\s+Destino\s+(.+)$",
    ]

    for linea in lineas:

        valor = valor_despues_de_patron(
            linea,
            patrones
        )

        if valor:
            return limpiar_valor(
                valor
            )

    return None


# ============================================================
# BENEFICIARIO
# ============================================================

def extraer_nombre_beneficiario(datos):

    lineas = obtener_lineas(datos)

    # --------------------------------------------------------
    # FORMATO ESPECIAL BANBAJIO
    #
    # IPTVTEL COMUNICCIONES S DE
    # Nombre del Beneficiario:
    # RL DE CV
    #
    # Resultado:
    # IPTVTEL COMUNICCIONES S DE RL DE CV
    # --------------------------------------------------------

    detecciones = obtener_detecciones(
        datos
    )

    for i, deteccion in enumerate(detecciones):

        texto = normalizar_texto(
            deteccion.get(
                "texto",
                ""
            )
        )

        if not re.search(
            r"^Nombre\s+del\s+Beneficiario\s*:?\s*$",
            texto,
            re.IGNORECASE
        ):
            continue

        x_nombre = float(
            deteccion.get(
                "x",
                0
            )
        )

        y_nombre = float(
            deteccion.get(
                "y",
                0
            )
        )

        parte_superior = None
        parte_inferior = None

        # ----------------------------------------------------
        # BUSCAR PARTE SUPERIOR
        # ----------------------------------------------------

        for candidato in detecciones:

            texto_candidato = normalizar_texto(
                candidato.get(
                    "texto",
                    ""
                )
            )

            if not texto_candidato:
                continue

            if re.search(
                r"^IPTVTEL\s+COMUNICCIONES\s+S\s+DE$",
                texto_candidato,
                re.IGNORECASE
            ):

                x_candidato = float(
                    candidato.get(
                        "x",
                        0
                    )
                )

                y_candidato = float(
                    candidato.get(
                        "y",
                        0
                    )
                )

                if (
                    y_candidato < y_nombre
                    and y_nombre - y_candidato <= 40
                    and x_candidato >= x_nombre + 100
                ):
                    parte_superior = texto_candidato
                    break

        # ----------------------------------------------------
        # BUSCAR PARTE INFERIOR
        # ----------------------------------------------------

        for candidato in detecciones:

            texto_candidato = normalizar_texto(
                candidato.get(
                    "texto",
                    ""
                )
            )

            if not re.fullmatch(
                r"RL\s+DE\s+CV",
                texto_candidato,
                re.IGNORECASE
            ):
                continue

            x_candidato = float(
                candidato.get(
                    "x",
                    0
                )
            )

            y_candidato = float(
                candidato.get(
                    "y",
                    0
                )
            )

            if (
                y_candidato > y_nombre
                and y_candidato - y_nombre <= 40
                and x_candidato >= x_nombre + 100
            ):
                parte_inferior = texto_candidato
                break

        if parte_superior and parte_inferior:

            return (
                f"{parte_superior} "
                f"{parte_inferior}"
            )

    # --------------------------------------------------------
    # LÓGICA EXISTENTE
    # --------------------------------------------------------

    patrones = [
        r"^Nombre\s+del\s+Beneficiario\s*:\s*(.+)$",
        r"^Nombre\s+del\s+Beneficiario\s+(.+)$",
        r"^Nombre\s+deL\s+Beneficlarlo\s*:\s*(.+)$",
        r"^Nombre\s+deL\s+Beneficlarlo\s+(.+)$",
        r"^Beneficiario\s+(.+)$",
    ]

    for linea in lineas:

        valor = valor_despues_de_patron(
            linea,
            patrones
        )

        if valor:
            return limpiar_valor(
                valor
            )

    for i, linea in enumerate(lineas):

        if re.search(
            r"^Nombre\s+del\s+Beneficiario\s*:?\s*$",
            linea,
            re.IGNORECASE
        ):

            if i + 1 < len(lineas):

                return limpiar_valor(
                    lineas[i + 1]
                )

    return None


# ============================================================
# CONCEPTO
# ============================================================

def extraer_concepto(datos):

    lineas = obtener_lineas(datos)

    patrones = [
        r"^Concepto\s+de\s+Pago\s*:\s*(.+)$",
        r"^Concepto\s+de\s+Pago\s+(.+)$",
        r"^Conoepto\s+de\s+Pago\s*:\s*(.+)$",
        r"^Conoepto\s+de\s+Pago\s+(.+)$",
        r"^Concepto\s+(.+)$",
    ]

    for linea in lineas:

        valor = valor_despues_de_patron(
            linea,
            patrones
        )

        if valor:
            return limpiar_valor(
                valor
            )

    return None


# ============================================================
# MONTO
# ============================================================

def extraer_monto(datos):

    texto_completo = obtener_texto_completo(
        datos
    )

    patrones = [
        r"(?:Importe)\s*:\s*\$\s*([\d,]+\.\d{2})",
        r"(?:Importe)\s+\$\s*([\d,]+\.\d{2})",
        r"(?:Importe)\s*:\s*\$\s*([\d,]+)",
        r"(?:Importe)\s+\$\s*([\d,]+)",
    ]

    for patron in patrones:

        resultado = re.search(
            patron,
            texto_completo,
            re.IGNORECASE
        )

        if resultado:

            numero = (
                resultado
                .group(1)
                .replace(",", "")
            )

            return f"${numero}"

    return None


# ============================================================
# REFERENCIA
# ============================================================

def extraer_referencia(datos):

    lineas = obtener_lineas(datos)

    patrones = [
        r"^Referencia\s*:\s*(.+)$",
        r"^Referencia\s+(.+)$",
    ]

    for linea in lineas:

        valor = valor_despues_de_patron(
            linea,
            patrones
        )

        if valor:
            return limpiar_valor(
                valor
            )

    return None


# ============================================================
# CLAVE DE RASTREO
# ============================================================

def extraer_clave_rastreo(datos):

    lineas = obtener_lineas(datos)

    # --------------------------------------------------------
    # PRIMERO: buscar la clave directamente en una línea
    # etiquetada.
    #
    # Ejemplo image_680:
    #
    # Clave de Rastreo: BB2307382020743
    #
    # Existe otra detección separada:
    #
    # ?
    #
    # El "?" NO pertenece a la clave.
    # --------------------------------------------------------

    patrones = [
        r"^Clave\s+de\s+Rastreo\s*:\s*([A-Za-z0-9]+)",
        r"^Clave\s+de\s+Rastreo\s+([A-Za-z0-9]+)",
        r"^Clave\s+de\s+rastreo\s+([A-Za-z0-9]+)",
    ]

    for linea in lineas:

        valor = valor_despues_de_patron(
            linea,
            patrones
        )

        if valor:

            resultado = re.match(
                r"^[A-Za-z0-9]+",
                valor
            )

            if resultado:
                return resultado.group(0)

    # --------------------------------------------------------
    # RESPALDO: si la etiqueta y el valor vienen separados
    # --------------------------------------------------------

    for i, linea in enumerate(lineas):

        if re.search(
            r"^Clave\s+de\s+Rastreo\s*:?\s*$",
            linea,
            re.IGNORECASE
        ):

            if i + 1 < len(lineas):

                siguiente = limpiar_valor(
                    lineas[i + 1]
                )

                if siguiente:

                    resultado = re.match(
                        r"^[A-Za-z0-9]+",
                        siguiente
                    )

                    if resultado:
                        return resultado.group(0)

    return None


# ============================================================
# EXTRACTOR PRINCIPAL
# ============================================================

class BanBajioExtractor:

    def __init__(self):
        pass

    def extraer(self, datos):

        campos = {
            "fecha": extraer_fecha(datos),
            "cuenta_origen": extraer_cuenta_origen(datos),
            "nombre_ordenante": extraer_nombre_ordenante(datos),
            "cuenta_destino": extraer_cuenta_destino(datos),
            "banco_destino": extraer_banco_destino(datos),
            "nombre_beneficiario": extraer_nombre_beneficiario(datos),
            "concepto": extraer_concepto(datos),
            "monto": extraer_monto(datos),
            "referencia": extraer_referencia(datos),
            "clave_rastreo": extraer_clave_rastreo(datos),
        }

        return {
            "banco": BANCO,
            "campos": campos
        }


# ============================================================
# FACTORY
# ============================================================

def crear_extractor():
    return BanBajioExtractor()


# ============================================================
# FUNCION PUBLICA
# ============================================================

def extraer(datos):

    extractor = BanBajioExtractor()

    return extractor.extraer(datos)