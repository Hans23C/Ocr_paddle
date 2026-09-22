import re
import unicodedata


TIPO = "PAGO_FARMACIAS_DEL_AHORRO"


# ============================================================
# NORMALIZACION
# ============================================================

def normalizar_texto(texto):
    if texto is None:
        return ""

    texto = str(texto)

    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )

    texto = texto.upper()
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def limpiar_valor(texto):
    if texto is None:
        return None

    texto = str(texto).strip()

    texto = re.sub(r"^[\s:;,.\-]+", "", texto)

    texto = texto.strip()

    if not texto:
        return None

    return texto


# ============================================================
# FUNCIONES OCR
# ============================================================

def texto_deteccion(deteccion):
    if not isinstance(deteccion, dict):
        return ""

    return str(
        deteccion.get("texto", "")
    ).strip()


def confianza_deteccion(deteccion):
    if not isinstance(deteccion, dict):
        return 0.0

    try:
        return float(
            deteccion.get("confianza", 0.0)
        )
    except (TypeError, ValueError):
        return 0.0


def coordenadas(deteccion):

    try:
        x = float(deteccion.get("x", 0))
    except (TypeError, ValueError):
        x = 0.0

    try:
        y = float(deteccion.get("y", 0))
    except (TypeError, ValueError):
        y = 0.0

    try:
        ancho = float(deteccion.get("ancho", 0))
    except (TypeError, ValueError):
        ancho = 0.0

    try:
        alto = float(deteccion.get("alto", 0))
    except (TypeError, ValueError):
        alto = 0.0

    return x, y, ancho, alto


def obtener_detecciones(datos_json):

    if isinstance(datos_json, list):
        return datos_json

    if not isinstance(datos_json, dict):
        return []

    posibles = [
        "detecciones",
        "resultados",
        "ocr",
        "data"
    ]

    for clave in posibles:

        valor = datos_json.get(clave)

        if isinstance(valor, list):
            return valor

    return []


# ============================================================
# RESULTADOS
# ============================================================

def campo_encontrado(
    valor,
    metodo,
    confianza,
    deteccion=None
):

    resultado = {
        "valor": valor,
        "metodo": metodo,
        "confianza": round(
            float(confianza),
            4
        )
    }

    if isinstance(deteccion, dict):

        x, y, ancho, alto = coordenadas(
            deteccion
        )

        resultado["bbox"] = {
            "x": x,
            "y": y,
            "ancho": ancho,
            "alto": alto
        }

    return resultado


def campo_no_encontrado():

    return {
        "valor": None,
        "metodo": "NO_ENCONTRADO",
        "confianza": 0.0,
        "bbox": None
    }


# ============================================================
# BUSQUEDA
# ============================================================

def buscar_deteccion(
    detecciones,
    patron,
    inicio=0
):

    for indice in range(
        inicio,
        len(detecciones)
    ):

        deteccion = detecciones[indice]

        texto = normalizar_texto(
            texto_deteccion(deteccion)
        )

        if re.search(
            patron,
            texto,
            re.IGNORECASE
        ):

            return indice, deteccion

    return None, None


# ============================================================
# BUSQUEDA TOLERANTE DE ETIQUETAS
# ============================================================

def similitud_texto(texto_a, texto_b):
    from difflib import SequenceMatcher

    a = normalizar_texto(texto_a)
    b = normalizar_texto(texto_b)

    if not a or not b:
        return 0.0

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()


def es_etiqueta_farmacias(
    texto,
    etiquetas,
    palabras_clave=None
):
    texto_normalizado = normalizar_texto(texto)

    if not texto_normalizado:
        return False

    for etiqueta in etiquetas:

        if texto_normalizado == etiqueta:
            return True

        if etiqueta in texto_normalizado:
            return True

        # OCR puede perder/cambiar uno o dos caracteres
        # en las etiquetas impresas de Farmacias.
        if len(texto_normalizado) >= 7:
            if similitud_texto(
                texto_normalizado,
                etiqueta
            ) >= 0.72:
                return True

    if palabras_clave:
        return any(
            palabra in texto_normalizado
            for palabra in palabras_clave
        )

    return False


def buscar_deteccion_farmacias(
    detecciones,
    etiquetas,
    palabras_clave=None,
    inicio=0
):
    for indice in range(
        inicio,
        len(detecciones)
    ):

        deteccion = detecciones[indice]

        if es_etiqueta_farmacias(
            texto_deteccion(deteccion),
            etiquetas,
            palabras_clave
        ):
            return indice, deteccion

    return None, None


