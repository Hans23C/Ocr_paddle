import re


# ============================================================
# UTILIDADES
# ============================================================

def obtener_detecciones(datos_json):
    return datos_json.get("detecciones", [])


def obtener_texto(deteccion):
    return str(deteccion.get("texto", "")).strip()


def obtener_confianza(deteccion):
    try:
        return float(deteccion.get("confianza", 0.0))
    except (TypeError, ValueError):
        return 0.0


def obtener_x(deteccion):
    try:
        return float(deteccion.get("x", 0.0))
    except (TypeError, ValueError):
        return 0.0


def obtener_y(deteccion):
    try:
        return float(deteccion.get("y", 0.0))
    except (TypeError, ValueError):
        return 0.0


def limpiar_texto(texto):
    return re.sub(r"\s+", " ", str(texto)).strip()


# ============================================================
# BUSQUEDAS POR POSICION
# ============================================================

def buscar_valor_a_la_derecha(detecciones, etiqueta, tolerancia_y=35):
    """
    Busca un valor que aparezca a la derecha de una etiqueta
    y aproximadamente en la misma línea.
    """

    etiqueta = etiqueta.lower()

    for i, det in enumerate(detecciones):

        texto_etiqueta = limpiar_texto(obtener_texto(det)).lower()

        if texto_etiqueta != etiqueta:
            continue

        x_etiqueta = obtener_x(det)
        y_etiqueta = obtener_y(det)

        candidatos = []

        for j, candidato in enumerate(detecciones):

            if i == j:
                continue

            texto = limpiar_texto(obtener_texto(candidato))

            if not texto:
                continue

            x = obtener_x(candidato)
            y = obtener_y(candidato)

            # Debe estar a la derecha
            if x <= x_etiqueta:
                continue

            # Debe estar aproximadamente en la misma línea
            diferencia_y = abs(y - y_etiqueta)

            if diferencia_y <= tolerancia_y:
                candidatos.append(candidato)

        if candidatos:
            # El más cercano verticalmente
            candidatos.sort(
                key=lambda d: (
                    abs(obtener_y(d) - y_etiqueta),
                    obtener_x(d)
                )
            )

            return candidatos[0]

    return None


def buscar_valor_debajo(detecciones, etiqueta, max_y=100):
    """
    Busca un valor debajo de una etiqueta.
    """

    etiqueta = etiqueta.lower()

    for i, det in enumerate(detecciones):

        texto_etiqueta = limpiar_texto(obtener_texto(det)).lower()

        if texto_etiqueta != etiqueta:
            continue

        x_etiqueta = obtener_x(det)
        y_etiqueta = obtener_y(det)

        candidatos = []

        for j, candidato in enumerate(detecciones):

            if i == j:
                continue

            texto = limpiar_texto(obtener_texto(candidato))

            if not texto:
                continue

            x = obtener_x(candidato)
            y = obtener_y(candidato)

            # Debe estar debajo
            if y <= y_etiqueta:
                continue

            diferencia_y = y - y_etiqueta

            if diferencia_y > max_y:
                continue

            # Debe estar razonablemente alineado
            diferencia_x = abs(x - x_etiqueta)

            if diferencia_x <= 80:
                candidatos.append(candidato)

        if candidatos:
            candidatos.sort(
                key=lambda d: obtener_y(d)
            )

            return candidatos[0]

    return None


def buscar_deteccion_por_texto(detecciones, patron):
    """
    Busca una detección cuyo texto coincida con una expresión regular.
    """

    regex = re.compile(patron, re.IGNORECASE)

    for det in detecciones:
        texto = limpiar_texto(obtener_texto(det))

        if regex.search(texto):
            return det

    return None


# ============================================================
# CLABE
# ============================================================

def limpiar_clabe(texto):
    if not texto:
        return None

    texto = limpiar_texto(texto)

    # El OCR normalmente devuelve:
    # ****1311
    # ****0978
    #
    # Se conserva el formato detectado.
    match = re.search(r"\*{2,}\s*\d{4}$", texto)

    if match:
        return match.group(0)

    return None


