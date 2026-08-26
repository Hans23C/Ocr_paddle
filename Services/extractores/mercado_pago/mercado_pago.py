import re
import unicodedata


# ============================================================
# CONFIGURACIÓN
# ============================================================

BANCO = "MERCADO PAGO"

CAMPOS_TRANSFERENCIA = [
    "banco",
    "fecha",
    "monto",
    "titular_cuenta_ordenante",
    "clabe_tarjeta_celular_ordenante",
    "titular_cuenta_beneficiario",
    "banco_beneficiario",
    "clabe_tarjeta_celular_beneficiario",
    "numero_referencia",
    "concepto",
]

CAMPOS_CEP = [
    "banco",
    "numero_referencia",
    "clave_rastreo",
    "institucion_emisora",
    "institucion_receptora",
    "estado_banxico",
    "fecha_hora_recepcion",
    "fecha_hora_procesamiento",
    "cuenta_beneficiaria",
    "monto",
]


# ============================================================
# UTILIDADES
# ============================================================

def normalizar_texto(texto):
    if texto is None:
        return ""

    texto = str(texto).replace("\n", " ")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def normalizar_busqueda(texto):
    texto = normalizar_texto(texto)

    if not texto:
        return ""

    # Reparar mojibake cuando exista.
    if any(x in texto for x in ("Ã", "Â", "â")):
        try:
            texto = texto.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

    texto = unicodedata.normalize("NFD", texto)

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
# LÍNEAS
# ============================================================

def obtener_lineas(datos):
    if not isinstance(datos, dict):
        return []

    lineas = datos.get("lineas", [])

    if isinstance(lineas, list):
        resultado = [
            normalizar_texto(linea)
            for linea in lineas
            if normalizar_texto(linea)
        ]

        if resultado:
            return resultado

    detecciones = datos.get("detecciones", [])

    resultado = []

    if isinstance(detecciones, list):
        for deteccion in detecciones:

            if not isinstance(deteccion, dict):
                continue

            texto = normalizar_texto(
                deteccion.get("texto", "")
            )

            if texto:
                resultado.append(texto)

    return resultado


# ============================================================
# BÚSQUEDA DE ETIQUETAS
# ============================================================

def buscar_etiqueta(
    lineas,
    etiquetas,
    buscar_siguiente=True
):
    etiquetas_norm = [
        normalizar_busqueda(etiqueta)
        for etiqueta in etiquetas
    ]

    for indice, linea in enumerate(lineas):

        linea_norm = normalizar_busqueda(linea)

        for etiqueta_norm in etiquetas_norm:

            if not etiqueta_norm:
                continue

            if linea_norm.startswith(etiqueta_norm):

                # La etiqueta está dentro de la línea.
                valor = linea[
                    len(etiqueta_norm):
                ]

                valor = valor.lstrip(
                    " :.-"
                )

                if valor:
                    return normalizar_texto(valor)

                # Valor en la siguiente línea.
                if (
                    buscar_siguiente
                    and indice + 1 < len(lineas)
                ):
                    siguiente = normalizar_texto(
                        lineas[indice + 1]
                    )

                    if siguiente:
                        return siguiente

    return None


# ============================================================
# BUSCAR TEXTO EXACTO / CONTENIDO
# ============================================================

def contiene_etiqueta(
    linea,
    etiqueta
):
    return normalizar_busqueda(
        etiqueta
    ) in normalizar_busqueda(
        linea
    )


# ============================================================
# FECHA
# ============================================================

def extraer_fecha(lineas):

    patrones = [
        r"\d{1,2}\s+de\s+[A-Za-zÁÉÍÓÚáéíóúÑñ]+\s+de\s+\d{4}(?:.*)?",
        r"\d{1,2}/[A-Za-zÁÉÍÓÚáéíóúÑñ]+/\d{4}(?:.*)?",
        r"\d{1,2}/[A-Za-zÁÉÍÓÚáéíóúÑñ]+\s*-\s*.*",
        r"\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}(?::\d{2})?",
    ]

    for linea in lineas:

        for patron in patrones:

            if re.search(
                patron,
                linea,
                flags=re.IGNORECASE
            ):
                return linea

    return None