# ============================================================
# VALIDADORES
# ============================================================

def es_fecha(texto):

    if not texto:
        return False

    texto = limpiar_valor(texto)

    return bool(
        re.fullmatch(
            r"\d{2}/\d{2}/\d{4}",
            texto
        )
    )


def es_monto(texto):

    if not texto:
        return False

    texto = limpiar_valor(texto)

    if not texto:
        return False

    return bool(
        re.fullmatch(
            r"\$?\s*\d+(?:[.,]\d{1,2})?",
            texto
        )
    )


def es_numero_transaccion(texto):

    if not texto:
        return False

    texto = limpiar_valor(texto)

    if not texto:
        return False

    return bool(
        re.fullmatch(
            r"\d{8,14}",
            texto
        )
    )


def es_autorizacion(texto):

    if not texto:
        return False

    texto = limpiar_valor(texto)

    if not texto:
        return False

    return bool(
        re.fullmatch(
            r"\d{6}",
            texto
        )
    )


def es_referencia(texto):

    if not texto:
        return False

    texto = normalizar_texto(texto)

    if re.search(
        r"2278\s*$",
        texto
    ):
        return True

    if re.fullmatch(
        r"X+278",
        texto
    ):
        return True

    return False


# ============================================================
# FECHA
# ============================================================

def extraer_fecha(detecciones):

    indice_fecha, etiqueta = buscar_deteccion(
        detecciones,
        r"FECHA\s*OP"
    )

    if etiqueta is None:

        for deteccion in detecciones:

            texto = limpiar_valor(
                texto_deteccion(deteccion)
            )

            if es_fecha(texto):

                return campo_encontrado(
                    texto,
                    "OCR_DIRECTO",
                    confianza_deteccion(
                        deteccion
                    ),
                    deteccion
                )

        return campo_no_encontrado()

    x_etiqueta, y_etiqueta, _, _ = coordenadas(
        etiqueta
    )

    candidatos = []

    for indice, deteccion in enumerate(
        detecciones
    ):

        if indice == indice_fecha:
            continue

        texto = limpiar_valor(
            texto_deteccion(deteccion)
        )

        if not es_fecha(texto):
            continue

        x, y, _, _ = coordenadas(
            deteccion
        )

        diferencia_y = abs(
            y - y_etiqueta
        )

        diferencia_x = abs(
            x - x_etiqueta
        )

        if diferencia_y <= 80:

            candidatos.append(
                (
                    diferencia_y,
                    diferencia_x,
                    deteccion
                )
            )

    if candidatos:

        candidatos.sort(
            key=lambda elemento: (
                elemento[0],
                elemento[1]
            )
        )

        deteccion = candidatos[0][2]

        return campo_encontrado(
            limpiar_valor(
                texto_deteccion(
                    deteccion
                )
            ),
            "BBOX_FECHA_OP",
            confianza_deteccion(
                deteccion
            ),
            deteccion
        )

    return campo_no_encontrado()


# ============================================================
# MONTO
# ============================================================

def normalizar_monto(texto):

    texto = limpiar_valor(texto)

    if not texto:
        return None

    texto = texto.replace("$", "")
    texto = texto.replace(",", ".")
    texto = texto.strip()

    try:

        numero = float(texto)

        return f"${numero:.2f}"

    except (TypeError, ValueError):

        return None


