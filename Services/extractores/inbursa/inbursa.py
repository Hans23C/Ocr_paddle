import re
import unicodedata


# ============================================================
# UTILIDADES
# ============================================================

def normalizar(texto):
    texto = str(texto or "").strip().lower()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    return "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )


def texto(d):
    return str(
        d.get("texto", "")
    ).strip()


def confianza(d):
    try:
        return float(
            d.get("confianza", 0)
        )
    except Exception:
        return 0.0


def crear_campo(
    valor,
    deteccion=None,
    metodo="OCR_DIRECTO"
):

    if not valor:
        return {
            "valor": None,
            "metodo": "NO ENCONTRADO",
            "confianza": 0.0
        }

    resultado = {
        "valor": str(valor).strip(),
        "metodo": metodo,
        "confianza": confianza(
            deteccion
        )
    }

    if deteccion:
        resultado["bbox"] = {
            "x": deteccion.get(
                "x_rel", 0
            ),
            "y": deteccion.get(
                "y_rel", 0
            ),
            "w": deteccion.get(
                "ancho_rel", 0
            ),
            "h": deteccion.get(
                "alto_rel", 0
            )
        }

    return resultado


# ============================================================
# BUSQUEDAS BASICAS
# ============================================================

def buscar_texto(
    detecciones,
    buscado
):

    objetivo = normalizar(
        buscado
    )

    for d in detecciones:

        if normalizar(
            texto(d)
        ) == objetivo:

            return d

    return None


def buscar_contiene(
    detecciones,
    buscado
):

    objetivo = normalizar(
        buscado
    )

    for d in detecciones:

        if objetivo in normalizar(
            texto(d)
        ):

            return d

    return None


# ============================================================
# VALOR A LA DERECHA
# ============================================================