# ============================================================
# MONTO
# ============================================================

def extraer_monto(lineas):

    # Primero buscamos una línea que sea claramente un monto.
    for linea in lineas:

        texto = normalizar_texto(linea)

        if re.fullmatch(
            r"\$\s*[\d,]+(?:\.\d{1,2})?",
            texto
        ):
            return texto

    # Después buscamos montos con contexto explícito.
    for linea in lineas:

        texto_norm = normalizar_busqueda(linea)

        if (
            "monto" in texto_norm
            or "importe" in texto_norm
            or "total" in texto_norm
        ):

            match = re.search(
                r"\$\s*[\d,]+(?:\.\d{1,2})?",
                linea
            )

            if match:
                return match.group(0).strip()

    # Último recurso: monto que empieza con $.
    for linea in lineas:

        if linea.strip().startswith("$"):

            match = re.search(
                r"\$\s*[\d,]+(?:\.\d{1,2})?",
                linea
            )

            if match:
                return match.group(0).strip()

    return None


# ============================================================
# DATOS BANCARIOS
# ============================================================

def extraer_dato_bancario(
    lineas,
    inicio,
    limite=8
):
    """
    Busca CLABE o número de tarjeta/cuenta después
    de una sección determinada.
    """

    fin = min(
        inicio + limite,
        len(lineas)
    )

    for indice in range(
        inicio,
        fin
    ):

        linea = lineas[indice]
        linea_norm = normalizar_busqueda(linea)

        if "clabe" in linea_norm:

            match = re.search(
                r"clabe\s*:?\s*(.+)",
                linea,
                flags=re.IGNORECASE
            )

            if match:
                valor = normalizar_texto(
                    match.group(1)
                )

                if valor:
                    return valor

            if indice + 1 < len(lineas):
                siguiente = normalizar_texto(
                    lineas[indice + 1]
                )

                if siguiente:
                    return siguiente

        if (
            "numero de tarjeta" in linea_norm
            or "número de tarjeta" in linea_norm
        ):

            match = re.search(
                r"n[uú]mero de tarjeta\s*:?\s*(.+)",
                linea,
                flags=re.IGNORECASE
            )

            if match:
                valor = normalizar_texto(
                    match.group(1)
                )

                if valor:
                    return valor

            if indice + 1 < len(lineas):
                siguiente = normalizar_texto(
                    lineas[indice + 1]
                )

                if siguiente:
                    return siguiente

    return None


# ============================================================
# ORDENANTE
# ============================================================

def extraer_ordenante(lineas):

    titular = None
    cuenta = None

    for indice, linea in enumerate(lineas):

        linea_norm = normalizar_busqueda(linea)

        # Caso: "De"
        if linea_norm == "de":

            if indice + 1 < len(lineas):

                candidato = normalizar_texto(
                    lineas[indice + 1]
                )

                candidato_norm = normalizar_busqueda(
                    candidato
                )

                if (
                    candidato
                    and candidato_norm not in (
                        "mercado pago",
                        "clabe",
                        "numero de tarjeta",
                        "numero de cuenta",
                    )
                    and not candidato_norm.startswith(
                        "clabe"
                    )
                ):
                    titular = candidato

            cuenta = extraer_dato_bancario(
                lineas,
                indice + 1,
                limite=8
            )

            return titular, cuenta

        # Caso OCR: "De Nombre..."
        if linea_norm.startswith("de "):

            candidato = linea[
                len("de "):
            ].strip()

            if candidato:
                titular = candidato

            cuenta = extraer_dato_bancario(
                lineas,
                indice + 1,
                limite=8
            )

            return titular, cuenta

    return titular, cuenta


# ============================================================
# BENEFICIARIO
# ============================================================