def buscar_clabe(detecciones, indice_cuenta_clabe):
    """
    STORI tiene dos etiquetas 'Cuenta CLABE'.

    La primera corresponde a la cuenta destino.
    La segunda corresponde a la cuenta origen.

    El valor aparece a la derecha de la etiqueta.
    """

    etiquetas = []

    for i, det in enumerate(detecciones):

        texto = limpiar_texto(obtener_texto(det)).lower()

        if texto == "cuenta clabe":
            etiquetas.append((i, det))

    if indice_cuenta_clabe >= len(etiquetas):
        return None

    _, etiqueta = etiquetas[indice_cuenta_clabe]

    x_etiqueta = obtener_x(etiqueta)
    y_etiqueta = obtener_y(etiqueta)

    candidatos = []

    for det in detecciones:

        texto = limpiar_texto(obtener_texto(det))

        if not texto:
            continue

        clabe = limpiar_clabe(texto)

        if not clabe:
            continue

        x = obtener_x(det)
        y = obtener_y(det)

        # La CLABE está a la derecha
        if x <= x_etiqueta:
            continue

        # Aproximadamente en la misma línea
        if abs(y - y_etiqueta) <= 35:
            candidatos.append(det)

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda d: abs(obtener_y(d) - y_etiqueta)
    )

    return candidatos[0]


# ============================================================
# MONTO
# ============================================================

def extraer_monto(detecciones):

    for det in detecciones:

        texto = limpiar_texto(obtener_texto(det))

        match = re.search(
            r"-?\$\s*[\d,]+(?:\.\d{2})?",
            texto
        )

        if match:

            monto = match.group(0)

            # El comprobante muestra:
            # -$300.00
            #
            # El resultado esperado es:
            # $300.00
            monto = monto.replace("-", "")
            monto = monto.replace(" ", "")

            return {
                "valor": monto,
                "metodo": "patron_monto",
                "confianza": obtener_confianza(det)
            }

    return {
        "valor": None,
        "metodo": "no_encontrado",
        "confianza": 0.0
    }


# ============================================================
# FECHA
# ============================================================

def extraer_fecha(detecciones):

    patron = (
        r"\d{1,2}\s+"
        r"(?:ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)"
        r"\s+\d{4}\s+"
        r"\d{2}:\d{2}:\d{2}\s+h"
    )

    det = buscar_deteccion_por_texto(
        detecciones,
        patron
    )

    if det:

        texto = limpiar_texto(obtener_texto(det))

        return {
            "valor": texto,
            "metodo": "patron_fecha",
            "confianza": obtener_confianza(det)
        }

    return {
        "valor": None,
        "metodo": "no_encontrado",
        "confianza": 0.0
    }


# ============================================================
# REFERENCIA NUMERICA
# ============================================================

def extraer_referencia_numerica(detecciones):

    for i, det in enumerate(detecciones):

        texto = limpiar_texto(obtener_texto(det)).lower()

        if texto != "referencia numérica":
            continue

        y_etiqueta = obtener_y(det)

        candidatos = []

        for candidato in detecciones:

            texto_valor = limpiar_texto(
                obtener_texto(candidato)
            )

            if not re.fullmatch(r"\d{6}", texto_valor):
                continue

            y = obtener_y(candidato)

            if y <= y_etiqueta:
                continue

            diferencia_y = y - y_etiqueta

            if diferencia_y <= 80:
                candidatos.append(candidato)

        if candidatos:

            candidatos.sort(
                key=lambda d: obtener_y(d)
            )

            candidato = candidatos[0]

            return {
                "valor": limpiar_texto(
                    obtener_texto(candidato)
                ),
                "metodo": "etiqueta_referencia_numerica",
                "confianza": obtener_confianza(candidato)
            }

    return {
        "valor": None,
        "metodo": "no_encontrado",
        "confianza": 0.0
    }


# ============================================================
# REFERENCIA INTERNA
# ============================================================

def extraer_referencia_interna(detecciones):

    patron = (
        r"^[0-9a-fA-F]{8}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{12}$"
    )

    det = buscar_deteccion_por_texto(
        detecciones,
        patron
    )

    if det:

        return {
            "valor": limpiar_texto(
                obtener_texto(det)
            ),
            "metodo": "etiqueta_referencia_interna",
            "confianza": obtener_confianza(det)
        }

    return {
        "valor": None,
        "metodo": "no_encontrado",
        "confianza": 0.0
    }


