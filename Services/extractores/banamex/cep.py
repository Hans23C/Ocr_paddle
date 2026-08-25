import re


# ============================================================
# UTILIDADES
# ============================================================

def texto(deteccion):
    if not isinstance(deteccion, dict):
        return ""

    return str(
        deteccion.get("texto", "")
    ).strip()


def normalizar(valor):
    valor = str(valor or "").lower()

    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
        "ñ": "n",
        "®": "",
        "*": "",
    }

    for origen, destino in reemplazos.items():
        valor = valor.replace(origen, destino)

    return " ".join(valor.split())


def confianza(deteccion):
    try:
        return float(
            deteccion.get(
                "confianza",
                0.0
            )
        )
    except (TypeError, ValueError):
        return 0.0


def obtener_bbox(deteccion):
    if not deteccion:
        return None

    return {
        "x": deteccion.get("x_rel", 0.0),
        "y": deteccion.get("y_rel", 0.0),
        "ancho": deteccion.get("ancho_rel", 0.0),
        "alto": deteccion.get("alto_rel", 0.0),
    }


def crear_resultado(
    deteccion,
    metodo
):
    if deteccion is None:
        return {
            "encontrado": False,
            "valor": None,
            "metodo": metodo,
            "confianza": 0.0,
        }

    return {
        "encontrado": True,
        "valor": texto(deteccion),
        "metodo": metodo,
        "confianza": confianza(deteccion),
        "bbox": obtener_bbox(deteccion),
    }


def crear_resultado_texto(
    valor,
    metodo,
    confianza_valor=1.0
):
    if not valor:
        return {
            "encontrado": False,
            "valor": None,
            "metodo": metodo,
            "confianza": 0.0,
        }

    return {
        "encontrado": True,
        "valor": valor,
        "metodo": metodo,
        "confianza": confianza_valor,
    }


# ============================================================
# GEOMETRÍA
# ============================================================

def centro_y(deteccion):
    return (
        deteccion.get("y_rel", 0.0)
        +
        deteccion.get("alto_rel", 0.0) / 2
    )


# ============================================================
# BÚSQUEDA DE ETIQUETAS
# ============================================================

def buscar_exacta(
    detecciones,
    etiqueta
):
    objetivo = normalizar(etiqueta)

    for deteccion in detecciones:
        if normalizar(texto(deteccion)) == objetivo:
            return deteccion

    return None


def buscar_contiene(
    detecciones,
    etiqueta
):
    objetivo = normalizar(etiqueta)

    for deteccion in detecciones:
        if objetivo in normalizar(texto(deteccion)):
            return deteccion

    return None


# ============================================================
# BUSCAR VALOR A LA DERECHA
# ============================================================

def buscar_derecha(
    etiqueta,
    detecciones,
    tolerancia_y=0.05,
    validador=None
):
    if etiqueta is None:
        return None

    limite_x = (
        etiqueta.get("x_rel", 0.0)
        +
        etiqueta.get("ancho_rel", 0.0)
    )

    y_referencia = centro_y(etiqueta)

    candidatos = []

    for deteccion in detecciones:

        if deteccion is etiqueta:
            continue

        valor = texto(deteccion)

        if not valor:
            continue

        x = deteccion.get(
            "x_rel",
            0.0
        )

        if x <= limite_x:
            continue

        diferencia_y = abs(
            centro_y(deteccion)
            -
            y_referencia
        )

        if diferencia_y > tolerancia_y:
            continue

        if validador and not validador(valor):
            continue

        candidatos.append(
            (
                diferencia_y,
                x,
                deteccion
            )
        )

    candidatos.sort(
        key=lambda item: (
            item[0],
            item[1]
        )
    )

    if candidatos:
        return candidatos[0][2]

    return None


# ============================================================
# VALIDADORES
# ============================================================

def es_importe(valor):
    return bool(
        re.search(
            r"\$\s*[\d,]+\.\d{2}",
            valor
        )
    )


