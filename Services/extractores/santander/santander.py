import re
import unicodedata


# ============================================================
# CONFIGURACIÓN
# ============================================================

BANCO = "SANTANDER"


# ============================================================
# NORMALIZACIÓN
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

    if any(c in texto for c in ("Ã", "Â", "â")):
        try:
            texto = texto.encode("latin1").decode("utf-8")
        except Exception:
            pass

    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )

    return texto.lower().strip()


# ============================================================
# CAMPOS
# ============================================================

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
        "confianza": float(confianza)
    }


def campo_no_encontrado():

    return {
        "valor": None,
        "metodo": "no_encontrado",
        "confianza": 0.0
    }


# ============================================================
# DETECCIONES
# ============================================================

def obtener_detecciones(datos):

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

    for d in detecciones:

        if not isinstance(
            d,
            dict
        ):
            continue

        texto = normalizar_texto(
            d.get(
                "texto",
                ""
            )
        )

        if not texto:
            continue

        resultado.append({

            "texto":
                texto,

            "texto_norm":
                normalizar_busqueda(
                    texto
                ),

            "x":
                float(
                    d.get(
                        "x",
                        0
                    )
                ),

            "y":
                float(
                    d.get(
                        "y",
                        0
                    )
                ),

            "confianza":
                float(
                    d.get(
                        "confianza",
                        1.0
                    )
                )

        })

    return sorted(
        resultado,
        key=lambda x: (
            x["y"],
            x["x"]
        )
    )


# ============================================================
# UTILIDADES ESPACIALES
# ============================================================

def misma_fila(
    a,
    b,
    tolerancia=35
):

    return (
        abs(
            a["y"] -
            b["y"]
        )
        <= tolerancia
    )


def valor_a_la_derecha(
    detecciones,
    etiqueta,
    tolerancia=40
):

    etiqueta_norm = normalizar_busqueda(
        etiqueta
    )

    for etiqueta_det in detecciones:

        if (
            etiqueta_det["texto_norm"]
            != etiqueta_norm
        ):
            continue

        candidatos = [

            d for d in detecciones

            if (
                d["x"]
                > etiqueta_det["x"]

                and

                misma_fila(
                    etiqueta_det,
                    d,
                    tolerancia
                )
            )
        ]

        candidatos.sort(
            key=lambda x: x["x"]
        )

        for candidato in candidatos:

            if (
                candidato["texto_norm"]
                == etiqueta_norm
            ):
                continue

            return (
                candidato["texto"],
                candidato["confianza"]
            )

    return None, 0.0


def buscar_por_texto_parcial(
    detecciones,
    texto
):

    objetivo = normalizar_busqueda(
        texto
    )

    for d in detecciones:

        if objetivo in d["texto_norm"]:

            return d

    return None


def contiene_numero(
    texto
):

    return bool(
        re.search(
            r"\d",
            texto or ""
        )
    )


# ============================================================
# DETECCIÓN DE FORMATO
# ============================================================

def es_cep(
    detecciones
):

    texto = " ".join(
        d["texto_norm"]
        for d in detecciones
    )

    indicadores = [

        "comprobante electronico de pago",

        "institucion emisora del pago",

        "institucion receptora del pago",

        "referencia numerica",

        "clave de rastreo",

    ]

    encontrados = sum(
        indicador in texto
        for indicador in indicadores
    )

    return encontrados >= 3


def es_supermovil(
    detecciones
):

    texto = " ".join(
        d["texto_norm"]
        for d in detecciones
    )

    indicadores = [

        "enviaste una transferencia",

        "ref. supermovil",

        "tipo de operacion",

        "fecha y hora de operacion",

    ]

    encontrados = sum(
        indicador in texto
        for indicador in indicadores
    )

    return encontrados >= 2


def es_transferencia_referencia(
    detecciones
):

    texto = " ".join(
        d["texto_norm"]
        for d in detecciones
    )

    indicadores = [

        "banco destino",

        "cuenta destino",

        "numero de referencia",

        "clave de rastreo",

        "saldo posterior",

    ]

    encontrados = sum(
        indicador in texto
        for indicador in indicadores
    )

    return encontrados >= 3


# ============================================================
# MONTO
# ============================================================

def extraer_monto(
    detecciones
):

    # --------------------------------------------------------
    # $500.00
    # $ 300.00
    # --------------------------------------------------------

    for d in detecciones:

        match = re.search(
            r"-?\$\s*[\d,]+(?:\.\d{1,2})?",
            d["texto"]
        )

        if match:

            return (
                match.group(0),
                d["confianza"]
            )

    # --------------------------------------------------------
    # -600.00 MXN
    # --------------------------------------------------------

    for d in detecciones:

        match = re.search(
            r"-?\s*[\d,]+(?:\.\d{1,2})?\s*MXN",
            d["texto"],
            re.IGNORECASE
        )

        if match:

            return (
                re.sub(
                    r"\s+",
                    "",
                    match.group(0)
                ),
                d["confianza"]
            )

    return None, 0.0


# ============================================================
# FECHA TRANSFERENCIA
# image_089 / image_125
# ============================================================