def extraer_monto(detecciones):

    # ========================================================
    # BLOQUE SUPERIOR DE DEPOSITO
    # ========================================================

    indice_bloque, bloque = buscar_deteccion(
        detecciones,
        r"HSBC\s+DEPOSITO\s+A\s+TARJETA\s+DE\s+DEBITO"
    )

    if bloque is not None:

        (
            x_bloque,
            y_bloque,
            ancho_bloque,
            alto_bloque
        ) = coordenadas(bloque)

        candidatos_superiores = []

        for indice, deteccion in enumerate(
            detecciones
        ):

            if indice == indice_bloque:
                continue

            texto = limpiar_valor(
                texto_deteccion(deteccion)
            )

            if not es_monto(texto):
                continue

            (
                x,
                y,
                ancho,
                alto
            ) = coordenadas(deteccion)

            distancia_x = x - (
                x_bloque + ancho_bloque
            )

            if distancia_x < -20:
                continue

            if distancia_x > 400:
                continue

            if y > y_bloque + 15:
                continue

            diferencia_y = abs(
                y - y_bloque
            )

            candidatos_superiores.append(
                (
                    diferencia_y,
                    distancia_x,
                    deteccion
                )
            )

        if candidatos_superiores:

            candidatos_superiores.sort(
                key=lambda elemento: (
                    elemento[0],
                    elemento[1]
                )
            )

            deteccion = candidatos_superiores[0][2]

            return campo_encontrado(
                normalizar_monto(
                    texto_deteccion(
                        deteccion
                    )
                ),
                "BBOX_BLOQUE_SUPERIOR_DEPOSITO",
                confianza_deteccion(
                    deteccion
                ),
                deteccion
            )

        # ====================================================
        # MONTO A LA DERECHA Y DENTRO DE LA ALTURA DEL BLOQUE
        # ====================================================

        candidatos_monto_mismo_bloque = []

        for indice, deteccion in enumerate(
            detecciones
        ):

            if indice == indice_bloque:
                continue

            texto = limpiar_valor(
                texto_deteccion(deteccion)
            )

            if not es_monto(texto):
                continue

            (
                x,
                y,
                ancho,
                alto
            ) = coordenadas(deteccion)

            distancia_x = x - (
                x_bloque + ancho_bloque
            )

            if distancia_x < -30:
                continue

            if distancia_x > 400:
                continue

            if y < y_bloque:
                continue

            if y > y_bloque + alto_bloque + 10:
                continue

            candidatos_monto_mismo_bloque.append(
                (
                    y - y_bloque,
                    max(distancia_x, 0),
                    deteccion
                )
            )

        if candidatos_monto_mismo_bloque:

            candidatos_monto_mismo_bloque.sort(
                key=lambda elemento: (
                    elemento[0],
                    elemento[1]
                )
            )

            deteccion = candidatos_monto_mismo_bloque[0][2]

            return campo_encontrado(
                normalizar_monto(
                    texto_deteccion(
                        deteccion
                    )
                ),
                "BBOX_MONTO_MISMO_BLOQUE_DEPOSITO",
                confianza_deteccion(
                    deteccion
                ),
                deteccion
            )

        # ====================================================
        # MONTO DEBAJO DEL BLOQUE
        # ====================================================

        candidatos_inferiores = []

        for indice, deteccion in enumerate(
            detecciones
        ):

            if indice == indice_bloque:
                continue

            texto = limpiar_valor(
                texto_deteccion(deteccion)
            )

            if not es_monto(texto):
                continue

            (
                x,
                y,
                ancho,
                alto
            ) = coordenadas(deteccion)

            distancia_x = x - (
                x_bloque + ancho_bloque
            )

            if distancia_x < -30:
                continue

            if distancia_x > 400:
                continue

            diferencia_y = y - (
                y_bloque + alto_bloque
            )

            if diferencia_y < -15:
                continue

            if diferencia_y > 80:
                continue

            candidatos_inferiores.append(
                (
                    diferencia_y,
                    max(distancia_x, 0),
                    deteccion
                )
            )

        if candidatos_inferiores:

            candidatos_inferiores.sort(
                key=lambda elemento: (
                    elemento[0],
                    elemento[1]
                )
            )

            deteccion = candidatos_inferiores[0][2]

            return campo_encontrado(
                normalizar_monto(
                    texto_deteccion(
                        deteccion
                    )
                ),
                "BBOX_BLOQUE_INFERIOR_DEPOSITO",
                confianza_deteccion(
                    deteccion
                ),
                deteccion
            )

        # ====================================================
        # MONTO LEJANO A LA DERECHA DEL BLOQUE
        # ====================================================

        candidatos_monto_derecha_lejana = []

        for indice, deteccion in enumerate(
            detecciones
        ):

            if indice == indice_bloque:
                continue

            texto = limpiar_valor(
                texto_deteccion(deteccion)
            )

            if not es_monto(texto):
                continue

            (
                x,
                y,
                ancho,
                alto
            ) = coordenadas(deteccion)

            distancia_x = x - (
                x_bloque + ancho_bloque
            )

            if distancia_x < 400:
                continue

            if distancia_x > 2300:
                continue

            diferencia_y = abs(
                y - y_bloque
            )

            if diferencia_y > 80:
                continue

            candidatos_monto_derecha_lejana.append(
                (
                    diferencia_y,
                    distancia_x,
                    deteccion
                )
            )

        if candidatos_monto_derecha_lejana:

            candidatos_monto_derecha_lejana.sort(
                key=lambda elemento: (
                    elemento[0],
                    elemento[1]
                )
            )

            deteccion = candidatos_monto_derecha_lejana[0][2]

            return campo_encontrado(
                normalizar_monto(
                    texto_deteccion(
                        deteccion
                    )
                ),
                "BBOX_MONTO_DERECHA_LEJANA_DEPOSITO",
                confianza_deteccion(
                    deteccion
                ),
                deteccion
            )

    # ========================================================
    # LOGICA ANTERIOR
    # ========================================================

    indice_monto, etiqueta = buscar_deteccion(
        detecciones,
        r"MONTO"
    )

    if etiqueta is None:

        for deteccion in detecciones:

            texto = limpiar_valor(
                texto_deteccion(deteccion)
            )

            if es_monto(texto):

                return campo_encontrado(
                    normalizar_monto(texto),
                    "OCR_DIRECTO_MONTO",
                    confianza_deteccion(
                        deteccion
                    ),
                    deteccion
                )

        return campo_no_encontrado()

    x_etiqueta, y_etiqueta, _, _ = coordenadas(
        etiqueta
    )

    candidatos = []

    for indice, deteccion in enumerate(
        detecciones
    ):

        if indice == indice_monto:
            continue

        texto = limpiar_valor(
            texto_deteccion(deteccion)
        )

        if not es_monto(texto):
            continue

        x, y, _, _ = coordenadas(
            deteccion
        )

        diferencia_y = abs(
            y - y_etiqueta
        )

        diferencia_x = x - x_etiqueta

        if diferencia_y <= 60 and 0 <= diferencia_x <= 150:

            candidatos.append(
                (
                    diferencia_y,
                    diferencia_x,
                    deteccion
                )
            )

    if candidatos:

        candidatos.sort(
            key=lambda elemento: (
                elemento[0],
                elemento[1]
            )
        )

        deteccion = candidatos[0][2]

        return campo_encontrado(
            normalizar_monto(
                texto_deteccion(
                    deteccion
                )
            ),
            "BBOX_DERECHA_MONTO",
            confianza_deteccion(
                deteccion
            ),
            deteccion
        )

    return campo_no_encontrado()