# ============================================================
# CLAVE DE RASTREO
# ============================================================

def extraer_clave_rastreo(detecciones):

    for i, det in enumerate(detecciones):

        texto = limpiar_texto(obtener_texto(det)).lower()

        if texto != "clave de rastreo":
            continue

        y_etiqueta = obtener_y(det)

        candidatos = []

        for candidato in detecciones:

            texto_valor = limpiar_texto(
                obtener_texto(candidato)
            )

            if not texto_valor:
                continue

            # Las claves de rastreo STORI comienzan con SAC
            if not texto_valor.upper().startswith("SAC"):
                continue

            y = obtener_y(candidato)

            if y <= y_etiqueta:
                continue

            if y - y_etiqueta <= 80:
                candidatos.append(candidato)

        if candidatos:

            candidatos.sort(
                key=lambda d: obtener_y(d)
            )

            candidato = candidatos[0]

            return {
                "valor": limpiar_texto(
                    obtener_texto(candidato)
                ),
                "metodo": "etiqueta_clave_rastreo",
                "confianza": obtener_confianza(candidato)
            }

    return {
        "valor": None,
        "metodo": "no_encontrado",
        "confianza": 0.0
    }


# ============================================================
# NUMERO DE FOLIO
# ============================================================

def extraer_numero_folio(detecciones):

    for i, det in enumerate(detecciones):

        texto = limpiar_texto(obtener_texto(det)).lower()

        if texto != "número de folio":
            continue

        y_etiqueta = obtener_y(det)

        candidatos = []

        for candidato in detecciones:

            texto_valor = limpiar_texto(
                obtener_texto(candidato)
            )

            if not re.fullmatch(r"\d{20,}", texto_valor):
                continue

            y = obtener_y(candidato)

            if y <= y_etiqueta:
                continue

            if y - y_etiqueta <= 80:
                candidatos.append(candidato)

        if candidatos:

            candidatos.sort(
                key=lambda d: obtener_y(d)
            )

            candidato = candidatos[0]

            return {
                "valor": limpiar_texto(
                    obtener_texto(candidato)
                ),
                "metodo": "etiqueta_numero_folio",
                "confianza": obtener_confianza(candidato)
            }

    return {
        "valor": None,
        "metodo": "no_encontrado",
        "confianza": 0.0
    }


# ============================================================
# EXTRACTOR PRINCIPAL
# ============================================================