def es_clave_rastreo(valor):
    numeros = re.sub(
        r"\D",
        "",
        valor
    )

    return len(numeros) == 18


def es_fecha(valor):
    valor = normalizar(valor)

    patrones = [
        r"\d{1,2}\s+de\s+\w+\s+de\s+\d{4}",
        r"\d{1,2}\s+\w+\s+\d{4}",
        r"\d{1,2}/\d{1,2}/\d{4}",
    ]

    return any(
        re.search(
            patron,
            valor
        )
        for patron in patrones
    )


def es_hora(valor):
    return bool(
        re.search(
            r"\d{1,2}:\d{2}:\d{2}",
            valor
        )
    )


# ============================================================
# DATOS OCR
# ============================================================

def obtener_detecciones(
    resultado_ocr
):
    if isinstance(resultado_ocr, dict):
        return resultado_ocr.get(
            "detecciones",
            []
        )

    if isinstance(resultado_ocr, list):
        return resultado_ocr

    return []


def obtener_lineas(
    resultado_ocr
):
    if not isinstance(
        resultado_ocr,
        dict
    ):
        return []

    lineas = resultado_ocr.get(
        "lineas",
        []
    )

    if isinstance(
        lineas,
        list
    ):
        return [
            str(x).strip()
            for x in lineas
            if str(x).strip()
        ]

    return []


def obtener_texto_completo(
    resultado_ocr
):
    if not isinstance(
        resultado_ocr,
        dict
    ):
        return ""

    return str(
        resultado_ocr.get(
            "texto_completo",
            ""
        )
    )


# ============================================================
# DETECTAR FORMATO
# ============================================================

def detectar_formato(
    detecciones,
    lineas=None,
    texto_completo=""
):
    textos = [
        normalizar(texto(d))
        for d in detecciones
    ]

    texto_general = normalizar(
        texto_completo
    )

    # --------------------------------------------------------
    # CEP BANXICO
    # --------------------------------------------------------

    if any(
        "comprobante electronico de pago" in t
        for t in textos
    ):
        return "CEP_BANXICO"

    if (
        "comprobante electronico de pago"
        in texto_general
    ):
        return "CEP_BANXICO"

    if any(
        "fecha de operacion en el spei" in t
        for t in textos
    ):
        return "CEP_BANXICO"

    # --------------------------------------------------------
    # CEP BANAMEX
    # --------------------------------------------------------

    if any(
        "cuenta origen" in t
        for t in textos
    ):
        return "CEP_BANAMEX"

    return "CEP_DESCONOCIDO"


# ============================================================
# CEP BANAMEX
# ============================================================