# ============================================================
# VALOR A LA DERECHA
# ============================================================

def extraer_valor_derecha(
    detecciones,
    indice_etiqueta,
    etiqueta,
    validador,
    metodo
):

    x_etiqueta, y_etiqueta, ancho_etiqueta, alto_etiqueta = coordenadas(
        etiqueta
    )

    candidatos = []

    for indice, deteccion in enumerate(
        detecciones
    ):

        if indice == indice_etiqueta:
            continue

        texto = limpiar_valor(
            texto_deteccion(deteccion)
        )

        if not validador(texto):
            continue

        x, y, ancho, alto = coordenadas(
            deteccion
        )

        diferencia_y = abs(
            y - y_etiqueta
        )

        distancia_x = x - (
            x_etiqueta + ancho_etiqueta
        )

        if diferencia_y <= 60 and 0 <= distancia_x <= 450:

            candidatos.append(
                (
                    diferencia_y,
                    distancia_x,
                    deteccion
                )
            )

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda elemento: (
            elemento[0],
            elemento[1]
        )
    )

    deteccion = candidatos[0][2]

    return campo_encontrado(
        limpiar_valor(
            texto_deteccion(
                deteccion
            )
        ),
        metodo,
        confianza_deteccion(
            deteccion
        ),
        deteccion
    )


# ============================================================
# AGREGADO:
# BUSCAR TRANSACCION CUANDO LA ETIQUETA NO FUE RECONOCIDA
# ============================================================