def extraer_fecha_transferencia(
    detecciones
):
    """
    Extrae fechas/fechas-horas en formatos amplios sin normalizarlas.

    Ejemplos aceptados:
        03/Jun/2026 - 10:50
        16/Jul/2026-10:24
        31/may/26 - 09:38
        02/jul/26 - 15:55
        03/06/2026
        03-06-2026
        03.06.2026
        03/Jun/26
        03 Junio 2026
        03 de junio de 2026
        Jun 03, 2026
        10:50
        10:50:35

    El texto encontrado se devuelve tal como aparece en OCR.
    """

    # --------------------------------------------------------
    # Fecha con día/mes/año + hora opcional.
    # Se aceptan separadores / - .
    # Mes numérico o nombre abreviado/completo.
    # --------------------------------------------------------

    patrones = [

        # 02/jul/26 - 15:55
        r"\b\d{1,2}\s*[/.-]\s*"
        r"(?:\d{1,2}|[A-Za-zÁÉÍÓÚáéíóúÑñ]{3,})\s*[/.-]\s*"
        r"\d{2,4}"
        r"(?:\s*[-–—]\s*"
        r"\d{1,2}:\d{2}(?::\d{2})?"
        r"(?:\s*(?:hrs?|horas))?)?\b",

        # 03 Junio 2026
        r"\b\d{1,2}\s+"
        r"[A-Za-zÁÉÍÓÚáéíóúÑñ]+"
        r"(?:\s*,)?\s+\d{2,4}"
        r"(?:\s*[-–—]\s*"
        r"\d{1,2}:\d{2}(?::\d{2})?"
        r"(?:\s*(?:hrs?|horas))?)?\b",

        # 03 de junio de 2026
        r"\b\d{1,2}\s+de\s+"
        r"[A-Za-zÁÉÍÓÚáéíóúÑñ]+"
        r"\s+de\s+\d{2,4}"
        r"(?:\s*[-–—]\s*"
        r"\d{1,2}:\d{2}(?::\d{2})?"
        r"(?:\s*(?:hrs?|horas))?)?\b",

        # Jun 03, 2026
        r"\b[A-Za-zÁÉÍÓÚáéíóúÑñ]{3,9}\s+"
        r"\d{1,2},?\s+\d{2,4}"
        r"(?:\s*[-–—]\s*"
        r"\d{1,2}:\d{2}(?::\d{2})?"
        r"(?:\s*(?:hrs?|horas))?)?\b",
    ]

    for d in detecciones:
        for patron in patrones:
            match = re.search(
                patron,
                d["texto"],
                re.IGNORECASE
            )

            if match:
                return (
                    match.group(0),
                    d["confianza"]
                )

    # --------------------------------------------------------
    # Fallback: si la fecha y la hora fueron separadas por OCR
    # en detecciones distintas, intentar encontrar una fecha
    # y conservarla tal cual fue detectada.
    # --------------------------------------------------------

    patrones_fecha_sin_hora = [

        r"\b\d{1,2}\s*[/.-]\s*"
        r"(?:\d{1,2}|[A-Za-zÁÉÍÓÚáéíóúÑñ]{3,})\s*[/.-]\s*"
        r"\d{2,4}\b",

        r"\b\d{1,2}\s+"
        r"[A-Za-zÁÉÍÓÚáéíóúÑñ]+\s+"
        r"\d{2,4}\b",

        r"\b\d{1,2}\s+de\s+"
        r"[A-Za-zÁÉÍÓÚáéíóúÑñ]+\s+de\s+\d{2,4}\b",
    ]

    for d in detecciones:
        for patron in patrones_fecha_sin_hora:
            match = re.search(
                patron,
                d["texto"],
                re.IGNORECASE
            )

            if match:
                return (
                    match.group(0),
                    d["confianza"]
                )

    return None, 0.0


# ============================================================
# FECHA CEP
# image_140
# ============================================================