def valor_derecha(
    detecciones,
    etiqueta,
    max_dy=0.04
):

    if not etiqueta:
        return None

    x0 = float(
        etiqueta.get(
            "x_rel", 0
        )
    )

    y0 = float(
        etiqueta.get(
            "y_rel", 0
        )
    )

    candidatos = []

    for d in detecciones:

        if d is etiqueta:
            continue

        x = float(
            d.get(
                "x_rel", 0
            )
        )

        y = float(
            d.get(
                "y_rel", 0
            )
        )

        if x <= x0:
            continue

        dy = abs(
            y - y0
        )

        if dy > max_dy:
            continue

        candidatos.append(
            (
                dy,
                x - x0,
                d
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
# VALOR DEBAJO
# ============================================================

def valor_debajo(
    detecciones,
    etiqueta,
    max_dy=0.08
):

    if not etiqueta:
        return None

    x0 = float(
        etiqueta.get(
            "x_rel", 0
        )
    )

    y0 = float(
        etiqueta.get(
            "y_rel", 0
        )
    )

    candidatos = []

    for d in detecciones:

        if d is etiqueta:
            continue

        x = float(
            d.get(
                "x_rel", 0
            )
        )

        y = float(
            d.get(
                "y_rel", 0
            )
        )

        dy = y - y0

        if dy <= 0:
            continue

        if dy > max_dy:
            continue

        dx = abs(
            x - x0
        )

        candidatos.append(
            (
                dy,
                dx,
                d
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
# VALOR ARRIBA
# ============================================================

def valor_arriba(
    detecciones,
    etiqueta,
    max_dy=0.08
):

    if not etiqueta:
        return None

    x0 = float(
        etiqueta.get(
            "x_rel", 0
        )
    )

    y0 = float(
        etiqueta.get(
            "y_rel", 0
        )
    )

    candidatos = []

    for d in detecciones:

        if d is etiqueta:
            continue

        x = float(
            d.get(
                "x_rel", 0
            )
        )

        y = float(
            d.get(
                "y_rel", 0
            )
        )

        dy = y0 - y

        if dy <= 0:
            continue

        if dy > max_dy:
            continue

        dx = abs(
            x - x0
        )

        candidatos.append(
            (
                dy,
                dx,
                d
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
# VALOR EN LA MISMA LINEA
#
# Ejemplo:
#
# Folio: 4004798504
# ============================================================

def valor_misma_linea(
    detecciones,
    etiquetas
):

    for d in detecciones:

        original = texto(d)
        normal = normalizar(
            original
        )

        for etiqueta in etiquetas:

            etiqueta_normal = normalizar(
                etiqueta
            )

            if normal.startswith(
                etiqueta_normal
            ):

                posicion = len(
                    etiqueta
                )

                valor = original[
                    posicion:
                ].strip()

                valor = valor.lstrip(
                    ":"
                ).strip()

                if valor:
                    return (
                        valor,
                        d
                    )

    return (
        "",
        None
    )


# ============================================================
# BANCO
# ============================================================

def extraer_banco(
    detecciones
):

    d = buscar_texto(
        detecciones,
        "INBURSA"
    )

    return crear_campo(
        "INBURSA" if d else "",
        d
    )


# ============================================================
# FECHA
# ============================================================

def extraer_fecha(
    detecciones
):

    patrones = [

        r"\d{1,2}\s+[A-Za-z]+\s+\d{4},?\s+\d{1,2}:\d{2}:\d{2}\s*h?",

        r"\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}",

        r"\d{1,2}\s+[A-Za-z]+\s+\d{4}"

    ]

    for d in detecciones:

        valor = texto(d)

        for patron in patrones:

            if re.fullmatch(
                patron,
                valor,
                re.IGNORECASE
            ):

                return crear_campo(
                    valor,
                    d
                )

    return crear_campo(
        "",
        None
    )


# ============================================================
# MONTO
# ============================================================

def extraer_monto(
    detecciones
):

    patron = re.compile(
        r"^\$\s*[\d,]+\.\d{2}$"
    )

    for d in detecciones:

        valor = texto(d)

        if patron.fullmatch(
            valor
        ):

            return crear_campo(
                valor,
                d
            )

    return crear_campo(
        "",
        None
    )


# ============================================================
# FOLIO
# ============================================================

def extraer_folio(
    detecciones
):

    valor, d = valor_misma_linea(
        detecciones,
        ["Folio"]
    )

    if valor and re.fullmatch(
        r"\d{7,12}",
        valor
    ):

        return crear_campo(
            valor,
            d
        )

    return crear_campo(
        "",
        None
    )


# ============================================================
# CLAVE DE RASTREO
# ============================================================

def extraer_clave_rastreo(
    detecciones
):

    patron = re.compile(
        r"^036[A-Z0-9]{15,}$",
        re.IGNORECASE
    )

    for d in detecciones:

        valor = texto(d).replace(
            " ",
            ""
        )

        if patron.fullmatch(
            valor
        ):

            return crear_campo(
                texto(d),
                d
            )

    return crear_campo(
        "",
        None
    )


# ============================================================
# CLABE
# ============================================================

def extraer_clabe(
    detecciones
):

    valor, d = valor_misma_linea(
        detecciones,
        ["CLABE"]
    )

    if valor:

        limpio = valor.replace(
            " ",
            ""
        ).replace(
            "O",
            "0"
        ).replace(
            "o",
            "0"
        )

        if re.fullmatch(
            r"\d{18}",
            limpio
        ):

            return crear_campo(
                limpio,
                d
            )

    return crear_campo(
        "",
        None
    )


# ============================================================
# CONCEPTO - TRASPASO SPEI
# ============================================================

def extraer_concepto_traspaso(
    detecciones
):

    etiqueta = buscar_texto(
        detecciones,
        "Concepto"
    )

    if etiqueta:

        candidato = valor_arriba(
            detecciones,
            etiqueta,
            max_dy=0.08
        )

        if candidato:

            valor = texto(
                candidato
            )

            if (
                valor
                and
                not valor.isdigit()
                and
                normalizar(
                    valor
                ) != "informacion de la operacion"
            ):

                return crear_campo(
                    valor,
                    candidato,
                    "BBOX_ARRIBA"
                )

    return crear_campo(
        "",
        None
    )


# ============================================================
# REFERENCIA NUMÉRICA
# ============================================================

def extraer_referencia(
    detecciones
):

    etiqueta = None

    for d in detecciones:

        t = normalizar(
            texto(d)
        )

        if "referencia numerica" in t:

            etiqueta = d
            break

    if not etiqueta:

        return crear_campo(
            "",
            None
        )

    # --------------------------------------------------------
    # 1. ARRIBA
    #
    # image_665:
    # 621
    # Referencia númerica
    #
    # image_670:
    # 20260626
    # Referencia numérica
    # --------------------------------------------------------

    candidato = valor_arriba(
        detecciones,
        etiqueta,
        max_dy=0.08
    )

    if candidato:

        valor = texto(
            candidato
        )

        if re.fullmatch(
            r"\d+",
            valor
        ):

            return crear_campo(
                valor,
                candidato,
                "BBOX_ARRIBA"
            )

    # --------------------------------------------------------
    # 2. MISMA LINEA
    # --------------------------------------------------------

    valor, d = valor_misma_linea(
        detecciones,
        [
            "Referencia numérica:",
            "Referencia numerica:",
            "Referencia numérica",
            "Referencia numerica"
        ]
    )

    if valor:

        if re.fullmatch(
            r"\d+",
            valor
        ):

            return crear_campo(
                valor,
                d,
                "OCR_DIRECTO"
            )

    # --------------------------------------------------------
    # 3. DEBAJO
    # --------------------------------------------------------

    candidato = valor_debajo(
        detecciones,
        etiqueta,
        max_dy=0.08
    )

    if candidato:

        valor = texto(
            candidato
        )

        if re.fullmatch(
            r"\d+",
            valor
        ):

            return crear_campo(
                valor,
                candidato,
                "BBOX_DEBAJO"
            )

    # --------------------------------------------------------
    # 4. DERECHA
    # --------------------------------------------------------

    candidato = valor_derecha(
        detecciones,
        etiqueta
    )

    if candidato:

        valor = texto(
            candidato
        )

        if re.fullmatch(
            r"\d+",
            valor
        ):

            return crear_campo(
                valor,
                candidato,
                "BBOX_DERECHA"
            )

    return crear_campo(
        "",
        None
    )


# ============================================================
# DESTINATARIO - TRASPASO SPEI
# ============================================================

def extraer_destinatario(
    detecciones
):

    etiqueta = buscar_texto(
        detecciones,
        "Destinatario"
    )

    if not etiqueta:

        return crear_campo(
            "",
            None
        )

    candidato = valor_debajo(
        detecciones,
        etiqueta,
        max_dy=0.08
    )

    if candidato:

        valor = texto(
            candidato
        )

        if (
            valor
            and
            not normalizar(
                valor
            ).startswith("banco")
            and
            "clabe" not in normalizar(
                valor
            )
        ):

            return crear_campo(
                valor,
                candidato,
                "BBOX_DEBAJO"
            )

    return crear_campo(
        "",
        None
    )


# ============================================================
# BANCO DESTINATARIO - TRASPASO SPEI
# ============================================================

def extraer_banco_destinatario(
    detecciones
):

    for d in detecciones:

        valor = texto(d)

        normal = normalizar(
            valor
        )

        if normal.startswith(
            "banco "
        ):

            banco = re.sub(
                r"^Banco\s*",
                "",
                valor,
                flags=re.IGNORECASE
            ).strip()

            if banco:

                return crear_campo(
                    banco,
                    d
                )

    return crear_campo(
        "",
        None
    )


# ============================================================
# NÚMERO DE OPERACIÓN
# ============================================================

def extraer_numero_operacion(
    detecciones
):

    etiqueta = buscar_contiene(
        detecciones,
        "Número de operación"
    )

    if not etiqueta:

        etiqueta = buscar_contiene(
            detecciones,
            "Numero de operacion"
        )

    if not etiqueta:

        return crear_campo(
            "",
            None
        )

    # image_670:
    #
    # 4026542139
    # Número de operación

    candidato = valor_arriba(
        detecciones,
        etiqueta,
        max_dy=0.08
    )

    if candidato:

        valor = texto(
            candidato
        )

        if re.fullmatch(
            r"\d{7,12}",
            valor
        ):

            return crear_campo(
                valor,
                candidato,
                "BBOX_ARRIBA"
            )

    # image_683:
    #
    # Número de operación: 3991182362

    valor, d = valor_misma_linea(
        detecciones,
        [
            "Número de operación:",
            "Numero de operacion:"
        ]
    )

    if valor and re.fullmatch(
        r"\d{7,12}",
        valor
    ):

        return crear_campo(
            valor,
            d
        )

    candidato = valor_derecha(
        detecciones,
        etiqueta
    )

    if candidato:

        valor = texto(
            candidato
        )

        if re.fullmatch(
            r"\d{7,12}",
            valor
        ):

            return crear_campo(
                valor,
                candidato,
                "BBOX_DERECHA"
            )

    return crear_campo(
        "",
        None
    )


# ============================================================
# CUENTA BENEFICIARIO
# ============================================================

def extraer_cuenta_beneficiario(
    detecciones
):

    etiqueta = buscar_contiene(
        detecciones,
        "Cuenta beneficiario"
    )

    if not etiqueta:

        etiqueta = buscar_contiene(
            detecciones,
            "Cuenta del beneficiario"
        )

    if not etiqueta:

        return crear_campo(
            "",
            None
        )

    # image_670:
    #
    # ****1311
    # Cuenta beneficiario

    candidato = valor_arriba(
        detecciones,
        etiqueta,
        max_dy=0.08
    )

    if candidato:

        valor = texto(
            candidato
        )

        if "****" in valor:

            return crear_campo(
                valor,
                candidato,
                "BBOX_ARRIBA"
            )

    # image_683:
    #
    # Cuenta del beneficiario: ****9131

    valor, d = valor_misma_linea(
        detecciones,
        [
            "Cuenta del beneficiario:",
            "Cuenta del beneficiario"
        ]
    )

    if valor:

        return crear_campo(
            valor,
            d
        )

    candidato = valor_derecha(
        detecciones,
        etiqueta
    )

    if candidato:

        valor = texto(
            candidato
        )

        if "****" in valor:

            return crear_campo(
                valor,
                candidato,
                "BBOX_DERECHA"
            )

    return crear_campo(
        "",
        None
    )


# ============================================================
# NOMBRE BENEFICIARIO
# ============================================================

def extraer_nombre_beneficiario(
    detecciones
):

    etiqueta = buscar_contiene(
        detecciones,
        "Nombre del beneficiario"
    )

    if not etiqueta:

        return crear_campo(
            "",
            None
        )

    # --------------------------------------------------------
    # 1. MISMA LINEA
    #
    # image_683:
    #
    # Nombre del beneficiario*: IPTVTEL...
    # --------------------------------------------------------

    valor, d = valor_misma_linea(
        detecciones,
        [
            "Nombre del beneficiario*:",
            "Nombre del beneficiario*",
            "Nombre del beneficiario:"
        ]
    )

    if valor:

        return crear_campo(
            valor,
            d,
            "OCR_DIRECTO"
        )

    # --------------------------------------------------------
    # 2. DERECHA
    # --------------------------------------------------------

    candidato = valor_derecha(
        detecciones,
        etiqueta,
        max_dy=0.04
    )

    if candidato:

        valor = texto(
            candidato
        )

        if (
            valor
            and
            "cuenta" not in normalizar(
                valor
            )
            and
            "nsferencia" not in normalizar(
                valor
            )
        ):

            return crear_campo(
                valor,
                candidato,
                "BBOX_DERECHA"
            )

    # --------------------------------------------------------
    # 3. ARRIBA
    #
    # image_670:
    #
    # IPTVTEL COMUNICACIONES
    # Nombre del beneficiario
    # --------------------------------------------------------

    candidato = valor_arriba(
        detecciones,
        etiqueta,
        max_dy=0.08
    )

    if candidato:

        valor = texto(
            candidato
        )

        if (
            valor
            and
            "*" not in valor
            and
            "cuenta" not in normalizar(
                valor
            )
            and
            "nsferencia" not in normalizar(
                valor
            )
        ):

            return crear_campo(
                valor,
                candidato,
                "BBOX_ARRIBA"
            )

    # --------------------------------------------------------
    # 4. DEBAJO
    # --------------------------------------------------------

    candidato = valor_debajo(
        detecciones,
        etiqueta,
        max_dy=0.08
    )

    if candidato:

        valor = texto(
            candidato
        )

        if valor:

            return crear_campo(
                valor,
                candidato,
                "BBOX_DEBAJO"
            )

    return crear_campo(
        "",
        None
    )


# ============================================================
# TIPO DE NÚMERO DE CUENTA
# ============================================================

def extraer_tipo_cuenta(
    detecciones
):

    etiqueta = buscar_contiene(
        detecciones,
        "Tipo de número de cuenta"
    )

    if not etiqueta:

        etiqueta = buscar_contiene(
            detecciones,
            "Tipo de numero de cuenta"
        )

    if not etiqueta:

        return crear_campo(
            "",
            None
        )

    # --------------------------------------------------------
    # 1. MISMA LINEA
    #
    # image_683:
    #
    # Tipo de número de cuenta: CUENTA CLABE
    # --------------------------------------------------------

    valor, d = valor_misma_linea(
        detecciones,
        [
            "Tipo de número de cuenta:",
            "Tipo de numero de cuenta:",
            "Tipo de número de cuenta",
            "Tipo de numero de cuenta"
        ]
    )

    if valor:

        if "cuenta" in normalizar(
            valor
        ):

            return crear_campo(
                valor,
                d,
                "OCR_DIRECTO"
            )

    # --------------------------------------------------------
    # 2. DERECHA
    # --------------------------------------------------------

    candidato = valor_derecha(
        detecciones,
        etiqueta,
        max_dy=0.04
    )

    if candidato:

        valor = texto(
            candidato
        )

        if "cuenta" in normalizar(
            valor
        ):

            return crear_campo(
                valor,
                candidato,
                "BBOX_DERECHA"
            )

    # --------------------------------------------------------
    # 3. ARRIBA
    #
    # image_670:
    #
    # CUENTA CLABE
    # Tipo de número de cuenta
    # --------------------------------------------------------

    candidato = valor_arriba(
        detecciones,
        etiqueta,
        max_dy=0.08
    )

    if candidato:

        valor = texto(
            candidato
        )

        if "cuenta" in normalizar(
            valor
        ):

            return crear_campo(
                valor,
                candidato,
                "BBOX_ARRIBA"
            )

    # --------------------------------------------------------
    # 4. DEBAJO
    # --------------------------------------------------------

    candidato = valor_debajo(
        detecciones,
        etiqueta,
        max_dy=0.08
    )

    if candidato:

        valor = texto(
            candidato
        )

        if "cuenta" in normalizar(
            valor
        ):

            return crear_campo(
                valor,
                candidato,
                "BBOX_DEBAJO"
            )

    return crear_campo(
        "",
        None
    )


# ============================================================
# BANCO BENEFICIARIO
# ============================================================

def extraer_banco_beneficiario(
    detecciones
):

    etiqueta = buscar_contiene(
        detecciones,
        "Banco beneficiario"
    )

    if not etiqueta:

        etiqueta = buscar_contiene(
            detecciones,
            "Banco del beneficiario"
        )

    if not etiqueta:

        return crear_campo(
            "",
            None
        )

    # image_670:
    #
    # HSBC
    # Banco beneficiario

    candidato = valor_arriba(
        detecciones,
        etiqueta
    )

    if candidato:

        valor = texto(
            candidato
        )

        if normalizar(
            valor
        ) == "hsbc":

            return crear_campo(
                valor,
                candidato,
                "BBOX_ARRIBA"
            )

    # image_683:
    #
    # Banco del beneficiario: HSBC

    valor, d = valor_misma_linea(
        detecciones,
        [
            "Banco del beneficiario:",
            "Banco del beneficiario"
        ]
    )

    if valor:

        return crear_campo(
            valor,
            d
        )

    candidato = valor_derecha(
        detecciones,
        etiqueta
    )

    if candidato:

        valor = texto(
            candidato
        )

        if normalizar(
            valor
        ) == "hsbc":

            return crear_campo(
                valor,
                candidato,
                "BBOX_DERECHA"
            )

    return crear_campo(
        "",
        None
    )


# ============================================================
# CUENTA BANCO EMISOR
# ============================================================

def extraer_cuenta_banco_emisor(
    detecciones
):

    etiqueta = buscar_contiene(
        detecciones,
        "Cuenta del banco emisor"
    )

    if etiqueta:

        candidato = valor_arriba(
            detecciones,
            etiqueta
        )

        if candidato:

            valor = texto(
                candidato
            )

            limpio = valor.replace(
                " ",
                ""
            )

            if re.fullmatch(
                r"\d{10,30}",
                limpio
            ):

                return crear_campo(
                    valor,
                    candidato,
                    "BBOX_ARRIBA"
                )

        valor, d = valor_misma_linea(
            detecciones,
            [
                "Cuenta del banco emisor"
            ]
        )

        if valor:

            return crear_campo(
                valor,
                d
            )

    # --------------------------------------------------------
    # image_683
    #
    # Con cargo a tu cuenta
    # ****8289
    # --------------------------------------------------------

    etiqueta_cargo = buscar_contiene(
        detecciones,
        "Con cargo a tu cuenta"
    )

    if etiqueta_cargo:

        candidato = valor_debajo(
            detecciones,
            etiqueta_cargo,
            max_dy=0.08
        )

        if candidato:

            valor = texto(
                candidato
            )

            if (
                "****" in valor
                or
                re.fullmatch(
                    r"\d{4,30}",
                    valor
                )
            ):

                return crear_campo(
                    valor,
                    candidato,
                    "BBOX_DEBAJO"
                )

    return crear_campo(
        "",
        None
    )


# ============================================================
# CONCEPTO - TRANSFERENCIA
# ============================================================

def extraer_concepto_transferencia(
    detecciones
):

    # --------------------------------------------------------
    # image_670:
    #
    # Transferencia electronica
    # Concepto
    # --------------------------------------------------------

    etiqueta = buscar_texto(
        detecciones,
        "Concepto"
    )

    if etiqueta:

        candidato = valor_arriba(
            detecciones,
            etiqueta,
            max_dy=0.08
        )

        if candidato:

            valor = texto(
                candidato
            )

            if (
                valor
                and
                not valor.isdigit()
            ):

                return crear_campo(
                    valor,
                    candidato,
                    "BBOX_ARRIBA"
                )

    # --------------------------------------------------------
    # image_683:
    #
    # Referencia de la operación:
    # Transferencia electronica
    # --------------------------------------------------------

    etiqueta = buscar_contiene(
        detecciones,
        "Referencia de la operación"
    )

    if etiqueta:

        valor, d = valor_misma_linea(
            detecciones,
            [
                "Referencia de la operación:",
                "Referencia de la operación"
            ]
        )

        if valor:

            return crear_campo(
                valor,
                d,
                "OCR_DIRECTO"
            )

        candidato = valor_derecha(
            detecciones,
            etiqueta
        )

        if candidato:

            valor = texto(
                candidato
            )

            if valor:

                return crear_campo(
                    valor,
                    candidato,
                    "BBOX_DERECHA"
                )

    return crear_campo(
        "",
        None
    )


# ============================================================
# TRASPASO SPEI
# ============================================================

def extraer_traspaso_spei(
    detecciones
):

    campos = {}

    campos["banco"] = (
        extraer_banco(
            detecciones
        )
    )

    campos["fecha"] = (
        extraer_fecha(
            detecciones
        )
    )

    campos["monto"] = (
        extraer_monto(
            detecciones
        )
    )

    campos["folio"] = (
        extraer_folio(
            detecciones
        )
    )

    campos["destinatario"] = (
        extraer_destinatario(
            detecciones
        )
    )

    campos["banco_destinatario"] = (
        extraer_banco_destinatario(
            detecciones
        )
    )

    campos["clabe"] = (
        extraer_clabe(
            detecciones
        )
    )

    campos["clave_rastreo"] = (
        extraer_clave_rastreo(
            detecciones
        )
    )

    campos["concepto"] = (
        extraer_concepto_traspaso(
            detecciones
        )
    )

    campos["referencia_numerica"] = (
        extraer_referencia(
            detecciones
        )
    )

    return campos


# ============================================================
# TRANSFERENCIA
# ============================================================

def extraer_transferencia(
    detecciones
):

    campos = {}

    campos["banco"] = (
        extraer_banco(
            detecciones
        )
    )

    campos["fecha"] = (
        extraer_fecha(
            detecciones
        )
    )

    campos["numero_operacion"] = (
        extraer_numero_operacion(
            detecciones
        )
    )

    campos["monto"] = (
        extraer_monto(
            detecciones
        )
    )

    campos["cuenta_beneficiario"] = (
        extraer_cuenta_beneficiario(
            detecciones
        )
    )

    campos["nombre_beneficiario"] = (
        extraer_nombre_beneficiario(
            detecciones
        )
    )

    campos["tipo_numero_cuenta"] = (
        extraer_tipo_cuenta(
            detecciones
        )
    )

    campos["banco_beneficiario"] = (
        extraer_banco_beneficiario(
            detecciones
        )
    )

    campos["cuenta_banco_emisor"] = (
        extraer_cuenta_banco_emisor(
            detecciones
        )
    )

    campos["clave_rastreo"] = (
        extraer_clave_rastreo(
            detecciones
        )
    )

    campos["concepto"] = (
        extraer_concepto_transferencia(
            detecciones
        )
    )

    campos["referencia_numerica"] = (
        extraer_referencia(
            detecciones
        )
    )

    return campos


# ============================================================
# DETECTAR TIPO
# ============================================================

def detectar_tipo(
    detecciones
):

    texto_total = " ".join(
        normalizar(
            texto(d)
        )
        for d in detecciones
    )

    if "traspaso spei" in texto_total:

        return "TRASPASO_SPEI"

    if (
        "numero de operacion"
        in texto_total
        or
        "nombre del beneficiario"
        in texto_total
    ):

        return "TRANSFERENCIA"

    return "DESCONOCIDO"


# ============================================================
# EXTRACTOR PRINCIPAL
# ============================================================

def extraer(
    datos_json
):

    detecciones = datos_json.get(
        "detecciones",
        []
    )

    tipo = detectar_tipo(
        detecciones
    )

    if tipo == "TRASPASO_SPEI":

        campos = (
            extraer_traspaso_spei(
                detecciones
            )
        )

    elif tipo == "TRANSFERENCIA":

        campos = (
            extraer_transferencia(
                detecciones
            )
        )

    else:

        campos = {}

    return {
        "banco": "INBURSA",
        "tipo": tipo,
        "campos": campos
    }


# ============================================================
# COMPATIBILIDAD
# ============================================================

def extraer_inbursa(
    datos_json
):

    return extraer(
        datos_json
    )