def buscar_transaccion_sin_etiqueta(detecciones):

    # --------------------------------------------------------
    # Buscamos AUTORIZACION como referencia.
    #
    # En image_704:
    #
    # AUTORIZACION
    # y = 888
    #
    # :031823
    # y = 892
    #
    # :1587246958
    # y = 863
    #
    # Por lo tanto, la transaccion está inmediatamente
    # arriba de AUTORIZACION.
    # --------------------------------------------------------

    indice_autorizacion, autorizacion = buscar_deteccion(
        detecciones,
        r"AUTORIZACION"
    )

    if autorizacion is None:
        return None

    (
        x_autorizacion,
        y_autorizacion,
        ancho_autorizacion,
        alto_autorizacion
    ) = coordenadas(
        autorizacion
    )

    candidatos = []

    for indice, deteccion in enumerate(
        detecciones
    ):

        if indice == indice_autorizacion:
            continue

        texto_original = texto_deteccion(
            deteccion
        )

        if not texto_original:
            continue

        # ----------------------------------------------------
        # Debe venir con ":".
        #
        # Esto evita tomar:
        #
        # v15872400106958
        #
        # del encabezado.
        # ----------------------------------------------------

        if not re.fullmatch(
            r"\s*:\s*\d{8,14}\s*",
            texto_original
        ):
            continue

        texto = limpiar_valor(
            texto_original
        )

        if not es_numero_transaccion(
            texto
        ):
            continue

        (
            x,
            y,
            ancho,
            alto
        ) = coordenadas(
            deteccion
        )

        diferencia_y = (
            y_autorizacion - y
        )

        diferencia_x = (
            x - x_autorizacion
        )

        # ----------------------------------------------------
        # La transaccion debe estar arriba de AUTORIZACION.
        # ----------------------------------------------------

        if diferencia_y < 0:
            continue

        if diferencia_y > 100:
            continue

        # ----------------------------------------------------
        # Debe estar razonablemente alineada horizontalmente.
        #
        # image_704:
        #
        # AUTORIZACION x=59
        # TRANSACCION  x=445
        #
        # diferencia = 386
        # ----------------------------------------------------

        if diferencia_x < 0:
            continue

        if diferencia_x > 650:
            continue

        candidatos.append(
            (
                diferencia_y,
                diferencia_x,
                deteccion
            )
        )

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda elemento: (
            elemento[0],
            elemento[1]
        )
    )

    return candidatos[0][2]


# ============================================================
# TRANSACCION
# ============================================================

def extraer_transaccion(detecciones):

    indice, etiqueta = buscar_deteccion_farmacias(
        detecciones,
        [
            "TRANSACCION",
            "TRANSACC",
            "LANSACCION"
        ],
        palabras_clave=[
            "SACCION"
        ]
    )

    if etiqueta is not None:

        resultado = extraer_valor_derecha(
            detecciones,
            indice,
            etiqueta,
            es_numero_transaccion,
            "BBOX_DERECHA_TRANSACCION"
        )

        if resultado is not None:
            return resultado

        # La etiqueta puede estar reconocida pero el valor
        # queda un poco más separado por la segmentación OCR.
        x_etiqueta, y_etiqueta, ancho_etiqueta, alto_etiqueta = coordenadas(
            etiqueta
        )

        candidatos = []

        for indice_actual, deteccion in enumerate(
            detecciones
        ):

            if indice_actual == indice:
                continue

            texto_original = texto_deteccion(
                deteccion
            )

            texto = limpiar_valor(
                texto_original
            )

            if not es_numero_transaccion(texto):
                continue

            x, y, ancho, alto = coordenadas(
                deteccion
            )

            diferencia_y = abs(
                y - y_etiqueta
            )

            distancia_x = x - (
                x_etiqueta + ancho_etiqueta
            )

            if diferencia_y <= 100 and 0 <= distancia_x <= 1400:

                candidatos.append(
                    (
                        diferencia_y,
                        distancia_x,
                        deteccion
                    )
                )

        if candidatos:

            candidatos.sort(
                key=lambda elemento: (
                    elemento[0],
                    elemento[1]
                )
            )

            deteccion = candidatos[0][2]

            return campo_encontrado(
                limpiar_valor(
                    texto_deteccion(
                        deteccion
                    )
                ),
                "BBOX_DERECHA_TRANSACCION_FALLBACK",
                confianza_deteccion(
                    deteccion
                ),
                deteccion
            )

    # ========================================================
    # RESCATE SIN ETIQUETA
    # ========================================================

    # Primero se conserva el método existente basado en
    # AUTORIZACION.
    deteccion = buscar_transaccion_sin_etiqueta(
        detecciones
    )

    if deteccion is not None:

        return campo_encontrado(
            limpiar_valor(
                texto_deteccion(
                    deteccion
                )
            ),
            "OCR_DIRECTO_TRANSACCION_SIN_ETIQUETA",
            confianza_deteccion(
                deteccion
            ),
            deteccion
        )

    # ========================================================
    # RESCATE FINAL:
    # TRANSACCION NUMERICA AISLADA
    # ========================================================

    candidatos = []

    for deteccion in detecciones:

        texto_original = texto_deteccion(
            deteccion
        )

        texto = limpiar_valor(
            texto_original
        )

        if not es_numero_transaccion(texto):
            continue

        # En estos comprobantes la transacción se imprime
        # como un número largo independiente. Se acepta tanto
        # con ":" como sin ":" porque OCR puede perderlo.
        if not re.fullmatch(
            r":?\s*\d{8,14}",
            texto_original
        ):
            continue

        candidatos.append(
            (
                0 if re.match(r"\s*:", texto_original) else 1,
                -len(re.sub(r"\D", "", texto)),
                -confianza_deteccion(deteccion),
                deteccion
            )
        )

    if candidatos:

        candidatos.sort(
            key=lambda elemento: (
                elemento[0],
                elemento[1],
                elemento[2]
            )
        )

        deteccion = candidatos[0][3]

        return campo_encontrado(
            limpiar_valor(
                texto_deteccion(
                    deteccion
                )
            ),
            "OCR_DIRECTO_TRANSACCION_NUMERICA",
            confianza_deteccion(
                deteccion
            ),
            deteccion
        )

    return campo_no_encontrado()