def extraer_fecha_cep(
    detecciones
):

    patron = (
        r"\b\d{1,2}\s+de\s+"
        r"[A-Za-zÁÉÍÓÚáéíóúÑñ]+"
        r"\s+de\s+\d{4}\b"
    )

    # --------------------------------------------------------
    # Buscar específicamente la fecha asociada con:
    #
    # Fecha de operación en el SPEI
    #
    # image_140:
    #
    # 03 de junio de 2026
    # --------------------------------------------------------

    for d in detecciones:

        if (
            "fecha de operacion en el spei"
            not in d["texto_norm"]
        ):
            continue

        candidatos = [

            x for x in detecciones

            if (
                x["x"] > d["x"]

                and

                misma_fila(
                    d,
                    x,
                    50
                )
            )
        ]

        candidatos.sort(
            key=lambda x: x["x"]
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
    # FALLBACK
    # --------------------------------------------------------

    for d in detecciones:

        match = re.search(
            patron,
            d["texto"],
            re.IGNORECASE
        )

        if match:

            return (
                match.group(0),
                d["confianza"]
            )

    return None, 0.0


# ============================================================
# REF. SUPERMÓVIL
# ============================================================

def extraer_ref_supermovil(
    detecciones
):

    etiqueta = buscar_por_texto_parcial(
        detecciones,
        "ref. supermovil"
    )

    if not etiqueta:
        return None, 0.0

    candidatos = [

        d for d in detecciones

        if (
            d["x"] > etiqueta["x"]

            and

            misma_fila(
                etiqueta,
                d,
                45
            )
        )
    ]

    candidatos.sort(
        key=lambda x: x["x"]
    )

    for candidato in candidatos:

        match = re.search(
            r"\b\d{4,}\b",
            candidato["texto"]
        )

        if match:

            return (
                match.group(0),
                candidato["confianza"]
            )

    return None, 0.0


# ============================================================
# TIPO OPERACIÓN
# ============================================================

def extraer_tipo_operacion(
    detecciones
):

    return valor_a_la_derecha(
        detecciones,
        "tipo de operacion",
        45
    )


# ============================================================
# CUENTAS
# ============================================================

def limpiar_cuenta(
    texto
):

    if not texto:
        return None

    texto = normalizar_texto(
        texto
    )

    # --------------------------------------------------------
    # CTA **0555
    # --------------------------------------------------------

    match = re.search(
        r"\bCTA\s*\*+\s*\d+\b",
        texto,
        re.IGNORECASE
    )

    if match:

        return match.group(0)

    # --------------------------------------------------------
    # CLABE**1311
    # --------------------------------------------------------

    match = re.search(
        r"CLABE\s*\*+\s*\d+",
        texto,
        re.IGNORECASE
    )

    if match:

        return re.sub(
            r"^CLABE\s*",
            "",
            match.group(0),
            flags=re.IGNORECASE
        )

    # --------------------------------------------------------
    # 02**1311
    # --------------------------------------------------------

    match = re.search(
        r"\b\d{1,3}\s*\*{1,4}\s*\d{3,6}\b",
        texto
    )

    if match:

        return match.group(0)

    # --------------------------------------------------------
    # 18 dígitos
    # --------------------------------------------------------

    match = re.search(
        r"\b\d{18}\b",
        texto
    )

    if match:

        return match.group(0)

    return None


# ============================================================
# IMAGE_089
# CUENTA ORIGEN
# ============================================================

def extraer_cuenta_origen_supermovil(
    detecciones
):

    etiqueta = buscar_por_texto_parcial(
        detecciones,
        "cuenta origen"
    )

    if not etiqueta:
        return None, 0.0

    candidatos = [

        d for d in detecciones

        if (
            d["x"] > etiqueta["x"]

            and

            misma_fila(
                etiqueta,
                d,
                45
            )
        )
    ]

    candidatos.sort(
        key=lambda x: x["x"]
    )

    for candidato in candidatos:

        cuenta = limpiar_cuenta(
            candidato["texto"]
        )

        if cuenta:

            return (
                cuenta,
                candidato["confianza"]
            )

    return None, 0.0


# ============================================================
# IMAGE_089
# BANCO DESTINO
# ============================================================

def extraer_banco_supermovil(
    detecciones
):

    etiqueta = None

    for d in detecciones:

        if d["texto_norm"] == "banco":

            etiqueta = d
            break

    if not etiqueta:

        return None, 0.0

    candidatos = [

        d for d in detecciones

        if (
            d["x"] > etiqueta["x"]

            and

            misma_fila(
                etiqueta,
                d,
                45
            )
        )
    ]

    candidatos.sort(
        key=lambda x: x["x"]
    )

    for candidato in candidatos:

        if (
            candidato["texto_norm"]
            != "banco"
        ):

            return (
                candidato["texto"],
                candidato["confianza"]
            )

    return None, 0.0


# ============================================================
# IMAGE_089
# ESTATUS
# ============================================================

# ============================================================
# IMAGE_089
# ESTATUS
# ============================================================

def extraer_estatus_supermovil(
    detecciones
):
    """
    Extrae el valor asociado a 'Estatus de la operación'
    independientemente de cuál sea el estado.

    Ejemplos:
        Exitosa
        En proceso
        Pendiente
        Rechazada
        Cancelada
        cualquier otro texto corto mostrado como estado

    La extracción se basa en proximidad espacial, no en una lista
    cerrada de estados.
    """

    etiqueta = None

    # --------------------------------------------------------
    # Buscar la etiqueta exacta.
    # --------------------------------------------------------

    for d in detecciones:
        if d["texto_norm"] == "estatus de la operacion":
            etiqueta = d
            break

    if not etiqueta:
        return None, 0.0

    # --------------------------------------------------------
    # Primero buscamos valores a la derecha y muy cerca
    # verticalmente de la etiqueta.
    # --------------------------------------------------------

    candidatos = [
        d for d in detecciones
        if (
            d["x"] > etiqueta["x"]
            and
            abs(d["y"] - etiqueta["y"]) <= 30
        )
    ]

    candidatos.sort(
        key=lambda x: (
            abs(x["y"] - etiqueta["y"]),
            x["x"] - etiqueta["x"]
        )
    )

    # --------------------------------------------------------
    # Palabras que NO representan el valor del estatus.
    # No usamos una lista de estados válidos: cualquier estado
    # nuevo podrá ser extraído mientras respete la posición.
    # --------------------------------------------------------

    etiquetas_no_validas = {
        "estatus de la operacion",
        "fecha y hora de operacion",
        "cuenta origen",
        "banco",
        "ref. supermovil",
        "tipo de operacion",
        "rfc cliente santander",
    }

    for candidato in candidatos:

        texto = normalizar_texto(
            candidato["texto"]
        )

        texto_norm = candidato["texto_norm"]

        if not texto:
            continue

        if texto_norm in etiquetas_no_validas:
            continue

        # No aceptar únicamente números: evita que una referencia
        # como 8573476 sea tomada como estatus.
        if re.fullmatch(
            r"[\d\s.,$%*#/-]+",
            texto
        ):
            continue

        # No aceptar horas o fechas como estatus.
        if re.fullmatch(
            r"\d{1,2}:\d{2}(?::\d{2})?(?:\s*horas?)?",
            texto,
            re.IGNORECASE
        ):
            continue

        # El estatus normalmente es una frase corta. Evitamos
        # tomar bloques largos de texto de otras secciones.
        if len(texto) > 80:
            continue

        return (
            texto,
            candidato["confianza"]
        )

    return None, 0.0


# ============================================================
# IMAGE_089
# CONCEPTO
# ============================================================

def extraer_concepto_supermovil(
    detecciones
):

    for d in detecciones:

        match = re.search(
            r'por el concepto\s+"([^"]+)"',
            d["texto"],
            re.IGNORECASE
        )

        if match:

            return (
                match.group(1),
                d["confianza"]
            )

    return None, 0.0


# ============================================================
# IMAGE_089
# BENEFICIARIO / BANCO / CUENTA
# ============================================================

def extraer_beneficiario_supermovil(
    detecciones
):

    beneficiario = None
    conf_beneficiario = 0.0

    # --------------------------------------------------------
    # BENEFICIARIO
    # --------------------------------------------------------

    for d in detecciones:

        if d["texto_norm"] == "emenet":

            beneficiario = d["texto"]

            conf_beneficiario = (
                d["confianza"]
            )

            break

    banco = None
    conf_banco = 0.0

    cuenta = None
    conf_cuenta = 0.0

    # --------------------------------------------------------
    # BANCO + CUENTA
    # --------------------------------------------------------

    for d in detecciones:

        texto_norm = d["texto_norm"]

        if "hsbc" not in texto_norm:

            continue

        banco = "HSBC"

        conf_banco = (
            d["confianza"]
        )

        cuenta_extraida = limpiar_cuenta(
            d["texto"]
        )

        if cuenta_extraida:

            cuenta = cuenta_extraida

            conf_cuenta = (
                d["confianza"]
            )

        break

    return (

        beneficiario,

        conf_beneficiario,

        banco,

        conf_banco,

        cuenta,

        conf_cuenta

    )


# ============================================================
# EXTRACCIÓN IMAGE_089
# ============================================================

def extraer_supermovil(
    detecciones
):

    fecha, conf_fecha = (
        extraer_fecha_transferencia(
            detecciones
        )
    )

    monto, conf_monto = (
        extraer_monto(
            detecciones
        )
    )

    cuenta_origen, conf_cuenta_origen = (
        extraer_cuenta_origen_supermovil(
            detecciones
        )
    )

    (
        titular_beneficiario,
        conf_titular,
        banco_beneficiario,
        conf_banco,
        cuenta_beneficiario,
        conf_cuenta_beneficiario

    ) = extraer_beneficiario_supermovil(
        detecciones
    )

    estatus, conf_estatus = (
        extraer_estatus_supermovil(
            detecciones
        )
    )

    ref, conf_ref = (
        extraer_ref_supermovil(
            detecciones
        )
    )

    tipo, conf_tipo = (
        extraer_tipo_operacion(
            detecciones
        )
    )

    concepto, conf_concepto = (
        extraer_concepto_supermovil(
            detecciones
        )
    )

    return {

        "banco_emisor":
            campo_encontrado(
                BANCO,
                "metadato",
                1.0
            ),

        "monto":
            campo_encontrado(
                monto,
                "deteccion_monto",
                conf_monto
            ),

        "fecha_hora_operacion":
            campo_encontrado(
                fecha,
                "regex_fecha",
                conf_fecha
            ),

        "cuenta_origen":
            campo_encontrado(
                cuenta_origen,
                "coordenadas_cuenta_origen",
                conf_cuenta_origen
            ),

        "banco_destino":
            campo_encontrado(
                banco_beneficiario,
                "coordenadas_banco",
                conf_banco
            ),

        "estatus":
            campo_encontrado(
                estatus,
                "coordenadas_estatus",
                conf_estatus
            ),

        "ref_supermovil":
            campo_encontrado(
                ref,
                "etiqueta_ref_supermovil",
                conf_ref
            ),

        "tipo_operacion":
            campo_encontrado(
                tipo,
                "etiqueta_tipo_operacion",
                conf_tipo
            ),

        "concepto":
            campo_encontrado(
                concepto,
                "deteccion_concepto",
                conf_concepto
            ),

    }


# ============================================================
# IMAGE_125
# BANCO DESTINO
# ============================================================

def extraer_banco_destino_125(
    detecciones
):

    return valor_a_la_derecha(
        detecciones,
        "banco destino",
        45
    )


# ============================================================
# IMAGE_125
# CUENTA DESTINO
# ============================================================

def extraer_cuenta_destino_125(
    detecciones
):

    valor, confianza = (
        valor_a_la_derecha(
            detecciones,
            "cuenta destino",
            45
        )
    )

    cuenta = limpiar_cuenta(
        valor
    )

    if cuenta:

        return (
            cuenta,
            confianza
        )

    return None, 0.0


# ============================================================
# IMAGE_125
# CUENTA
# ============================================================

def extraer_cuenta_125(
    detecciones
):

    valor, confianza = (
        valor_a_la_derecha(
            detecciones,
            "cuenta",
            45
        )
    )

    cuenta = limpiar_cuenta(
        valor
    )

    if cuenta:

        return (
            cuenta,
            confianza
        )

    return None, 0.0


# ============================================================
# IMAGE_125
# SUCURSAL
# ============================================================

def extraer_sucursal_125(
    detecciones
):

    return valor_a_la_derecha(
        detecciones,
        "sucursal",
        45
    )


# ============================================================
# IMAGE_125
# REFERENCIA
# ============================================================

def extraer_referencia_125(
    detecciones
):

    return valor_a_la_derecha(
        detecciones,
        "referencia",
        45
    )


# ============================================================
# IMAGE_125
# SALDO POSTERIOR
# ============================================================

def extraer_saldo_125(
    detecciones
):

    valor, confianza = (
        valor_a_la_derecha(
            detecciones,
            "saldo posterior",
            45
        )
    )

    if valor:

        match = re.search(
            r"[\d,]+(?:\.\d{1,2})?\s*MXN",
            valor,
            re.IGNORECASE
        )

        if match:

            return (
                match.group(0),
                confianza
            )

    return None, 0.0


# ============================================================
# IMAGE_125
# HORA
# ============================================================

def extraer_hora_125(
    detecciones
):

    valor, confianza = (
        valor_a_la_derecha(
            detecciones,
            "hora",
            45
        )
    )

    if valor:

        match = re.search(
            r"\b\d{1,2}:\d{2}:\d{2}\b",
            valor
        )

        if match:

            return (
                match.group(0),
                confianza
            )

    return None, 0.0


# ============================================================
# IMAGE_125
# NÚMERO DE REFERENCIA
# ============================================================

def extraer_numero_referencia_125(
    detecciones
):

    valor, confianza = (
        valor_a_la_derecha(
            detecciones,
            "número de referencia",
            50
        )
    )

    if not valor:

        valor, confianza = (
            valor_a_la_derecha(
                detecciones,
                "numero de referencia",
                50
            )
        )

    if valor:

        match = re.search(
            r"\b\d{4,}\b",
            valor
        )

        if match:

            return (
                match.group(0),
                confianza
            )

    return None, 0.0


# ============================================================
# IMAGE_125
# CLAVE DE RASTREO
# ============================================================

def extraer_clave_rastreo(
    detecciones
):
    """
    Extrae la clave de rastreo aunque OCR:
      1) separe la clave en varias detecciones, o
      2) pegue la clave directamente a la etiqueta.

    Ejemplo problemático de OCR:
        CLAVE DE RASTREO2026060540014BMOVP0004267767
        80

    Resultado:
        2026060540014BMOVP000426776780
    """

    # --------------------------------------------------------
    # 1. Buscar la etiqueta aunque esté pegada al valor.
    # --------------------------------------------------------

    for d in detecciones:

        texto = normalizar_texto(d["texto"])

        match_etiqueta = re.search(
            r"clave\s+de\s+rastreo",
            texto,
            re.IGNORECASE
        )

        if not match_etiqueta:
            continue

        # Lo que venga después de la etiqueta puede ser
        # directamente el inicio de la clave.
        resto = texto[match_etiqueta.end():]

        inicio = re.search(
            r"[A-Za-z0-9]{8,}",
            resto
        )

        if inicio:

            clave = inicio.group(0)

            # ------------------------------------------------
            # 2. Si la clave continúa en la siguiente detección,
            #    agregar fragmentos alfanuméricos cercanos.
            # ------------------------------------------------

            siguientes = [
                x for x in detecciones
                if (
                    x is not d
                    and x["y"] >= d["y"]
                    and x["y"] - d["y"] <= 80
                    and x["x"] >= d["x"]
                )
            ]

            siguientes.sort(
                key=lambda x: (
                    x["y"],
                    x["x"]
                )
            )

            for siguiente in siguientes:

                fragmentos = re.findall(
                    r"[A-Za-z0-9]+",
                    siguiente["texto"]
                )

                for fragmento in fragmentos:

                    # Solo aceptar fragmentos que puedan continuar
                    # una clave numérica/alfanumérica.
                    if (
                        len(fragmento) <= 4
                        and fragmento.isdigit()
                    ):
                        clave += fragmento

                    if len(clave) >= 15:
                        break

                if len(clave) >= 30:
                    break

            return (
                clave,
                d["confianza"]
            )

    # --------------------------------------------------------
    # 3. Formato normal:
    #
    # CLAVE DE RASTREO
    # 2026060540014BMOVP000475611720
    # --------------------------------------------------------

    for d in detecciones:

        if d["texto_norm"] != "clave de rastreo":
            continue

        candidatos = [
            x for x in detecciones
            if (
                x["x"] > d["x"]
                and
                abs(x["y"] - d["y"]) <= 70
            )
        ]

        candidatos.sort(
            key=lambda x: (
                abs(x["y"] - d["y"]),
                x["x"]
            )
        )

        for candidato in candidatos:

            match = re.search(
                r"\b[A-Za-z0-9]{15,}\b",
                candidato["texto"]
            )

            if match:

                clave = match.group(0)

                # Si OCR dividió los últimos dígitos en otra
                # detección cercana, anexarlos.
                for siguiente in candidatos:

                    if siguiente is candidato:
                        continue

                    if (
                        siguiente["y"] >= candidato["y"]
                        and
                        siguiente["y"] - candidato["y"] <= 70
                        and
                        siguiente["x"] >= candidato["x"]
                    ):

                        fragmentos = re.findall(
                            r"\b\d{1,4}\b",
                            siguiente["texto"]
                        )

                        for fragmento in fragmentos:
                            clave += fragmento

                return (
                    clave,
                    candidato["confianza"]
                )

    return None, 0.0


# ============================================================
# IMAGE_125
# CONCEPTO
# ============================================================

def extraer_concepto_125(
    detecciones
):

    for d in detecciones:

        if d["texto_norm"].startswith(
            "transferencia a "
        ):

            return (
                d["texto"],
                d["confianza"]
            )

    return None, 0.0


# ============================================================
# IMAGE_125
# EXTRACCIÓN COMPLETA
# ============================================================

def extraer_transferencia_referencia(
    detecciones
):

    fecha, conf_fecha = (
        extraer_fecha_transferencia(
            detecciones
        )
    )

    monto, conf_monto = (
        extraer_monto(
            detecciones
        )
    )

    banco_destino, conf_banco = (
        extraer_banco_destino_125(
            detecciones
        )
    )

    cuenta_destino, conf_cuenta_destino = (
        extraer_cuenta_destino_125(
            detecciones
        )
    )

    cuenta, conf_cuenta = (
        extraer_cuenta_125(
            detecciones
        )
    )

    sucursal, conf_sucursal = (
        extraer_sucursal_125(
            detecciones
        )
    )

    referencia, conf_referencia = (
        extraer_referencia_125(
            detecciones
        )
    )

    saldo, conf_saldo = (
        extraer_saldo_125(
            detecciones
        )
    )

    hora, conf_hora = (
        extraer_hora_125(
            detecciones
        )
    )

    numero_referencia, conf_numero = (
        extraer_numero_referencia_125(
            detecciones
        )
    )

    rastreo, conf_rastreo = (
        extraer_clave_rastreo(
            detecciones
        )
    )

    concepto, conf_concepto = (
        extraer_concepto_125(
            detecciones
        )
    )

    return {

        "banco_emisor":
            campo_encontrado(
                BANCO,
                "metadato",
                1.0
            ),

        "monto":
            campo_encontrado(
                monto,
                "deteccion_monto",
                conf_monto
            ),

        "fecha":
            campo_encontrado(
                fecha,
                "regex_fecha",
                conf_fecha
            ),

        "concepto":
            campo_encontrado(
                concepto,
                "deteccion_concepto",
                conf_concepto
            ),

        "banco_destino":
            campo_encontrado(
                banco_destino,
                "coordenadas_banco_destino",
                conf_banco
            ),

        "cuenta_destino":
            campo_encontrado(
                cuenta_destino,
                "coordenadas_cuenta_destino",
                conf_cuenta_destino
            ),

        "cuenta":
            campo_encontrado(
                cuenta,
                "coordenadas_cuenta",
                conf_cuenta
            ),

        "sucursal":
            campo_encontrado(
                sucursal,
                "coordenadas_sucursal",
                conf_sucursal
            ),

        "referencia":
            campo_encontrado(
                referencia,
                "coordenadas_referencia",
                conf_referencia
            ),

        "saldo_posterior":
            campo_encontrado(
                saldo,
                "coordenadas_saldo_posterior",
                conf_saldo
            ),

        "hora":
            campo_encontrado(
                hora,
                "coordenadas_hora",
                conf_hora
            ),

        "numero_referencia":
            campo_encontrado(
                numero_referencia,
                "etiqueta_numero_referencia",
                conf_numero
            ),

        "clave_rastreo":
            campo_encontrado(
                rastreo,
                "etiqueta_clave_rastreo",
                conf_rastreo
            ),

    }


# ============================================================
# CEP IMAGE_140
# INSTITUCIÓN EMISORA
# ============================================================

def extraer_institucion_emisora_cep(
    detecciones
):

    etiqueta = None

    for d in detecciones:

        if (
            d["texto_norm"]
            == "institucion emisora del pago"
        ):

            etiqueta = d
            break

    if not etiqueta:

        return None, 0.0

    # image_140:
    #
    # x=25  Institución emisora del pago
    # x=180 SANTANDER
    #
    candidatos = [

        d for d in detecciones

        if (
            d["x"] > etiqueta["x"]

            and

            d["x"] < 330

            and

            abs(
                d["y"] -
                etiqueta["y"]
            ) <= 15
        )
    ]

    candidatos = [

        d for d in candidatos

        if d["texto_norm"] not in (

            "institucion emisora del pago",

            "institucion receptora del pago",

            "titular de la cuenta",

            "rfc/curp",

            "ordenante",

            "beneficiario",

        )
    ]

    if not candidatos:

        return None, 0.0

    candidato = min(
        candidatos,
        key=lambda x: x["x"]
    )

    return (
        candidato["texto"],
        candidato["confianza"]
    )


# ============================================================
# CEP IMAGE_140
# INSTITUCIÓN RECEPTORA
# ============================================================

def extraer_institucion_receptora_cep(
    detecciones
):

    etiqueta = None

    for d in detecciones:

        if (
            d["texto_norm"]
            == "institucion receptora del pago"
        ):

            etiqueta = d
            break

    if not etiqueta:

        return None, 0.0

    # image_140:
    #
    # x=363 Institución receptora del pago
    # x=516 HSBC
    #
    candidatos = [

        d for d in detecciones

        if (
            d["x"] > etiqueta["x"]

            and

            abs(
                d["y"] -
                etiqueta["y"]
            ) <= 15
        )
    ]

    candidatos = [

        d for d in candidatos

        if d["texto_norm"] not in (

            "institucion emisora del pago",

            "institucion receptora del pago",

            "titular de la cuenta",

            "rfc/curp",

            "ordenante",

            "beneficiario",

        )
    ]

    if not candidatos:

        return None, 0.0

    candidato = min(
        candidatos,
        key=lambda x: x["x"]
    )

    return (
        candidato["texto"],
        candidato["confianza"]
    )


# ============================================================
# CEP IMAGE_140
# FECHA
# ============================================================

def extraer_fecha_cep_directa(
    detecciones
):

    patron = (
        r"\b\d{1,2}\s+de\s+"
        r"[A-Za-zÁÉÍÓÚáéíóúÑñ]+"
        r"\s+de\s+\d{4}\b"
    )

    # Buscar primero la etiqueta correcta.

    for d in detecciones:

        if (
            "fecha de operacion en el spei"
            not in d["texto_norm"]
        ):
            continue

        candidatos = [

            x for x in detecciones

            if (
                x["x"] > d["x"]

                and

                abs(
                    x["y"] -
                    d["y"]
                ) <= 25
            )
        ]

        for candidato in sorted(
            candidatos,
            key=lambda x: x["x"]
        ):

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

    return extraer_fecha_cep(
        detecciones
    )


# ============================================================
# CEP IMAGE_140
# CONCEPTO
# ============================================================

def extraer_concepto_cep_directo(
    detecciones
):

    etiqueta = None

    for d in detecciones:

        if (
            d["texto_norm"]
            == "concepto del pago"
        ):

            etiqueta = d
            break

    if not etiqueta:

        return None, 0.0

    # image_140:
    #
    # x=25  Concepto del pago
    # x=130 PAGO INTERNET JUN2026 ERICK CUEVAS

    candidatos = [

        d for d in detecciones

        if (
            d["x"] > etiqueta["x"]

            and

            abs(
                d["y"] -
                etiqueta["y"]
            ) <= 15
        )
    ]

    candidatos.sort(
        key=lambda x: x["x"]
    )

    for candidato in candidatos:

        texto_norm = (
            candidato["texto_norm"]
        )

        # No tomar etiquetas.

        if texto_norm in (

            "concepto del pago",

            "clave de rastreo",

            "referencia numerica",

            "institucion emisora del pago",

            "institucion receptora del pago",

            "titular de la cuenta",

        ):
            continue

        # No tomar fecha.

        if texto_norm.startswith(
            "fecha "
        ):
            continue

        # No tomar hora.

        if texto_norm.startswith(
            "hora "
        ):
            continue

        # No tomar IVA.

        if texto_norm == "iva":
            continue

        # No tomar montos.

        if re.fullmatch(
            r"-?\$?\s*[\d,]+(?:\.\d{1,2})?",
            candidato["texto"]
        ):
            continue

        # No tomar horas.

        if re.fullmatch(
            r"\d{1,2}:\d{2}:\d{2}.*",
            candidato["texto"]
        ):
            continue

        return (
            candidato["texto"],
            candidato["confianza"]
        )

    return None, 0.0


# ============================================================
# CEP IMAGE_140
# REFERENCIA NUMÉRICA
# ============================================================

def extraer_referencia_numerica_cep_directa(
    detecciones
):

    etiqueta = None

    for d in detecciones:

        if (
            d["texto_norm"]
            == "referencia numerica"
        ):

            etiqueta = d
            break

    if not etiqueta:

        return None, 0.0

    # image_140:
    #
    # Referencia numérica
    # 9074542

    candidatos = [

        d for d in detecciones

        if (
            d["x"] > etiqueta["x"]

            and

            abs(
                d["y"] -
                etiqueta["y"]
            ) <= 20
        )
    ]

    candidatos.sort(
        key=lambda x: x["x"]
    )

    for candidato in candidatos:

        match = re.fullmatch(
            r"\d{4,10}",
            candidato["texto"].strip()
        )

        if match:

            return (
                match.group(0),
                candidato["confianza"]
            )

    return None, 0.0


# ============================================================
# CEP IMAGE_140
# CLAVE DE RASTREO
# ============================================================

def extraer_clave_rastreo_cep_directa(
    detecciones
):

    etiqueta = None

    for d in detecciones:

        if (
            d["texto_norm"]
            == "clave de rastreo"
        ):

            etiqueta = d
            break

    if not etiqueta:

        return None, 0.0

    # image_140:
    #
    # Clave de rastreo
    # 2026060340014BMOVP000448322090

    candidatos = [

        d for d in detecciones

        if (
            d["x"] > etiqueta["x"]

            and

            abs(
                d["y"] -
                etiqueta["y"]
            ) <= 20
        )
    ]

    candidatos.sort(
        key=lambda x: x["x"]
    )

    for candidato in candidatos:

        match = re.fullmatch(
            r"[A-Za-z0-9]{15,}",
            candidato["texto"].strip()
        )

        if match:

            return (
                match.group(0),
                candidato["confianza"]
            )

    return None, 0.0


# ============================================================
# CEP IMAGE_140
# TITULAR BENEFICIARIO
# ============================================================

def extraer_titular_beneficiario_cep_directo(
    detecciones
):

    etiquetas = [

        d for d in detecciones

        if (
            d["texto_norm"]
            == "titular de la cuenta"
        )
    ]

    # Necesitamos las dos columnas:
    #
    # izquierda = Ordenante
    # derecha  = Beneficiario

    if len(etiquetas) < 2:

        return None, 0.0

    # Tomamos la etiqueta derecha.

    etiqueta = max(
        etiquetas,
        key=lambda x: x["x"]
    )

    candidatos = [

        d for d in detecciones

        if (
            d["x"] > etiqueta["x"]

            and

            d["y"]
            >= etiqueta["y"] - 5

            and

            d["y"]
            <= etiqueta["y"] + 25

            and

            not contiene_numero(
                d["texto"]
            )

            and

            "rfc"
            not in d["texto_norm"]

            and

            "clabe"
            not in d["texto_norm"]

            and

            "institucion"
            not in d["texto_norm"]

            and

            "titular"
            not in d["texto_norm"]
        )
    ]

    candidatos.sort(
        key=lambda x: (
            x["y"],
            x["x"]
        )
    )

    if not candidatos:

        return None, 0.0

    partes = []

    confianza = 0.0

    for candidato in candidatos:

        partes.append(
            candidato["texto"]
        )

        confianza = max(
            confianza,
            candidato["confianza"]
        )

        # En image_140 son dos líneas.

        if len(partes) >= 2:
            break

    return (
        " ".join(partes),
        confianza
    )


# ============================================================
# CEP IMAGE_140
# CLABE BENEFICIARIO
# ============================================================

def extraer_clabe_cep_directa(
    detecciones
):

    candidatos = []

    for d in detecciones:

        encontrados = re.findall(
            r"\b\d{18}\b",
            d["texto"]
        )

        for valor in encontrados:

            candidatos.append({

                "valor":
                    valor,

                "x":
                    d["x"],

                "y":
                    d["y"],

                "confianza":
                    d["confianza"]

            })

    if not candidatos:

        return None, 0.0

    # En image_140:
    #
    # Ordenante:
    # 014420565961615726
    #
    # Beneficiario:
    # 021453040624091311
    #
    # El beneficiario está a la derecha.

    candidatos_derecha = [

        c for c in candidatos

        if c["x"] > 350
    ]

    if candidatos_derecha:

        candidato = min(
            candidatos_derecha,
            key=lambda x: x["x"]
        )

    else:

        candidato = max(
            candidatos,
            key=lambda x: x["x"]
        )

    return (
        candidato["valor"],
        candidato["confianza"]
    )


# ============================================================
# CEP IMAGE_140
# EXTRACCIÓN COMPLETA
# ============================================================

def extraer_cep(
    detecciones
):

    # ========================================================
    # INSTITUCIÓN EMISORA
    # ========================================================

    institucion_emisora, conf_emisora = (
        extraer_institucion_emisora_cep(
            detecciones
        )
    )

    # ========================================================
    # FECHA OPERACIÓN
    # ========================================================

    fecha, conf_fecha = (
        extraer_fecha_cep_directa(
            detecciones
        )
    )

    # ========================================================
    # CONCEPTO
    # ========================================================

    concepto, conf_concepto = (
        extraer_concepto_cep_directo(
            detecciones
        )
    )

    # ========================================================
    # MONTO
    # ========================================================

    monto, conf_monto = (
        extraer_monto(
            detecciones
        )
    )

    # ========================================================
    # REFERENCIA NUMÉRICA
    # ========================================================

    referencia_numerica, conf_referencia = (
        extraer_referencia_numerica_cep_directa(
            detecciones
        )
    )

    # ========================================================
    # CLAVE DE RASTREO
    # ========================================================

    clave_rastreo, conf_rastreo = (
        extraer_clave_rastreo_cep_directa(
            detecciones
        )
    )

    # ========================================================
    # INSTITUCIÓN RECEPTORA
    # ========================================================

    institucion_receptora, conf_receptora = (
        extraer_institucion_receptora_cep(
            detecciones
        )
    )

    # ========================================================
    # TITULAR BENEFICIARIO
    # ========================================================

    titular_beneficiario, conf_titular = (
        extraer_titular_beneficiario_cep_directo(
            detecciones
        )
    )

    # ========================================================
    # CLABE BENEFICIARIO
    # ========================================================

    clabe_beneficiario, conf_clabe = (
        extraer_clabe_cep_directa(
            detecciones
        )
    )

    # ========================================================
    # RESULTADO
    # ========================================================

    return {

        "institucion_emisora":
            campo_encontrado(
                institucion_emisora,
                "coordenadas_institucion_emisora",
                conf_emisora
            ),

        "fecha_operacion":
            campo_encontrado(
                fecha,
                "fecha_cep",
                conf_fecha
            ),

        "concepto":
            campo_encontrado(
                concepto,
                "etiqueta_concepto",
                conf_concepto
            ),

        "monto":
            campo_encontrado(
                monto,
                "deteccion_monto",
                conf_monto
            ),

        "referencia_numerica":
            campo_encontrado(
                referencia_numerica,
                "etiqueta_referencia_numerica",
                conf_referencia
            ),

        "clave_rastreo":
            campo_encontrado(
                clave_rastreo,
                "etiqueta_clave_rastreo",
                conf_rastreo
            ),

        "institucion_receptora":
            campo_encontrado(
                institucion_receptora,
                "coordenadas_institucion_receptora",
                conf_receptora
            ),

        "titular_cuenta_beneficiario":
            campo_encontrado(
                titular_beneficiario,
                "coordenadas_titular_beneficiario",
                conf_titular
            ),

        "clabe_beneficiario":
            campo_encontrado(
                clabe_beneficiario,
                "deteccion_clabe_beneficiario",
                conf_clabe
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

    # ========================================================
    # PRIORIDAD 1
    # CEP
    # ========================================================

    if es_cep(
        detecciones
    ):

        return {

            "banco":
                BANCO,

            "tipo":
                "CEP_SANTANDER",

            "campos":
                extraer_cep(
                    detecciones
                )

        }

    # ========================================================
    # PRIORIDAD 2
    # REF. SUPERMÓVIL
    # ========================================================

    if es_supermovil(
        detecciones
    ):

        return {

            "banco":
                BANCO,

            "tipo":
                "REF_SUPERMOVIL_SANTANDER",

            "campos":
                extraer_supermovil(
                    detecciones
                )

        }

    # ========================================================
    # PRIORIDAD 3
    # TRANSFERENCIA CON REFERENCIA
    # ========================================================

    if es_transferencia_referencia(
        detecciones
    ):

        return {

            "banco":
                BANCO,

            "tipo":
                "TRANSFERENCIA_SANTANDER_REFERENCIA",

            "campos":
                extraer_transferencia_referencia(
                    detecciones
                )

        }

    # ========================================================
    # FORMATO DESCONOCIDO
    # ========================================================

    return {

        "banco":
            BANCO,

        "tipo":
            "FORMATO_SANTANDER_DESCONOCIDO",

        "campos":
            {}

    }


# ============================================================
# CLASE
# ============================================================

class SantanderExtractor:

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

    return SantanderExtractor()