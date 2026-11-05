import re
import unicodedata


# ============================================================
# CONFIGURACIÓN
# ============================================================

BANCO = "NU_MEXICO"

TIPO_COMPROBANTE = "TRANSFERENCIA_NU_MEXICO"


# ============================================================
# UTILIDADES GENERALES
# ============================================================

def normalizar_texto(texto):

    if texto is None:
        return ""

    texto = str(texto)

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        c
        for c in texto
        if not unicodedata.combining(c)
    )

    return texto.lower().strip()


def limpiar_valor(valor):

    if valor is None:
        return None

    valor = str(valor).strip()

    if not valor:
        return None

    return valor


def obtener_confianza(deteccion):

    try:

        return float(
            deteccion.get(
                "confianza",
                0.0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return 0.0


def resultado_campo(
    valor=None,
    metodo="no_encontrado",
    confianza=0.0
):

    if valor is None:

        return {
            "valor": None,
            "metodo": "no_encontrado",
            "confianza": 0.0
        }

    valor = str(valor).strip()

    if not valor:

        return {
            "valor": None,
            "metodo": "no_encontrado",
            "confianza": 0.0
        }

    return {
        "valor": valor,
        "metodo": metodo,
        "confianza": float(confianza)
    }


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

    return detecciones


def obtener_lineas(datos):

    lineas = datos.get(
        "lineas",
        []
    )

    if not isinstance(
        lineas,
        list
    ):

        return []

    return [
        str(linea).strip()
        for linea in lineas
        if str(linea).strip()
    ]


# ============================================================
# BANCO
# ============================================================

def extraer_banco(datos):

    banco = datos.get(
        "banco"
    )

    if banco:

        return resultado_campo(
            "Nu México",
            "metadato",
            1.0
        )

    texto = datos.get(
        "texto_completo",
        ""
    )

    normalizado = normalizar_texto(
        texto
    )

    if "nu mexico" in normalizado:

        return resultado_campo(
            "Nu México",
            "texto",
            0.95
        )

    return resultado_campo()


# ============================================================
# FECHA
# ============================================================

def extraer_fecha(datos):

    patron_fecha = re.compile(
        r"\b"
        r"(\d{1,2})\s*"
        r"(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)"
        r"\s+"
        r"(\d{4})"
        r"\b",
        re.IGNORECASE
    )

    patron_hora = re.compile(
        r"\b"
        r"(\d{1,2}:\d{2}:\d{2})"
        r"\s*"
        r"(AM|PM)"
        r"\b",
        re.IGNORECASE
    )

    detecciones = obtener_detecciones(
        datos
    )

    if detecciones:

        ordenadas = sorted(
            detecciones,
            key=lambda d: (
                float(
                    d.get(
                        "y",
                        0
                    )
                ),
                float(
                    d.get(
                        "x",
                        0
                    )
                )
            )
        )

        for i, deteccion_fecha in enumerate(
            ordenadas
        ):

            texto_fecha = limpiar_valor(
                deteccion_fecha.get(
                    "texto"
                )
            )

            if not texto_fecha:
                continue

            coincidencia_fecha = (
                patron_fecha.search(
                    texto_fecha
                )
            )

            if not coincidencia_fecha:
                continue

            dia = coincidencia_fecha.group(
                1
            )

            mes = coincidencia_fecha.group(
                2
            ).upper()

            anio = coincidencia_fecha.group(
                3
            )

            coincidencia_hora = (
                patron_hora.search(
                    texto_fecha
                )
            )

            deteccion_hora = None

            if coincidencia_hora:

                hora = coincidencia_hora.group(
                    1
                )

                am_pm = coincidencia_hora.group(
                    2
                ).upper()

            else:

                hora = None
                am_pm = None

                y_fecha = float(
                    deteccion_fecha.get(
                        "y",
                        0
                    )
                )

                for siguiente in ordenadas[
                    i + 1:
                ]:

                    texto_siguiente = limpiar_valor(
                        siguiente.get(
                            "texto"
                        )
                    )

                    if not texto_siguiente:
                        continue

                    coincidencia_hora = (
                        patron_hora.search(
                            texto_siguiente
                        )
                    )

                    if not coincidencia_hora:
                        continue

                    y_hora = float(
                        siguiente.get(
                            "y",
                            0
                        )
                    )

                    diferencia_y = (
                        y_hora
                        - y_fecha
                    )

                    if (
                        0
                        <= diferencia_y
                        <= 100
                    ):

                        hora = (
                            coincidencia_hora.group(
                                1
                            )
                        )

                        am_pm = (
                            coincidencia_hora.group(
                                2
                            ).upper()
                        )

                        deteccion_hora = siguiente

                        break

            if hora and am_pm:

                valor = (
                    f"{dia} {mes} {anio}, "
                    f"{hora} {am_pm}"
                )

                confianza_fecha = (
                    obtener_confianza(
                        deteccion_fecha
                    )
                )

                if deteccion_hora is not None:

                    confianza_hora = (
                        obtener_confianza(
                            deteccion_hora
                        )
                    )

                    confianza = min(
                        confianza_fecha,
                        confianza_hora
                    )

                else:

                    confianza = confianza_fecha

                return resultado_campo(
                    valor,
                    "coordenadas_fecha",
                    confianza
                )

    texto_completo = datos.get(
        "texto_completo",
        ""
    )

    if texto_completo:

        coincidencia_fecha = (
            patron_fecha.search(
                texto_completo
            )
        )

        if coincidencia_fecha:

            dia = coincidencia_fecha.group(
                1
            )

            mes = coincidencia_fecha.group(
                2
            ).upper()

            anio = coincidencia_fecha.group(
                3
            )

            texto_despues = (
                texto_completo[
                    coincidencia_fecha.end():
                ]
            )

            coincidencia_hora = (
                patron_hora.search(
                    texto_despues
                )
            )

            if coincidencia_hora:

                hora = coincidencia_hora.group(
                    1
                )

                am_pm = coincidencia_hora.group(
                    2
                ).upper()

                valor = (
                    f"{dia} {mes} {anio}, "
                    f"{hora} {am_pm}"
                )

                return resultado_campo(
                    valor,
                    "regex_fecha",
                    0.95
                )

    if texto_completo:

        coincidencia_fecha = (
            patron_fecha.search(
                texto_completo
            )
        )

        if coincidencia_fecha:

            valor = (
                f"{coincidencia_fecha.group(1)} "
                f"{coincidencia_fecha.group(2).upper()} "
                f"{coincidencia_fecha.group(3)}"
            )

            return resultado_campo(
                valor,
                "regex_fecha_sin_hora",
                0.90
            )

    # Respaldo: derivar fecha desde número de referencia (DDMMYY o DMMYY) cuando el encabezado oscuro fue distorsionado por OCR
    ref_res = extraer_numero_referencia(datos)
    ref_val = ref_res.get("valor") if isinstance(ref_res, dict) else None
    if ref_val and re.fullmatch(r"\d{5,6}", str(ref_val)):
        ref_str = str(ref_val).zfill(6)
        dia_r = ref_str[:2]
        mes_num = ref_str[2:4]
        anio_r = "20" + ref_str[4:6]
        meses_map = {
            "01": "ENE", "02": "FEB", "03": "MAR", "04": "ABR",
            "05": "MAY", "06": "JUN", "07": "JUL", "08": "AGO",
            "09": "SEP", "10": "OCT", "11": "NOV", "12": "DIC",
        }
        if mes_num in meses_map and 1 <= int(dia_r) <= 31:
            return resultado_campo(
                f"{dia_r} {meses_map[mes_num]} {anio_r}",
                "referencia_fecha_respaldo",
                0.85
            )

    return resultado_campo()


# ============================================================
# MONTO
# ============================================================

def extraer_monto(datos):

    detecciones = obtener_detecciones(
        datos
    )

    patron_monto = re.compile(
        r"^\$?\s*"
        r"\d{1,3}"
        r"(?:,\d{3})*"
        r"(?:\.\d{2})$"
    )

    candidatos = []

    for deteccion in detecciones:

        texto = limpiar_valor(
            deteccion.get(
                "texto"
            )
        )

        if not texto:
            continue

        limpio = texto.replace(
            " ",
            ""
        )

        if patron_monto.fullmatch(
            limpio
        ):

            candidatos.append(
                (
                    deteccion,
                    obtener_confianza(
                        deteccion
                    )
                )
            )

    if candidatos:

        candidatos.sort(
            key=lambda x: (
                x[0].get(
                    "y",
                    999999
                ),
                -x[1]
            )
        )

        deteccion, confianza = (
            candidatos[0]
        )

        return resultado_campo(
            deteccion.get(
                "texto"
            ),
            "deteccion_monto",
            confianza
        )

    texto_completo = datos.get(
        "texto_completo",
        ""
    )

    coincidencia = re.search(
        r"\bMonto\b\s*"
        r"(\$?\s*[\d,]+\.\d{2})",
        texto_completo,
        re.IGNORECASE
    )

    if coincidencia:

        return resultado_campo(
            coincidencia.group(1).replace(
                " ",
                ""
            ),
            "texto_monto",
            0.90
        )

    return resultado_campo()


# ============================================================
# TIPO DE TRANSFERENCIA
# ============================================================

def extraer_tipo_transferencia(datos):

    detecciones = obtener_detecciones(
        datos
    )

    encontro_spei = False
    encontro_gratuita = False

    confianza_spei = 0.0
    confianza_gratuita = 0.0

    for deteccion in detecciones:

        texto = limpiar_valor(
            deteccion.get(
                "texto"
            )
        )

        if not texto:
            continue

        normalizado = normalizar_texto(
            texto
        )

        if normalizado == "spei":

            encontro_spei = True

            confianza_spei = max(
                confianza_spei,
                obtener_confianza(
                    deteccion
                )
            )

        if normalizado == "transferencia gratuita":

            encontro_gratuita = True

            confianza_gratuita = max(
                confianza_gratuita,
                obtener_confianza(
                    deteccion
                )
            )

    if (
        encontro_spei
        and encontro_gratuita
    ):

        return resultado_campo(
            "Transferencia gratuita SPEI",
            "deteccion_tipo_transferencia",
            min(
                confianza_spei,
                confianza_gratuita
            )
        )

    if encontro_gratuita:

        return resultado_campo(
            "Transferencia gratuita",
            "deteccion_tipo_transferencia",
            confianza_gratuita
        )

    if encontro_spei:

        return resultado_campo(
            "SPEI",
            "deteccion_tipo_transferencia",
            confianza_spei
        )

    texto_completo = datos.get(
        "texto_completo",
        ""
    )

    normalizado = normalizar_texto(
        texto_completo
    )

    if (
        "transferencia gratuita"
        in normalizado
        and "spei"
        in normalizado
    ):

        return resultado_campo(
            "Transferencia gratuita SPEI",
            "texto_tipo_transferencia",
            0.90
        )

    if "transferencia gratuita" in normalizado:

        return resultado_campo(
            "Transferencia gratuita",
            "texto_tipo_transferencia",
            0.85
        )

    if re.search(
        r"\bspei\b",
        normalizado
    ):

        return resultado_campo(
            "SPEI",
            "texto_tipo_transferencia",
            0.85
        )

    return resultado_campo()


# ============================================================
# NÚMERO DE REFERENCIA
# ============================================================

def extraer_numero_referencia(datos):

    detecciones = obtener_detecciones(
        datos
    )

    for indice, deteccion in enumerate(
        detecciones
    ):

        texto = normalizar_texto(
            deteccion.get(
                "texto"
            )
        )

        if texto != "numero de referencia":
            continue

        x_etiqueta = float(
            deteccion.get(
                "x",
                0
            )
        )

        y_etiqueta = float(
            deteccion.get(
                "y",
                0
            )
        )

        candidatos = []

        for j, candidato in enumerate(
            detecciones
        ):

            if j == indice:
                continue

            valor = limpiar_valor(
                candidato.get(
                    "texto"
                )
            )

            if not valor:
                continue

            if not re.fullmatch(
                r"\d{1,20}",
                valor
            ):
                continue

            x = float(
                candidato.get(
                    "x",
                    0
                )
            )

            y = float(
                candidato.get(
                    "y",
                    0
                )
            )

            distancia_y = abs(
                y - y_etiqueta
            )

            distancia_x = abs(
                x - x_etiqueta
            )

            if distancia_y <= 45:

                candidatos.append(
                    (
                        distancia_y,
                        distancia_x,
                        candidato
                    )
                )

        if candidatos:

            candidatos.sort(
                key=lambda x: (
                    x[0],
                    x[1]
                )
            )

            candidato = candidatos[0][2]

            return resultado_campo(
                candidato.get(
                    "texto"
                ),
                "coordenadas_referencia",
                obtener_confianza(
                    candidato
                )
            )

    lineas = obtener_lineas(
        datos
    )

    for i, linea in enumerate(
        lineas
    ):

        normalizada = normalizar_texto(
            linea
        )

        if "numero de referencia" not in normalizada:
            continue

        coincidencia = re.search(
            r"numero de referencia\s*(\d{1,20})",
            linea,
            re.IGNORECASE
        )

        if coincidencia:

            return resultado_campo(
                coincidencia.group(1),
                "linea_referencia",
                0.95
            )

        if i + 1 < len(lineas):

            siguiente = lineas[
                i + 1
            ].strip()

            if re.fullmatch(
                r"\d{1,20}",
                siguiente
            ):

                return resultado_campo(
                    siguiente,
                    "linea_siguiente_referencia",
                    0.90
                )

    return resultado_campo()


# ============================================================
# BLOQUE CUENTA DESTINO
# ============================================================

def obtener_bloque_destino(detecciones):

    inicio = None
    fin = None

    for i, deteccion in enumerate(
        detecciones
    ):

        texto = normalizar_texto(
            deteccion.get(
                "texto"
            )
        )

        if texto == "cuenta destino":

            inicio = i

        elif (
            inicio is not None
            and texto == "cuenta origen"
        ):

            fin = i
            break

    if inicio is None:

        return detecciones

    if fin is None:

        fin = len(detecciones)

    return detecciones[
        inicio:fin
    ]


# ============================================================
# NOMBRE
# ============================================================

def extraer_nombre(datos):

    detecciones = obtener_detecciones(
        datos
    )

    bloque = obtener_bloque_destino(
        detecciones
    )

    indice_nombre = None
    y_limite_inferior = 999999.0

    for indice, deteccion in enumerate(
        bloque
    ):

        texto = normalizar_texto(
            deteccion.get(
                "texto"
            )
        )

        if (
            indice_nombre is None
            and (
                texto in ("nombre", "nombr", "nomb")
                or texto.startswith("nombre ")
                or texto.startswith("nombr ")
                or texto.startswith("nomb ")
            )
        ):
            indice_nombre = indice

        if texto == "entidad" or texto.startswith("dato no verificado") or "datvno" in texto:
            y_det = float(deteccion.get("y", 999999.0))
            if y_det < y_limite_inferior:
                y_limite_inferior = y_det

    if indice_nombre is None:

        return resultado_campo()

    etiqueta = bloque[
        indice_nombre
    ]

    x_etiqueta = float(
        etiqueta.get(
            "x",
            0
        )
    )

    y_etiqueta = float(
        etiqueta.get(
            "y",
            0
        )
    )

    candidatos = []

    # ========================================================
    # BUSCAR VALORES ALREDEDOR DE LA ETIQUETA
    #
    # El comprobante puede colocar el valor:
    #
    #        VALOR
    #        Nombre
    #
    # o:
    #
    #        Nombre        VALOR
    #
    # Por eso no usamos únicamente x > x_etiqueta.
    # ========================================================

    palabras_excluidas = {
        "nombre",
        "nombr",
        "nomb",
        "re",
        "e",
        "nu",
        "hsbc",
        "entidad",
        "clabe",
        "labe",
        "estatus",
        "cuenta destino",
        "cuenta origen",
    }

    texto_etiqueta_raw = limpiar_valor(etiqueta.get("texto")) or ""
    m_inline = re.match(r"^(?:nombre|nombr|nomb)\s+(.+)$", texto_etiqueta_raw, flags=re.IGNORECASE)
    if m_inline:
        candidatos.append(
            {
                "indice": indice_nombre,
                "texto": m_inline.group(1).strip(),
                "x": x_etiqueta + 50,
                "y": y_etiqueta,
                "confianza": obtener_confianza(etiqueta),
            }
        )

    for indice, deteccion in enumerate(
        bloque
    ):

        if indice == indice_nombre:
            continue

        texto = limpiar_valor(
            deteccion.get(
                "texto"
            )
        )

        if not texto:
            continue

        normalizado = normalizar_texto(
            texto
        )

        if normalizado in palabras_excluidas:
            continue

        if normalizado.startswith(
            "dato no verificado"
        ) or "datvno" in normalizado:
            continue

        x = float(
            deteccion.get(
                "x",
                0
            )
        )

        y = float(
            deteccion.get(
                "y",
                0
            )
        )

        diferencia_y = abs(
            y - y_etiqueta
        )

        # Aceptamos valores hasta 75 px arriba o abajo
        # de la etiqueta Nombre, sin pasar a Entidad / Dato no verificado.
        if diferencia_y <= 75 and y < y_limite_inferior - 2:

            candidatos.append(
                {
                    "indice": indice,
                    "texto": texto,
                    "x": x,
                    "y": y,
                    "confianza": obtener_confianza(
                        deteccion
                    )
                }
            )

    if not candidatos:

        return resultado_campo()

    # ========================================================
    # ORDENAR DE IZQUIERDA A DERECHA
    #
    # Esto permite reconstruir:
    #
    # IPTV... S DE RL
    # DE CV
    #
    # o:
    #
    # Irene Idania Martinez
    # Sanchez
    # ========================================================

    candidatos.sort(
        key=lambda x: (
            x["y"],
            x["x"]
        )
    )

    partes = []
    confianzas = []

    for candidato in candidatos:

        texto = candidato[
            "texto"
        ]

        # Evitar duplicados
        if texto in partes:
            continue

        partes.append(
            texto
        )

        confianzas.append(
            candidato[
                "confianza"
            ]
        )

    nombre = " ".join(
        partes
    ).strip()

    if nombre:

        return resultado_campo(
            nombre,
            "coordenadas_nombre",
            min(confianzas)
            if confianzas
            else 0.0
        )

    return resultado_campo()


# ============================================================
# ENTIDAD
# ============================================================

def extraer_entidad(datos):

    detecciones = obtener_detecciones(
        datos
    )

    bloque = obtener_bloque_destino(
        detecciones
    )

    indice_entidad = None

    for indice, deteccion in enumerate(
        bloque
    ):

        texto = normalizar_texto(
            deteccion.get(
                "texto"
            )
        )

        if texto == "entidad":

            indice_entidad = indice
            break

    if indice_entidad is None:

        return resultado_campo()

    etiqueta = bloque[
        indice_entidad
    ]

    x_etiqueta = float(
        etiqueta.get(
            "x",
            0
        )
    )

    y_etiqueta = float(
        etiqueta.get(
            "y",
            0
        )
    )

    candidatos = []

    palabras_excluidas = {
        "clabe",
        "estatus",
        "nombre",
        "entidad",
        "cuenta destino",
        "cuenta origen",
    }

    for indice, deteccion in enumerate(
        bloque
    ):

        if indice == indice_entidad:
            continue

        texto = limpiar_valor(
            deteccion.get(
                "texto"
            )
        )

        if not texto:
            continue

        normalizado = normalizar_texto(
            texto
        )

        if normalizado in palabras_excluidas:
            continue

        if normalizado.startswith(
            "dato no verificado"
        ) or "datvno" in normalizado:
            continue

        x = float(
            deteccion.get(
                "x",
                0
            )
        )

        y = float(
            deteccion.get(
                "y",
                0
            )
        )

        diferencia_y = abs(
            y - y_etiqueta
        )

        # IMPORTANTE:
        # Ya no existe el límite de 350 px.
        #
        # Esto permite casos como image_079:
        #
        # Entidad x=38
        # HSBC    x=613
        #
        # que son válidos.
        if (
            (diferencia_y <= 50 and x > x_etiqueta)
            or (0 < y - y_etiqueta <= 60 and abs(x - x_etiqueta) <= 80)
        ):

            candidatos.append(
                (
                    diferencia_y,
                    x,
                    deteccion
                )
            )

    if candidatos:

        candidatos.sort(
            key=lambda x: (
                x[0],
                x[1]
            )
        )

        candidato = candidatos[0][2]

        return resultado_campo(
            candidato.get(
                "texto"
            ),
            "coordenadas_entidad",
            obtener_confianza(
                candidato
            )
        )

    return resultado_campo()


# ============================================================
# CLABE
# ============================================================

def limpiar_clabe(texto):

    if not texto:

        return ""

    return re.sub(
        r"[^A-Za-z0-9*]",
        "",
        str(texto)
    )


def es_valor_clabe(texto):

    if not texto:

        return False

    limpio = limpiar_clabe(
        texto
    )

    if len(limpio) < 4:

        return False

    tiene_numero = any(
        c.isdigit()
        for c in limpio
    )

    tiene_mascara = any(
        c == "*"
        for c in limpio
    )

    return (
        tiene_numero
        and (
            tiene_mascara
            or len(limpio) <= 20
        )
    )


def extraer_clabe(datos):

    detecciones = obtener_detecciones(
        datos
    )

    bloque = obtener_bloque_destino(
        detecciones
    )

    indice_clabe = None

    for indice, deteccion in enumerate(
        bloque
    ):

        texto = normalizar_texto(
            deteccion.get(
                "texto"
            )
        )

        if texto in (
            "clabe",
            "labe",
            "tarjeta de debito"
        ):

            indice_clabe = indice
            break

    if indice_clabe is None:

        return resultado_campo()

    etiqueta = bloque[
        indice_clabe
    ]

    x_etiqueta = float(
        etiqueta.get(
            "x",
            0
        )
    )

    y_etiqueta = float(
        etiqueta.get(
            "y",
            0
        )
    )

    candidatos = []

    for indice, deteccion in enumerate(
        bloque
    ):

        if indice == indice_clabe:
            continue

        texto = limpiar_valor(
            deteccion.get(
                "texto"
            )
        )

        if not texto:
            continue

        if not es_valor_clabe(
            texto
        ):
            continue

        x = float(
            deteccion.get(
                "x",
                0
            )
        )

        y = float(
            deteccion.get(
                "y",
                0
            )
        )

        diferencia_y = abs(
            y - y_etiqueta
        )

        # Igual que Entidad:
        # no limitamos la distancia horizontal.
        if (
            (diferencia_y <= 50 and x > x_etiqueta)
            or (0 < y - y_etiqueta <= 60 and abs(x - x_etiqueta) <= 80)
        ):

            candidatos.append(
                (
                    diferencia_y,
                    x,
                    deteccion
                )
            )

    if candidatos:

        candidatos.sort(
            key=lambda x: (
                x[0],
                x[1]
            )
        )

        candidato = candidatos[0][2]

        valor = limpiar_clabe(
            candidato.get(
                "texto"
            )
        )

        return resultado_campo(
            valor,
            "coordenadas_clabe",
            obtener_confianza(
                candidato
            )
        )

    return resultado_campo()


# ============================================================
# CLAVE DE RASTREO
# ============================================================

def limpiar_clave_rastreo(texto):

    if not texto:

        return ""

    return re.sub(
        r"[^A-Za-z0-9]",
        "",
        str(texto)
    ).upper()


def es_fragmento_clave(texto):

    limpio = limpiar_clave_rastreo(
        texto
    )

    if len(limpio) < 2:

        return False

    return (
        any(
            c.isalpha()
            for c in limpio
        )
        and
        any(
            c.isdigit()
            for c in limpio
        )
    )


def es_clave_rastreo_valida(texto):

    limpio = limpiar_clave_rastreo(
        texto
    )

    return (
        len(limpio) >= 20
        and
        any(
            c.isalpha()
            for c in limpio
        )
        and
        any(
            c.isdigit()
            for c in limpio
        )
    )


def extraer_clave_rastreo(datos):

    detecciones = obtener_detecciones(
        datos
    )

    indices_etiqueta = []

    for indice, deteccion in enumerate(
        detecciones
    ):

        texto = normalizar_texto(
            deteccion.get(
                "texto"
            )
        )

        if texto in (
            "clave",
            "clave de",
            "rastreo",
            "clave de rastreo"
        ):

            indices_etiqueta.append(
                indice
            )

    candidatos = []

    for indice, deteccion in enumerate(
        detecciones
    ):

        texto = limpiar_valor(
            deteccion.get(
                "texto"
            )
        )

        if not texto:
            continue

        limpio = limpiar_clave_rastreo(
            texto
        )

        if not es_fragmento_clave(
            limpio
        ):
            continue

        normalizado = normalizar_texto(
            texto
        )

        if normalizado in (
            "spei",
            "aceptada",
            "hsbc",
            "nu mexico",
        ):

            continue

        x = float(
            deteccion.get(
                "x",
                0
            )
        )

        y = float(
            deteccion.get(
                "y",
                0
            )
        )

        confianza = obtener_confianza(
            deteccion
        )

        distancia_minima = 999999

        cerca = False

        for indice_etiqueta in indices_etiqueta:

            etiqueta = detecciones[
                indice_etiqueta
            ]

            xe = float(
                etiqueta.get(
                    "x",
                    0
                )
            )

            ye = float(
                etiqueta.get(
                    "y",
                    0
                )
            )

            distancia_y = abs(
                y - ye
            )

            distancia_x = abs(
                x - xe
            )

            if (
                distancia_y <= 120
                and distancia_x <= 500
            ):

                cerca = True

                distancia = (
                    distancia_y
                    + distancia_x
                )

                distancia_minima = min(
                    distancia_minima,
                    distancia
                )

        if cerca:

            candidatos.append(
                {
                    "indice": indice,
                    "texto": limpio,
                    "x": x,
                    "y": y,
                    "confianza": confianza,
                    "distancia": distancia_minima
                }
            )

    if not candidatos:

        return resultado_campo()

    candidatos.sort(
        key=lambda x: (
            x["y"],
            x["x"]
        )
    )

    # ========================================================
    # BUSCAR FRAGMENTOS QUE COMIENCEN CON NU
    # ========================================================

    for i, candidato in enumerate(
        candidatos
    ):

        base = candidato[
            "texto"
        ]

        if not base.startswith(
            "NU"
        ):

            continue

        acumulado = base
        if len(acumulado) < 29:
            idx_base = candidato["indice"]
            for k in range(idx_base + 1, min(idx_base + 5, len(detecciones))):
                t_raw = limpiar_valor(detecciones[k].get("texto"))
                if not t_raw:
                    continue
                t_norm = normalizar_texto(t_raw)
                if t_norm in ("de", "clave", "clave de", "rastreo"):
                    continue
                if t_norm in ("cuenta origen", "nombre", "estatus", "aceptada"):
                    break
                t_strip = t_raw.strip()
                if re.fullmatch(r"[A-Z0-9]{1,12}", t_strip) and len(acumulado) + len(t_strip) <= 30:
                    acumulado += t_strip
                    if len(acumulado) >= 28:
                        break
        if len(acumulado) > len(base) and es_clave_rastreo_valida(acumulado):
            return resultado_campo(acumulado, "detecciones_clave_rastreo_unidas", candidato["confianza"])

        confianzas = [
            candidato[
                "confianza"
            ]
        ]

        y_anterior = candidato[
            "y"
        ]

        x_anterior = candidato[
            "x"
        ]

        for siguiente in candidatos[
            i + 1:
        ]:

            diferencia_y = (
                siguiente["y"]
                - y_anterior
            )

            diferencia_x = abs(
                siguiente["x"]
                - x_anterior
            )

            if diferencia_y < 0:
                continue

            if diferencia_y > 90:
                break

            if diferencia_x > 400:
                continue

            fragmento = siguiente[
                "texto"
            ]

            if not es_fragmento_clave(
                fragmento
            ):
                continue

            acumulado += fragmento

            confianzas.append(
                siguiente[
                    "confianza"
                ]
            )

            y_anterior = siguiente[
                "y"
            ]

            x_anterior = siguiente[
                "x"
            ]

            if es_clave_rastreo_valida(
                acumulado
            ):

                return resultado_campo(
                    acumulado,
                    "detecciones_clave_rastreo_unidas",
                    min(confianzas)
                )

    # ========================================================
    # UNA SOLA DETECCIÓN
    # ========================================================

    for candidato in candidatos:

        valor = candidato[
            "texto"
        ]

        if es_clave_rastreo_valida(
            valor
        ):

            return resultado_campo(
                valor,
                "coordenadas_clave_rastreo",
                candidato[
                    "confianza"
                ]
            )

    # ========================================================
    # TEXTO COMPLETO
    # ========================================================

    texto_completo = datos.get(
        "texto_completo",
        ""
    )

    posibles = re.findall(
        r"\b[A-Z0-9]{20,}\b",
        texto_completo.upper()
    )

    for posible in posibles:

        if es_clave_rastreo_valida(
            posible
        ):

            return resultado_campo(
                posible,
                "texto_clave_rastreo",
                0.85
            )

    return resultado_campo()


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def extraer(datos):

    if not isinstance(
        datos,
        dict
    ):

        datos = {}

    campos = {

        "banco":
            extraer_banco(
                datos
            ),

        "fecha":
            extraer_fecha(
                datos
            ),

        "monto":
            extraer_monto(
                datos
            ),

        "tipo_transferencia":
            extraer_tipo_transferencia(
                datos
            ),

        "numero_referencia":
            extraer_numero_referencia(
                datos
            ),

        "nombre":
            extraer_nombre(
                datos
            ),

        "entidad":
            extraer_entidad(
                datos
            ),

        "clabe":
            extraer_clabe(
                datos
            ),

        "clave_rastreo":
            extraer_clave_rastreo(
                datos
            ),
    }

    return {
        "banco": BANCO,
        "tipo": TIPO_COMPROBANTE,
        "campos": campos
    }