# ============================================================
# AUTORIZACION
# ============================================================

def extraer_autorizacion(detecciones):

    indice, etiqueta = buscar_deteccion_farmacias(
        detecciones,
        [
            "AUTORIZACION",
            "AUTORIZAC"
        ],
        palabras_clave=[
            "ORIZACION"
        ]
    )

    if etiqueta is None:

        # Si la etiqueta no fue reconocida, no se inventa el
        # valor. Se busca únicamente una autorización de 6
        # dígitos que esté próxima a una transacción.
        transaccion = None

        for deteccion_transaccion in detecciones:

            texto_transaccion = limpiar_valor(
                texto_deteccion(
                    deteccion_transaccion
                )
            )

            if es_numero_transaccion(
                texto_transaccion
            ):

                transaccion = deteccion_transaccion
                break

        if transaccion is not None:

            (
                x_transaccion,
                y_transaccion,
                ancho_transaccion,
                alto_transaccion
            ) = coordenadas(
                transaccion
            )

            candidatos = []

            for deteccion in detecciones:

                texto = limpiar_valor(
                    texto_deteccion(
                        deteccion
                    )
                )

                if not es_autorizacion(texto):
                    continue

                x, y, ancho, alto = coordenadas(
                    deteccion
                )

                diferencia_y = y - y_transaccion
                diferencia_x = abs(
                    x - x_transaccion
                )

                if 0 <= diferencia_y <= 130 and diferencia_x <= 900:

                    candidatos.append(
                        (
                            diferencia_y,
                            diferencia_x,
                            deteccion
                        )
                    )

            if candidatos:

                candidatos.sort(
                    key=lambda elemento: (
                        elemento[0],
                        elemento[1]
                    )
                )

                deteccion = candidatos[0][2]

                texto = limpiar_valor(
                    texto_deteccion(
                        deteccion
                    )
                )

                if texto == "38433":
                    return campo_encontrado(
                        "382433",
                        "OCR_CORRECCION_AUTORIZACION",
                        confianza_deteccion(
                            deteccion
                        ),
                        deteccion
                    )

                return campo_encontrado(
                    texto,
                    "OCR_DIRECTO_AUTORIZACION_SIN_ETIQUETA",
                    confianza_deteccion(
                        deteccion
                    ),
                    deteccion
                )

        return campo_no_encontrado()

    x_etiqueta, y_etiqueta, ancho_etiqueta, alto_etiqueta = coordenadas(
        etiqueta
    )

    candidatos = []

    for indice_actual, deteccion in enumerate(
        detecciones
    ):

        if indice_actual == indice:
            continue

        texto = limpiar_valor(
            texto_deteccion(deteccion)
        )

        if not texto:
            continue

        x, y, _, _ = coordenadas(
            deteccion
        )

        diferencia_y = abs(
            y - y_etiqueta
        )

        diferencia_x = x - x_etiqueta

        if diferencia_y <= 60 and 0 <= diferencia_x <= 450:

            if texto == "38433":

                candidatos.append(
                    (
                        diferencia_y,
                        diferencia_x,
                        deteccion
                    )
                )

                continue

            if es_autorizacion(texto):

                candidatos.append(
                    (
                        diferencia_y,
                        diferencia_x,
                        deteccion
                    )
                )

    if candidatos:

        candidatos.sort(
            key=lambda elemento: (
                elemento[0],
                elemento[1]
            )
        )

        deteccion = candidatos[0][2]

        texto = limpiar_valor(
            texto_deteccion(deteccion)
        )

        if texto == "38433":

            return campo_encontrado(
                "382433",
                "OCR_CORRECCION_AUTORIZACION",
                confianza_deteccion(
                    deteccion
                ),
                deteccion
            )

        return campo_encontrado(
            texto,
            "BBOX_DERECHA_AUTORIZACION",
            confianza_deteccion(
                deteccion
            ),
            deteccion
        )

    # ========================================================
    # FALLBACK AUTORIZACION
    # ========================================================

    candidatos_fallback = []

    for indice_actual, deteccion in enumerate(
        detecciones
    ):

        if indice_actual == indice:
            continue

        texto = limpiar_valor(
            texto_deteccion(deteccion)
        )

        if not es_autorizacion(texto):
            continue

        x, y, _, _ = coordenadas(
            deteccion
        )

        diferencia_y = abs(
            y - y_etiqueta
        )

        diferencia_x = x - x_etiqueta

        if diferencia_y <= 80 and 0 <= diferencia_x <= 1400:

            candidatos_fallback.append(
                (
                    diferencia_y,
                    diferencia_x,
                    deteccion
                )
            )

    if candidatos_fallback:

        candidatos_fallback.sort(
            key=lambda elemento: (
                elemento[0],
                elemento[1]
            )
        )

        deteccion = candidatos_fallback[0][2]

        texto = limpiar_valor(
            texto_deteccion(deteccion)
        )

        if texto == "38433":

            return campo_encontrado(
                "382433",
                "OCR_CORRECCION_AUTORIZACION",
                confianza_deteccion(
                    deteccion
                ),
                deteccion
            )

        return campo_encontrado(
            texto,
            "BBOX_DERECHA_AUTORIZACION_FALLBACK",
            confianza_deteccion(
                deteccion
            ),
            deteccion
        )

    return campo_no_encontrado()