def extraer_beneficiario(lineas):

    titular = None
    banco = None
    cuenta = None

    for indice, linea in enumerate(lineas):

        linea_norm = normalizar_busqueda(linea)

        posicion_para = None
        candidato = None

        # --------------------------------------------
        # "Para"
        # --------------------------------------------

        if linea_norm == "para":

            posicion_para = indice

            if indice + 1 < len(lineas):
                candidato = normalizar_texto(
                    lineas[indice + 1]
                )

        # --------------------------------------------
        # "... Para"
        # --------------------------------------------

        elif re.search(
            r"\bpara\b",
            linea_norm
        ):

            posicion_para = indice

            match = re.search(
                r"\bpara\b\s*(.*)$",
                linea,
                flags=re.IGNORECASE
            )

            if match:
                candidato = normalizar_texto(
                    match.group(1)
                )

        if posicion_para is None:
            continue

        # --------------------------------------------
        # BENEFICIARIO
        # --------------------------------------------

        if candidato:

            candidato_norm = normalizar_busqueda(
                candidato
            )

            if candidato_norm != "hsbc":
                titular = candidato

        # --------------------------------------------
        # DATOS POSTERIORES
        # --------------------------------------------

        limite = min(
            posicion_para + 10,
            len(lineas)
        )

        for j in range(
            posicion_para + 1,
            limite
        ):

            texto = lineas[j]
            texto_norm = normalizar_busqueda(
                texto
            )

            if texto_norm == "hsbc":
                banco = "HSBC"

            # No aceptar cualquier texto como cuenta.
            if (
                "clabe" in texto_norm
                or "numero de tarjeta" in texto_norm
                or "número de tarjeta" in texto_norm
            ):

                cuenta = extraer_dato_bancario(
                    lineas,
                    j,
                    limite=3
                )

                if cuenta:
                    break

        return titular, banco, cuenta

    return titular, banco, cuenta


# ============================================================
# REFERENCIA
# ============================================================

def extraer_numero_referencia(lineas):

    valor = buscar_etiqueta(
        lineas,
        [
            "Número de referencia",
            "Numero de referencia",
        ]
    )

    if not valor:
        return None

    match = re.search(
        r"\b\d+\b",
        valor
    )

    if not match:
        return None

    return match.group(0)


# ============================================================
# CONCEPTO
# ============================================================

def extraer_concepto(lineas):

    return buscar_etiqueta(
        lineas,
        ["Concepto"]
    )


# ============================================================
# CEP
# ============================================================

def es_cep(lineas):

    texto = " ".join(
        normalizar_busqueda(linea)
        for linea in lineas
    )

    return (
        "institucion emisora del pago" in texto
        or
        "institucion receptora del pago" in texto
        or
        "estado del pago en banxico" in texto
    )