def extraer(datos_json):

    detecciones = obtener_detecciones(datos_json)

    campos = {}

    # --------------------------------------------------------
    # BANCO
    # --------------------------------------------------------

    campos["banco"] = {
        "valor": "STORI",
        "metodo": "banco_configurado",
        "confianza": 1.0
    }

    # --------------------------------------------------------
    # FECHA
    # --------------------------------------------------------

    campos["fecha"] = extraer_fecha(detecciones)

    # --------------------------------------------------------
    # MONTO
    # --------------------------------------------------------

    campos["monto"] = extraer_monto(detecciones)

    # --------------------------------------------------------
    # DESTINATARIO
    # --------------------------------------------------------

    det = buscar_valor_a_la_derecha(
        detecciones,
        "Destinatario"
    )

    if det:
        campos["destinatario"] = {
            "valor": limpiar_texto(
                obtener_texto(det)
            ),
            "metodo": "etiqueta_destinatario",
            "confianza": obtener_confianza(det)
        }
    else:
        campos["destinatario"] = {
            "valor": None,
            "metodo": "no_encontrado",
            "confianza": 0.0
        }

    # --------------------------------------------------------
    # CONCEPTO
    # --------------------------------------------------------

    det = buscar_valor_a_la_derecha(
        detecciones,
        "Concepto"
    )

    if det:
        campos["concepto"] = {
            "valor": limpiar_texto(
                obtener_texto(det)
            ),
            "metodo": "etiqueta_concepto",
            "confianza": obtener_confianza(det)
        }
    else:
        campos["concepto"] = {
            "valor": None,
            "metodo": "no_encontrado",
            "confianza": 0.0
        }

    # --------------------------------------------------------
    # ENTIDAD RECEPTORA
    # --------------------------------------------------------

    det = buscar_valor_a_la_derecha(
        detecciones,
        "Entidad receptora"
    )

    if det:
        campos["entidad_receptora"] = {
            "valor": limpiar_texto(
                obtener_texto(det)
            ),
            "metodo": "etiqueta_entidad_receptora",
            "confianza": obtener_confianza(det)
        }
    else:
        campos["entidad_receptora"] = {
            "valor": None,
            "metodo": "no_encontrado",
            "confianza": 0.0
        }

    # --------------------------------------------------------
    # CLABE DESTINO
    # --------------------------------------------------------

    det = buscar_clabe(
        detecciones,
        0
    )

    if det:
        campos["cuenta_clabe_destino"] = {
            "valor": limpiar_clabe(
                obtener_texto(det)
            ),
            "metodo": "etiqueta_cuenta_clabe_destino",
            "confianza": obtener_confianza(det)
        }
    else:
        campos["cuenta_clabe_destino"] = {
            "valor": None,
            "metodo": "no_encontrado",
            "confianza": 0.0
        }

    # --------------------------------------------------------
    # TITULAR
    # --------------------------------------------------------

    det = buscar_valor_a_la_derecha(
        detecciones,
        "Titular"
    )

    if det:
        campos["titular"] = {
            "valor": limpiar_texto(
                obtener_texto(det)
            ),
            "metodo": "etiqueta_titular",
            "confianza": obtener_confianza(det)
        }
    else:
        campos["titular"] = {
            "valor": None,
            "metodo": "no_encontrado",
            "confianza": 0.0
        }

    # --------------------------------------------------------
    # ENTIDAD EMISORA
    # --------------------------------------------------------

    det = buscar_valor_a_la_derecha(
        detecciones,
        "Entidad emisora"
    )

    if det:
        campos["entidad_emisora"] = {
            "valor": limpiar_texto(
                obtener_texto(det)
            ),
            "metodo": "etiqueta_entidad_emisora",
            "confianza": obtener_confianza(det)
        }
    else:
        campos["entidad_emisora"] = {
            "valor": None,
            "metodo": "no_encontrado",
            "confianza": 0.0
        }

    # --------------------------------------------------------
    # CLABE ORIGEN
    # --------------------------------------------------------

    det = buscar_clabe(
        detecciones,
        1
    )

    if det:
        campos["cuenta_clabe_origen"] = {
            "valor": limpiar_clabe(
                obtener_texto(det)
            ),
            "metodo": "etiqueta_cuenta_clabe_origen",
            "confianza": obtener_confianza(det)
        }
    else:
        campos["cuenta_clabe_origen"] = {
            "valor": None,
            "metodo": "no_encontrado",
            "confianza": 0.0
        }

    # --------------------------------------------------------
    # REFERENCIA NUMERICA
    # --------------------------------------------------------

    campos["referencia_numerica"] = (
        extraer_referencia_numerica(detecciones)
    )

    # --------------------------------------------------------
    # REFERENCIA INTERNA
    # --------------------------------------------------------

    campos["referencia_interna"] = (
        extraer_referencia_interna(detecciones)
    )

    # --------------------------------------------------------
    # CLAVE DE RASTREO
    # --------------------------------------------------------

    campos["clave_rastreo"] = (
        extraer_clave_rastreo(detecciones)
    )

    # --------------------------------------------------------
    # NUMERO DE FOLIO
    # --------------------------------------------------------

    campos["numero_folio"] = (
        extraer_numero_folio(detecciones)
    )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    return {
        "banco": "STORI",
        "tipo": "transferencia",
        "campos": campos
    }


# ============================================================
# CLASE
# ============================================================

class StoriExtractor:

    def extraer(self, datos_json):
        return extraer(datos_json)

    def extract(self, datos_json):
        return extraer(datos_json)

    def extraer_datos(self, datos_json):
        return extraer(datos_json)


# ============================================================
# FACTORY
# ============================================================

def crear_extractor():
    return StoriExtractor()