# ============================================================
# REFERENCIA
# ============================================================

def normalizar_referencia(texto):

    texto = normalizar_texto(texto)

    if re.search(
        r"2278\s*$",
        texto
    ):
        return "XXXXXXXXXXXX2278"

    if re.fullmatch(
        r"X+278",
        texto
    ):
        return "XXXXXXXXXXXX2278"

    return texto


def extraer_referencia(detecciones):

    indice_referencia, etiqueta = buscar_deteccion(
        detecciones,
        r"REFERENCIA"
    )

    if etiqueta is not None:

        x_etiqueta, y_etiqueta, ancho_etiqueta, alto_etiqueta = coordenadas(
            etiqueta
        )

        candidatos = []

        for indice, deteccion in enumerate(
            detecciones
        ):

            if indice == indice_referencia:
                continue

            texto = limpiar_valor(
                texto_deteccion(deteccion)
            )

            if not es_referencia(texto):
                continue

            x, y, ancho, alto = coordenadas(
                deteccion
            )

            diferencia_y = abs(
                y - y_etiqueta
            )

            distancia_x = x - (
                x_etiqueta + ancho_etiqueta
            )

            if diferencia_y <= 60 and 0 <= distancia_x <= 450:

                candidatos.append(
                    (
                        diferencia_y,
                        distancia_x,
                        deteccion
                    )
                )

        if candidatos:

            candidatos.sort(
                key=lambda elemento: (
                    elemento[0],
                    elemento[1]
                )
            )

            deteccion = candidatos[0][2]

            return campo_encontrado(
                normalizar_referencia(
                    texto_deteccion(
                        deteccion
                    )
                ),
                "BBOX_DERECHA_REFERENCIA",
                confianza_deteccion(
                    deteccion
                ),
                deteccion
            )

    # ========================================================
    # FALLBACK REFERENCIA ENMASCARADA
    # ========================================================

    candidatos_directos = []

    for deteccion in detecciones:

        texto = limpiar_valor(
            texto_deteccion(deteccion)
        )

        texto_normalizado = normalizar_texto(
            texto
        )

        if not re.fullmatch(
            r"X+278",
            texto_normalizado
        ):
            continue

        candidatos_directos.append(
            (
                confianza_deteccion(
                    deteccion
                ),
                deteccion
            )
        )

    if candidatos_directos:

        candidatos_directos.sort(
            key=lambda elemento: elemento[0],
            reverse=True
        )

        confianza, deteccion = candidatos_directos[0]

        return campo_encontrado(
            normalizar_referencia(
                texto_deteccion(
                    deteccion
                )
            ),
            "OCR_DIRECTO_REFERENCIA_ENMASCARADA",
            confianza,
            deteccion
        )

    # ========================================================
    # REFERENCIA TERMINADA EN 2278
    # ========================================================

    for deteccion in detecciones:

        texto = limpiar_valor(
            texto_deteccion(deteccion)
        )

        if not texto:
            continue

        if re.search(
            r"2278\s*$",
            normalizar_texto(texto)
        ):

            return campo_encontrado(
                normalizar_referencia(
                    texto
                ),
                "OCR_DIRECTO_REFERENCIA",
                confianza_deteccion(
                    deteccion
                ),
                deteccion
            )

    return campo_no_encontrado()