def extraer_cep(lineas):

    referencia = buscar_etiqueta(
        lineas,
        [
            "Número de Referencia",
            "Numero de Referencia",
        ]
    )

    clave_rastreo = buscar_etiqueta(
        lineas,
        [
            "Clave de Rastreo",
            "Clave de rastreo",
        ]
    )

    institucion_emisora = buscar_etiqueta(
        lineas,
        [
            "Institución emisora del pago",
            "Institucion emisora del pago",
        ]
    )

    institucion_receptora = buscar_etiqueta(
        lineas,
        [
            "Institución receptora del pago",
            "Institucion receptora del pago",
        ]
    )

    estado = buscar_etiqueta(
        lineas,
        [
            "Estado del pago en Banxico",
            "Estado del pago en BANXICO",
        ]
    )

    fecha_recepcion = buscar_etiqueta(
        lineas,
        [
            "Fecha y hora de recepción",
            "Fecha y hora de recepcion",
        ]
    )

    fecha_procesamiento = buscar_etiqueta(
        lineas,
        [
            "Fecha y hora de procesamiento",
            "Fecha y hora de procesamiento",
        ]
    )

    cuenta_beneficiaria = buscar_etiqueta(
        lineas,
        [
            "Cuenta Beneficiaria",
            "Cuenta beneficiaria",
        ]
    )

    monto = buscar_etiqueta(
        lineas,
        [
            "Monto",
        ]
    )

    # --------------------------------------------
    # Limpiar referencia
    # --------------------------------------------

    if referencia:

        match = re.search(
            r"\b\d+\b",
            referencia
        )

        referencia = (
            match.group(0)
            if match
            else None
        )

    # --------------------------------------------
    # Limpiar monto
    # --------------------------------------------

    if monto:

        match = re.search(
            r"\$?\s*[\d,]+(?:\.\d{1,2})?",
            monto
        )

        monto = (
            match.group(0).strip()
            if match
            else None
        )

    return {
        "banco": campo_encontrado(
            BANCO
        ),

        "numero_referencia":
            campo_encontrado(
                referencia
            ),

        "clave_rastreo":
            campo_encontrado(
                clave_rastreo
            ),

        "institucion_emisora":
            campo_encontrado(
                institucion_emisora
            ),

        "institucion_receptora":
            campo_encontrado(
                institucion_receptora
            ),

        "estado_banxico":
            campo_encontrado(
                estado
            ),

        "fecha_hora_recepcion":
            campo_encontrado(
                fecha_recepcion
            ),

        "fecha_hora_procesamiento":
            campo_encontrado(
                fecha_procesamiento
            ),

        "cuenta_beneficiaria":
            campo_encontrado(
                cuenta_beneficiaria
            ),

        "monto":
            campo_encontrado(
                monto
            ),
    }


# ============================================================
# TRANSFERENCIA
# ============================================================

def extraer_transferencia(lineas):

    titular_ordenante, cuenta_ordenante = (
        extraer_ordenante(lineas)
    )

    (
        titular_beneficiario,
        banco_beneficiario,
        cuenta_beneficiario
    ) = extraer_beneficiario(lineas)

    referencia = extraer_numero_referencia(
        lineas
    )

    concepto = extraer_concepto(
        lineas
    )

    return {
        "banco": campo_encontrado(
            BANCO
        ),

        "fecha": campo_encontrado(
            extraer_fecha(lineas)
        ),

        "monto": campo_encontrado(
            extraer_monto(lineas)
        ),

        "titular_cuenta_ordenante":
            campo_encontrado(
                titular_ordenante,
                "BBOX_DEBAJO"
            ),

        "clabe_tarjeta_celular_ordenante":
            campo_encontrado(
                cuenta_ordenante
            ),

        "titular_cuenta_beneficiario":
            campo_encontrado(
                titular_beneficiario,
                "BBOX_DEBAJO"
            ),

        "banco_beneficiario":
            campo_encontrado(
                banco_beneficiario,
                "BBOX_DEBAJO"
            ),

        "clabe_tarjeta_celular_beneficiario":
            campo_encontrado(
                cuenta_beneficiario
            ),

        "numero_referencia":
            campo_encontrado(
                referencia
            ),

        "concepto":
            campo_encontrado(
                concepto
            ),
    }


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def extraer(datos_json):

    lineas = obtener_lineas(
        datos_json
    )

    if es_cep(lineas):

        return {
            "banco": BANCO,
            "tipo": "CEP_MERCADO_PAGO",
            "campos": extraer_cep(lineas),
        }

    return {
        "banco": BANCO,
        "tipo": "TRANSFERENCIA_MERCADO_PAGO",
        "campos": extraer_transferencia(
            lineas
        ),
    }


# ============================================================
# COMPATIBILIDAD
# ============================================================

class MercadoPagoExtractor:

    def extraer(self, datos_json):
        return extraer(datos_json)

    def extract(self, datos_json):
        return extraer(datos_json)

    def extraer_datos(self, datos_json):
        return extraer(datos_json)


def crear_extractor():
    return MercadoPagoExtractor()