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

        # Caso: "De" o ruido OCR como "è De"
        if linea_norm == "de" or re.fullmatch(r"[^a-z0-9]*[eè]?\s*de", linea_norm):

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

        # Caso OCR: "De Nombre..." (excluyendo continuación de razón social como "De C", "De CV", "De RL")
        if linea_norm.startswith("de ") and not re.match(r"^de\s+(c|cv|rl|r\.l\.|c\.v\.)\b", linea_norm):

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

    # Caso formato "Origen y destino" (Transferencia enviada)
    for indice, linea in enumerate(lineas):
        if "origen y destino" in normalizar_busqueda(linea):
            idx_mp = None
            for j in range(indice + 1, min(indice + 5, len(lineas))):
                cand = normalizar_texto(lineas[j]).rstrip("> ").strip()
                if "mercado pago" in normalizar_busqueda(cand) and not titular:
                    titular = cand
                    idx_mp = j
                if "|" in cand and not cuenta:
                    partes = [p.strip() for p in cand.split("|") if p.strip()]
                    if partes:
                        cuenta = partes[-1]
            if not cuenta and idx_mp is not None:
                for k in range(idx_mp + 1, min(idx_mp + 3, len(lineas))):
                    t_norm = normalizar_busqueda(lineas[k])
                    if "spei" in t_norm or "comprobante" in t_norm:
                        break
                    if (
                        "clabe" in t_norm
                        or "numero de tarjeta" in t_norm
                        or "número de tarjeta" in t_norm
                    ):
                        cuenta = extraer_dato_bancario(lineas, k, limite=2)
                        if cuenta:
                            break
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

            if match and normalizar_texto(match.group(1)):
                candidato = normalizar_texto(
                    match.group(1)
                )
            else:
                antes = normalizar_texto(
                    re.sub(r"\bpara\b.*$", "", linea, flags=re.IGNORECASE)
                )
                if antes:
                    if indice + 1 < len(lineas):
                        sig = normalizar_texto(lineas[indice + 1])
                        if sig and normalizar_busqueda(sig) not in ("hsbc",) and not normalizar_busqueda(sig).startswith("clabe"):
                            antes = f"{antes} {sig}"
                    candidato = antes

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

            if texto_norm == "hsbc" or texto_norm.endswith(" hsbc"):
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

    # Caso formato "Transferencia enviada / Origen y destino"
    for indice, linea in enumerate(lineas):
        if "origen y destino" in normalizar_busqueda(linea):
            idx_monto = None
            idx_enviada = None
            for k, l in enumerate(lineas):
                if idx_monto is None and l.strip().startswith("$"):
                    idx_monto = k
                if "transferencia enviada" in normalizar_busqueda(l):
                    idx_enviada = k
                    break
            if idx_enviada is not None:
                if idx_monto is not None and idx_enviada > idx_monto + 1:
                    partes_benef = [normalizar_texto(lineas[k]) for k in range(idx_monto + 1, idx_enviada) if normalizar_texto(lineas[k])]
                    if partes_benef:
                        titular = " ".join(partes_benef)
                for j in range(indice + 1, min(indice + 10, len(lineas))):
                    t_norm = normalizar_busqueda(lineas[j])
                    if "hsbc" in t_norm:
                        banco = "HSBC"
                    if "clabe" in t_norm or "tarjeta" in t_norm:
                        cuenta = extraer_dato_bancario(lineas, j, limite=3)
                        if cuenta:
                            break
                return titular, banco, cuenta

            # Caso "Comprobante de transferencia" con "Origen y destino" (sin "De"/"Para" ni "Transferencia enviada")
            inicio_benef = indice + 1
            for j in range(indice + 1, min(indice + 6, len(lineas))):
                t_norm = normalizar_busqueda(lineas[j])
                if "mercado pago" in t_norm:
                    inicio_benef = j + 1
                    if j + 1 < len(lineas):
                        sig_norm = normalizar_busqueda(lineas[j + 1])
                        if (
                            "clabe" in sig_norm
                            or "tarjeta" in sig_norm
                            or "cuenta" in sig_norm
                            or "saldo" in sig_norm
                            or "|" in sig_norm
                        ):
                            inicio_benef = j + 2
                    break

            previos = []
            for j in range(inicio_benef, min(inicio_benef + 6, len(lineas))):
                texto = normalizar_texto(lineas[j])
                t_norm = normalizar_busqueda(texto)
                if not texto:
                    continue
                if (
                    t_norm.startswith("comprobante")
                    or "protegemos tu dinero" in t_norm
                    or "seguridad de mercado pago" in t_norm
                    or "clave de rastreo" in t_norm
                    or "de operacion" in t_norm
                    or "referencia" in t_norm
                ):
                    break
                if (
                    "clabe" in t_norm
                    or "numero de tarjeta" in t_norm
                    or "número de tarjeta" in t_norm
                    or "numero de cuenta" in t_norm
                    or "número de cuenta" in t_norm
                ):
                    cuenta = extraer_dato_bancario(lineas, j, limite=2)
                    break
                previos.append(texto)

            if len(previos) >= 2:
                banco = previos[-1]
                titular = " ".join(previos[:-1])
            elif len(previos) == 1:
                p_norm = normalizar_busqueda(previos[0])
                bancos_conocidos = (
                    "hsbc", "bbva", "banamex", "citibanamex", "banorte", "santander",
                    "scotiabank", "azteca", "bancoppel", "inbursa", "banbajio", "nu",
                    "klar", "mercado pago", "stp", "spin", "albo", "stori", "plata",
                    "hey", "fondeadora", "mifel", "compartamos", "revolut", "claro pay",
                    "bienestar", "actinver", "afirme", "banregio", "multiva",
                )
                if any(b in p_norm for b in bancos_conocidos):
                    banco = previos[0]
                else:
                    titular = previos[0]

            return titular, banco, cuenta

    return titular, banco, cuenta


# ============================================================
# REFERENCIA
# ============================================================

def extraer_numero_referencia(lineas):
    valor_prio = buscar_etiqueta(lineas, ["Número de referencia", "Numero de referencia", "Referencia adicional"])
    if valor_prio:
        m_p = re.search(r"\b\d+\b", valor_prio)
        if m_p:
            return m_p.group(0)

    valor = buscar_etiqueta(
        lineas,
        [
            "Número de referencia",
            "Numero de referencia",
            "Referencia adicional",
            "N.° de operación",
            "N.º de operación",
            "N. de operación",
        ]
    )

    if valor:
        match = re.search(
            r"\b\d+\b",
            valor
        )
        if match:
            return match.group(0)

    valor_comp = buscar_etiqueta(
        lineas,
        ["Comprobante"]
    )
    if valor_comp:
        m_comp = re.search(r"#?\s*([A-Za-z0-9]{6,})", valor_comp)
        if m_comp:
            return m_comp.group(1)

    return None


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

    resultado = {
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
    }

    if concepto:
        resultado["concepto"] = campo_encontrado(
            concepto
        )
    clave_r = buscar_etiqueta(lineas, ["Clave de rastreo", "Clave de Rastreo"])
    if clave_r:
        resultado["clave_rastreo"] = campo_encontrado(clave_r)
    num_op = buscar_etiqueta(lineas, ["N.° de operación", "N.º de operación", "N. de operación"])
    if num_op:
        resultado["numero_operacion"] = campo_encontrado(num_op)
    if False:
        resultado["concepto"] = campo_encontrado(
            concepto
        )

    return resultado


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