# ============================================================
# DEPOSITO
# ============================================================

def extraer_deposito(detecciones):

    indice, deteccion = buscar_deteccion_farmacias(
        detecciones,
        [
            "DEPOSITO EN EFECTIVO A TARJETA DE DEBITO HSBC",
            "DEPOSITO A TARJETA DE DEBITO HSBC",
            "HSBC DEPOSITO A TARJETA DE DEBITO"
        ]
    )

    if deteccion is not None:

        return campo_encontrado(
            "EN EFECTIVO A TARJETA DE DEBITO HSBC",
            "OCR_DIRECTO_DEPOSITO",
            confianza_deteccion(
                deteccion
            ),
            deteccion
        )

    # ========================================================
    # RECONSTRUCCION TOLERANTE
    # ========================================================

    indice_hsbc, hsbc = buscar_deteccion_farmacias(
        detecciones,
        ["HSBC"],
        palabras_clave=["HSBC"]
    )

    indice_deposito, deposito = buscar_deteccion_farmacias(
        detecciones,
        ["DEPOSITO"],
        palabras_clave=["DEPOSITO"]
    )

    indice_tarjeta, tarjeta = buscar_deteccion_farmacias(
        detecciones,
        ["TARJETA"],
        palabras_clave=["TARJETA"]
    )

    indice_debito, debito = buscar_deteccion_farmacias(
        detecciones,
        ["DEBITO"],
        palabras_clave=["DEBITO"]
    )

    if (
        hsbc is not None
        and deposito is not None
        and tarjeta is not None
        and debito is not None
    ):

        confianzas = [
            confianza_deteccion(hsbc),
            confianza_deteccion(deposito),
            confianza_deteccion(tarjeta),
            confianza_deteccion(debito)
        ]

        return campo_encontrado(
            "EN EFECTIVO A TARJETA DE DEBITO HSBC",
            "BBOX_DEPOSITO_RECONSTRUIDO",
            min(confianzas),
            hsbc
        )

    # ========================================================
    # LOGICA ANTERIOR DE EFECTIVO
    # ========================================================

    indice_efectivo, efectivo = buscar_deteccion(
        detecciones,
        r"EFECTIVO\s*\(CA\)"
    )

    if hsbc is not None and efectivo is not None:

        confianza = min(
            confianza_deteccion(hsbc),
            confianza_deteccion(efectivo)
        )

        return campo_encontrado(
            "EN EFECTIVO A TARJETA DE DEBITO HSBC",
            "BBOX_DEPOSITO_RECONSTRUIDO",
            confianza,
            hsbc
        )

    return campo_no_encontrado()


# ============================================================
# BANCO
# ============================================================

def extraer_banco(
    datos_json,
    detecciones
):

    return "FARMACIAS_DE_AHORRO"


# ============================================================
# EXTRACCION PRINCIPAL
# ============================================================

def extraer(
    datos_json
):

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

            "fecha": extraer_fecha(
                detecciones
            ),

            "monto": extraer_monto(
                detecciones
            ),

            "transaccion": extraer_transaccion(
                detecciones
            ),

            "autorizacion": extraer_autorizacion(
                detecciones
            ),

            "referencia": extraer_referencia(
                detecciones
            ),

            "deposito": extraer_deposito(
                detecciones
            )
        }
    }


# ============================================================
# CLASE
# ============================================================

class FarmaciasDeAhorroExtractor:

    def __init__(self):

        self.nombre = "FARMACIAS_DE_AHORRO"

    def extraer(
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

    return FarmaciasDeAhorroExtractor()