def extraer_cep_banamex(
    detecciones
):
    campos = {}

    # ========================================================
    # IMPORTE
    # ========================================================

    importe = None

    for deteccion in detecciones:
        if es_importe(
            texto(deteccion)
        ):
            importe = deteccion
            break

    campos["importe"] = crear_resultado(
        importe,
        "OCR_DIRECTO"
    )

    # ========================================================
    # CUENTA ORIGEN
    # ========================================================

    etiqueta = buscar_exacta(
        detecciones,
        "Cuenta origen"
    )

    valor = None

    if etiqueta:

        y_limite = (
            etiqueta.get("y_rel", 0)
            +
            etiqueta.get("alto_rel", 0)
        )

        candidatos = []

        for deteccion in detecciones:

            if deteccion is etiqueta:
                continue

            y = deteccion.get(
                "y_rel",
                0
            )

            if y <= y_limite:
                continue

            if y - y_limite > 0.07:
                continue

            if texto(deteccion):
                candidatos.append(
                    deteccion
                )

        candidatos.sort(
            key=lambda d:
                d.get("y_rel", 0)
        )

        if candidatos:
            valor = candidatos[0]

    campos["cuenta_origen"] = crear_resultado(
        valor,
        "BBOX_DEBAJO"
    )

    # ========================================================
    # CUENTA DESTINO
    # ========================================================

    etiqueta = buscar_exacta(
        detecciones,
        "Cuenta destino"
    )

    valor = None

    if etiqueta:

        y_limite = (
            etiqueta.get("y_rel", 0)
            +
            etiqueta.get("alto_rel", 0)
        )

        candidatos = []

        for deteccion in detecciones:

            if deteccion is etiqueta:
                continue

            y = deteccion.get(
                "y_rel",
                0
            )

            if y <= y_limite:
                continue

            if y - y_limite > 0.07:
                continue

            if texto(deteccion):
                candidatos.append(
                    deteccion
                )

        candidatos.sort(
            key=lambda d:
                d.get("y_rel", 0)
        )

        if candidatos:
            valor = candidatos[0]

    campos["cuenta_destino"] = crear_resultado(
        valor,
        "BBOX_DEBAJO"
    )

    # ========================================================
    # NÚMERO AUTORIZACIÓN
    # ========================================================

    etiqueta = buscar_contiene(
        detecciones,
        "numero de autorizacion"
    )

    numero = None

    if etiqueta:

        match = re.search(
            r"autorizacion\s+(\d+)",
            texto(etiqueta),
            re.IGNORECASE
        )

        if match:

            campos["numero_autorizacion"] = (
                crear_resultado_texto(
                    match.group(1),
                    "REGEX"
                )
            )

        else:

            numero = buscar_derecha(
                etiqueta,
                detecciones,
                0.04
            )

            campos["numero_autorizacion"] = (
                crear_resultado(
                    numero,
                    "BBOX_DERECHA"
                )
            )

    else:

        campos["numero_autorizacion"] = (
            crear_resultado(
                None,
                "REGEX"
            )
        )

    # ========================================================
    # CLAVE RASTREO
    # ========================================================

    etiqueta = buscar_contiene(
        detecciones,
        "clave de rastreo"
    )

    valor = buscar_derecha(
        etiqueta,
        detecciones,
        0.04,
        es_clave_rastreo
    )

    campos["clave_rastreo"] = crear_resultado(
        valor,
        "BBOX_DERECHA"
    )

    # ========================================================
    # TIPO CUENTA
    # ========================================================

    etiqueta = buscar_contiene(
        detecciones,
        "tipo de cuenta"
    )

    valor = buscar_derecha(
        etiqueta,
        detecciones,
        0.04
    )

    campos["tipo_cuenta"] = crear_resultado(
        valor,
        "BBOX_DERECHA"
    )

    # ========================================================
    # TIPO BENEFICIARIO
    # ========================================================

    etiqueta = buscar_contiene(
        detecciones,
        "tipo de beneficiario"
    )

    valor = buscar_derecha(
        etiqueta,
        detecciones,
        0.04
    )

    campos["tipo_beneficiario"] = crear_resultado(
        valor,
        "BBOX_DERECHA"
    )

    # ========================================================
    # CONCEPTO
    # ========================================================

    etiqueta = buscar_contiene(
        detecciones,
        "concepto"
    )

    valor = buscar_derecha(
        etiqueta,
        detecciones,
        0.04
    )

    campos["concepto"] = crear_resultado(
        valor,
        "BBOX_DERECHA"
    )

    # ========================================================
    # REFERENCIA
    # ========================================================

    etiqueta = buscar_contiene(
        detecciones,
        "referencia numerica"
    )

    valor = buscar_derecha(
        etiqueta,
        detecciones,
        0.04
    )

    campos["referencia_numerica"] = (
        crear_resultado(
            valor,
            "BBOX_DERECHA"
        )
    )

    # ========================================================
    # FECHA HORA
    # ========================================================

    etiqueta = buscar_contiene(
        detecciones,
        "fecha y hora"
    )

    valor = buscar_derecha(
        etiqueta,
        detecciones,
        0.04
    )

    campos["fecha_hora"] = crear_resultado(
        valor,
        "BBOX_DERECHA"
    )

    return campos


# ============================================================
# CEP BANXICO
# ============================================================

def extraer_cep_banxico(
    resultado_ocr,
    detecciones
):
    campos = {}

    # ========================================================
    # MONTO
    # ========================================================

    monto = None

    etiqueta = buscar_exacta(
        detecciones,
        "Monto"
    )

    if etiqueta:

        monto = buscar_derecha(
            etiqueta,
            detecciones,
            0.06,
            es_importe
        )

    if monto is None:

        for deteccion in detecciones:

            if es_importe(
                texto(deteccion)
            ):
                monto = deteccion
                break

    campos["monto"] = crear_resultado(
        monto,
        "BBOX_DERECHA"
    )

    # ========================================================
    # FECHA OPERACIÓN
    # ========================================================

    fecha = None

    etiqueta = buscar_contiene(
        detecciones,
        "fecha de operacion en el spei"
    )

    if etiqueta:

        fecha = buscar_derecha(
            etiqueta,
            detecciones,
            0.06,
            es_fecha
        )

    if fecha is None:

        for deteccion in detecciones:

            if es_fecha(
                texto(deteccion)
            ):

                y = deteccion.get(
                    "y_rel",
                    0
                )

                if y < 0.20:
                    fecha = deteccion
                    break

    campos["fecha_operacion"] = (
        crear_resultado(
            fecha,
            "BBOX_DERECHA"
        )
    )

    # ========================================================
    # HORA ABONO
    # ========================================================

    hora = None

    etiqueta = buscar_contiene(
        detecciones,
        "hora de abono en la cuenta beneficiaria"
    )

    if etiqueta:

        hora = buscar_derecha(
            etiqueta,
            detecciones,
            0.06,
            es_hora
        )

    if hora is None:

        for deteccion in detecciones:

            if es_hora(
                texto(deteccion)
            ):

                y = deteccion.get(
                    "y_rel",
                    0
                )

                if 0.20 <= y <= 0.30:
                    hora = deteccion
                    break

    campos["hora_abono"] = crear_resultado(
        hora,
        "BBOX_DERECHA"
    )

    # ========================================================
    # CONCEPTO
    # ========================================================
    #
    # NO usamos la etiqueta "Concepto del pago" porque en
    # algunos OCR esa detección queda asociada a la zona
    # equivocada.
    #
    # Buscamos directamente el texto real del concepto.
    # ========================================================

    concepto = None

    for deteccion in detecciones:

        valor = normalizar(
            texto(deteccion)
        )

        if valor == "transferencia interbancaria":

            concepto = deteccion
            break

    # Fallback para otros CEP Banxico
    if concepto is None:

        etiqueta = buscar_contiene(
            detecciones,
            "concepto del pago"
        )

        if etiqueta:

            concepto = buscar_derecha(
                etiqueta,
                detecciones,
                0.06
            )

    campos["concepto"] = crear_resultado(
        concepto,
        "BBOX_DIRECTO"
    )

    # ========================================================
    # REFERENCIA NUMÉRICA
    # ========================================================

    referencia = None

    etiqueta = buscar_contiene(
        detecciones,
        "referencia numerica"
    )

    if etiqueta:

        referencia = buscar_derecha(
            etiqueta,
            detecciones,
            0.06
        )

    if referencia is None:

        for deteccion in detecciones:

            valor = texto(deteccion)

            if re.fullmatch(
                r"\d{4,8}",
                valor
            ):

                y = deteccion.get(
                    "y_rel",
                    0
                )

                if 0.18 <= y <= 0.28:

                    referencia = deteccion
                    break

    campos["referencia_numerica"] = (
        crear_resultado(
            referencia,
            "BBOX_DERECHA"
        )
    )

    # ========================================================
    # CLAVE RASTREO
    # ========================================================

    clave = None

    etiqueta = buscar_contiene(
        detecciones,
        "clave de rastreo"
    )

    if etiqueta:

        clave = buscar_derecha(
            etiqueta,
            detecciones,
            0.06,
            es_clave_rastreo
        )

    campos["clave_rastreo"] = crear_resultado(
        clave,
        "BBOX_DERECHA"
    )

    # ========================================================
    # INSTITUCIÓN EMISORA
    # ========================================================

    etiqueta = buscar_contiene(
        detecciones,
        "institucion emisora del pago"
    )

    emisora = buscar_derecha(
        etiqueta,
        detecciones,
        0.06
    )

    campos["institucion_emisora"] = (
        crear_resultado(
            emisora,
            "BBOX_DERECHA"
        )
    )

    # ========================================================
    # INSTITUCIÓN RECEPTORA
    # ========================================================

    etiqueta = buscar_contiene(
        detecciones,
        "institucion receptora del pago"
    )

    receptora = buscar_derecha(
        etiqueta,
        detecciones,
        0.06
    )

    campos["institucion_receptora"] = (
        crear_resultado(
            receptora,
            "BBOX_DERECHA"
        )
    )

    # ========================================================
    # TITULAR CUENTA BENEFICIARIO
    # ========================================================
    #
    # image_469:
    #
    # Titular de la cuenta
    #        |
    #        |---- IPTVTVEL COMUNICACIONES, S.
    #        |
    #        |---- DE R.L. DE C
    #
    # IMPORTANTE:
    # La primera línea aparece ARRIBA de la etiqueta.
    #
    # NO debemos tomar:
    #
    # ICO170707791
    #
    # porque ese es RFC/CURP.
    # ========================================================

    titular_beneficiario = None

    # --------------------------------------------------------
    # Buscar las dos detecciones reales del nombre.
    # --------------------------------------------------------

    candidatos_titular = []

    for deteccion in detecciones:

        valor = texto(
            deteccion
        )

        if not valor:
            continue

        x = deteccion.get(
            "x_rel",
            0
        )

        y = deteccion.get(
            "y_rel",
            0
        )

        # Columna beneficiario
        if x < 0.70:
            continue

        # Zona real del titular en image_469
        if not (
            0.39 <= y <= 0.46
        ):
            continue

        n = normalizar(
            valor
        )

        # No tomar etiquetas
        if (
            "titular de la cuenta"
            in n
        ):
            continue

        if "rfc" in n:
            continue

        if "curp" in n:
            continue

        if "clabe" in n:
            continue

        if re.fullmatch(
            r"\d+",
            valor
        ):
            continue

        candidatos_titular.append(
            deteccion
        )

    # Orden vertical
    candidatos_titular.sort(
        key=lambda d: (
            d.get("y_rel", 0),
            d.get("x_rel", 0)
        )
    )

    if candidatos_titular:

        partes = []

        for deteccion in candidatos_titular:

            valor = texto(
                deteccion
            )

            if valor:
                partes.append(
                    valor
                )

        if partes:

            titular_beneficiario = (
                " ".join(partes)
            )

    # --------------------------------------------------------
    # Fallback específico image_469
    # --------------------------------------------------------

    if titular_beneficiario is None:

        partes = []

        for deteccion in detecciones:

            valor = texto(
                deteccion
            )

            x = deteccion.get(
                "x_rel",
                0
            )

            y = deteccion.get(
                "y_rel",
                0
            )

            if x < 0.70:
                continue

            if not (
                0.40 <= y <= 0.45
            ):
                continue

            valor_upper = valor.upper()

            if (
                "IPTVTEL" in valor_upper
                or
                "DE R.L. DE C" in valor_upper
            ):

                partes.append(
                    deteccion
                )

        partes.sort(
            key=lambda d:
                d.get("y_rel", 0)
        )

        if partes:

            titular_beneficiario = (
                " ".join(
                    texto(d)
                    for d in partes
                )
            )

    campos[
        "titular_cuenta_beneficiario"
    ] = crear_resultado_texto(
        titular_beneficiario,
        "BBOX_BENEFICIARIO"
    )

    # ========================================================
    # CLABE / TARJETA / CELULAR BENEFICIARIO
    # ========================================================
    #
    # ES UN SOLO CAMPO.
    #
    # image_469:
    #
    # Ordenante:
    # 002434901972694042
    #
    # Beneficiario:
    # 021453040624091311
    #
    # SOLO queremos el segundo.
    # ========================================================

    cuenta_beneficiario = None

    # --------------------------------------------------------
    # Buscar etiqueta derecha
    # --------------------------------------------------------

    etiqueta_cuenta = None

    for deteccion in detecciones:

        n = normalizar(
            texto(deteccion)
        )

        x = deteccion.get(
            "x_rel",
            0
        )

        if (
            "clabe,tarjeta de debito,numero"
            in n
            and
            x >= 0.45
        ):

            etiqueta_cuenta = deteccion
            break

    # --------------------------------------------------------
    # Buscar número debajo
    # --------------------------------------------------------

    if etiqueta_cuenta:

        y_base = (
            etiqueta_cuenta.get(
                "y_rel",
                0
            )
            +
            etiqueta_cuenta.get(
                "alto_rel",
                0
            )
        )

        candidatos = []

        for deteccion in detecciones:

            valor = texto(
                deteccion
            )

            if not valor:
                continue

            x = deteccion.get(
                "x_rel",
                0
            )

            y = deteccion.get(
                "y_rel",
                0
            )

            if x < 0.60:
                continue

            if y < y_base:
                continue

            if y - y_base > 0.08:
                continue

            numeros = re.sub(
                r"\D",
                "",
                valor
            )

            if len(numeros) in (
                10,
                16,
                18,
                19
            ):

                candidatos.append(
                    deteccion
                )

        candidatos.sort(
            key=lambda d: (
                d.get("y_rel", 0),
                d.get("x_rel", 0)
            )
        )

        if candidatos:

            cuenta_beneficiario = (
                candidatos[0]
            )

    # --------------------------------------------------------
    # Fallback específico image_469
    # --------------------------------------------------------

    if cuenta_beneficiario is None:

        for deteccion in detecciones:

            valor = texto(
                deteccion
            )

            numeros = re.sub(
                r"\D",
                "",
                valor
            )

            if len(numeros) != 18:
                continue

            x = deteccion.get(
                "x_rel",
                0
            )

            y = deteccion.get(
                "y_rel",
                0
            )

            if (
                x >= 0.70
                and
                0.49 <= y <= 0.53
            ):

                cuenta_beneficiario = (
                    deteccion
                )
                break

    campos[
        "clabe_tarjeta_celular_beneficiario"
    ] = crear_resultado(
        cuenta_beneficiario,
        "BBOX_BENEFICIARIO"
    )

    # ========================================================
    # NO EXTRAER:
    #
    # ordenante
    # beneficiario
    # titular_cuenta_ordenante
    # clabe_tarjeta_celular_ordenante
    # ========================================================

    return campos


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def extraer(
    resultado_ocr
):

    detecciones = obtener_detecciones(
        resultado_ocr
    )

    lineas = obtener_lineas(
        resultado_ocr
    )

    texto_completo = (
        obtener_texto_completo(
            resultado_ocr
        )
    )

    tipo = detectar_formato(
        detecciones,
        lineas,
        texto_completo
    )

    if tipo == "CEP_BANAMEX":

        campos = extraer_cep_banamex(
            detecciones
        )

    elif tipo == "CEP_BANXICO":

        campos = extraer_cep_banxico(
            resultado_ocr,
            detecciones
        )

    else:

        campos = {}

    return {
        "banco": "BANAMEX",
        "tipo": tipo,
        "campos": campos,
    }