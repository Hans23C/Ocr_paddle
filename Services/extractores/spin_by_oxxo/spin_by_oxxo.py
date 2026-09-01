import re
import unicodedata


BANCO = "SPIN BY OXXO"

TIPO_TRANSFERENCIA = "TRANSFERENCIA_SPIN_BY_OXXO"
TIPO_CEP = "CEP_SPIN_BY_OXXO"


# ============================================================
# UTILIDADES
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

    if any(
        x in texto
        for x in ("Ã", "Â", "â")
    ):

        try:

            texto = (
                texto
                .encode("latin1")
                .decode("utf-8")
            )

        except (
            UnicodeEncodeError,
            UnicodeDecodeError
        ):

            pass

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

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
        "confianza": confianza
    }


def campo_no_encontrado():

    return {
        "valor": "NO ENCONTRADO",
        "metodo": "NO ENCONTRADO",
        "confianza": 0.0
    }


# ============================================================
# EXTRACTOR SPIN BY OXXO
# ============================================================

class SpinByOxxoExtractor:

    # ========================================================
    # CONSTRUCTOR
    # ========================================================

    def __init__(
        self,
        detecciones=None
    ):

        self.detecciones = (
            detecciones
            if detecciones is not None
            else []
        )

    # ========================================================
    # UTILIDADES
    # ========================================================

    def _texto(self, deteccion):

        if not isinstance(
            deteccion,
            dict
        ):

            return ""

        return normalizar_texto(
            deteccion.get(
                "texto",
                ""
            )
        )

    def _texto_norm(self, deteccion):

        if not isinstance(
            deteccion,
            dict
        ):

            return ""

        texto_norm = deteccion.get(
            "texto_norm"
        )

        if texto_norm:

            return normalizar_busqueda(
                texto_norm
            )

        return normalizar_busqueda(
            self._texto(deteccion)
        )

    def _x(self, deteccion):

        try:

            return float(
                deteccion.get(
                    "x",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            return 0.0

    def _y(self, deteccion):

        try:

            return float(
                deteccion.get(
                    "y",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            return 0.0

    def _confianza(self, deteccion):

        try:

            return float(
                deteccion.get(
                    "confianza",
                    1.0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            return 1.0

    def _promedio_confianza(
        self,
        detecciones
    ):

        if not detecciones:

            return 0.0

        valores = [
            self._confianza(d)
            for d in detecciones
        ]

        return sum(valores) / len(valores)

    def _crear_campo(
        self,
        valor,
        metodo,
        confianza
    ):

        return campo_encontrado(
            valor,
            metodo,
            confianza
        )

    # ========================================================
    # OBTENER DETECCIONES
    # ========================================================

    def _obtener_detecciones(
        self,
        datos
    ):

        if isinstance(
            datos,
            list
        ):

            resultado = []

            for d in datos:

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

                copia = dict(d)

                copia["texto"] = texto

                copia["texto_norm"] = (
                    normalizar_busqueda(
                        texto
                    )
                )

                resultado.append(
                    copia
                )

            return resultado

        if not isinstance(
            datos,
            dict
        ):

            return []

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

            copia = dict(d)

            copia["texto"] = texto

            copia["texto_norm"] = (
                normalizar_busqueda(
                    texto
                )
            )

            resultado.append(
                copia
            )

        return resultado

    # ========================================================
    # BUSCAR ÍNDICE
    # ========================================================

    def _buscar_indice(
        self,
        detecciones,
        patron
    ):

        regex = re.compile(
            patron,
            re.IGNORECASE
        )

        for i, deteccion in enumerate(
            detecciones
        ):

            texto = self._texto(
                deteccion
            )

            texto_norm = self._texto_norm(
                deteccion
            )

            if regex.search(texto):

                return i

            if regex.search(texto_norm):

                return i

        return None

    # ========================================================
    # DETECTAR CEP
    # ========================================================

    def _es_formato_cep(
        self,
        detecciones
    ):

        texto = " ".join(
            self._texto_norm(d)
            for d in detecciones
        )

        indicadores = [

            "fecha de operacion en el spei",

            "fecha de abono en la cuenta beneficiaria",

            "hora de abono en la cuenta beneficiaria",

            "institucion emisora del pago",

            "institucion receptora del pago",

            "titular de la cuenta",

            "rfc/curp",

            "cadena original",

            "comprobante electronico de pago"

        ]

        encontrados = sum(
            indicador in texto
            for indicador in indicadores
        )

        return encontrados >= 2

    # ========================================================
    # BANCO
    # ========================================================

    def _extraer_banco(
        self,
        detecciones
    ):

        tiene_spin = False
        tiene_oxxo = False

        for d in detecciones:

            texto_norm = self._texto_norm(d)

            if texto_norm == "spin":

                tiene_spin = True

            if (
                "by oxxo" in texto_norm
                or texto_norm == "byoxxo"
            ):

                tiene_oxxo = True

        if tiene_spin and tiene_oxxo:

            return self._crear_campo(
                BANCO,
                "deteccion_banco",
                1.0
            )

        return None

    # ========================================================
    # MONTO
    # ========================================================

    def _extraer_monto(
        self,
        detecciones
    ):

        for d in detecciones:

            texto = self._texto(d)

            encontrados = re.findall(
                r"-?\$\s*[\d,]+(?:\.\d{1,2})?",
                texto
            )

            if encontrados:

                valor = re.sub(
                    r"\s+",
                    "",
                    encontrados[0]
                )

                return self._crear_campo(
                    valor,
                    "deteccion_monto",
                    self._confianza(d)
                )

        return None

    # ========================================================
    # FECHA
    # ========================================================

    def _extraer_fecha(
        self,
        detecciones
    ):

        # ----------------------------------------------------
        # CEP
        # ----------------------------------------------------

        indice = self._buscar_indice(
            detecciones,
            r"fecha\s+de\s+operaci[oó]n\s+en\s+el\s+spei"
        )

        if indice is not None:

            etiqueta = detecciones[
                indice
            ]

            x_etiqueta = self._x(
                etiqueta
            )

            y_etiqueta = self._y(
                etiqueta
            )

            patron = re.compile(
                r"\b\d{1,2}\s+de\s+"
                r"[A-Za-zÁÉÍÓÚáéíóúÑñ]+"
                r"\s+de\s+\d{4}\b",
                re.IGNORECASE
            )

            candidatos = []

            for d in detecciones:

                if d is etiqueta:

                    continue

                if self._x(d) <= x_etiqueta:

                    continue

                if abs(
                    self._y(d)
                    - y_etiqueta
                ) > 35:

                    continue

                match = patron.search(
                    self._texto(d)
                )

                if match:

                    candidatos.append(
                        (
                            abs(
                                self._y(d)
                                - y_etiqueta
                            ),
                            self._x(d),
                            d,
                            match.group(0)
                        )
                    )

            if candidatos:

                candidatos.sort(
                    key=lambda x: (
                        x[0],
                        x[1]
                    )
                )

                _, _, d, valor = (
                    candidatos[0]
                )

                return self._crear_campo(
                    valor,
                    "etiqueta_fecha_operacion_spei",
                    self._confianza(d)
                )

        # ----------------------------------------------------
        # TRANSFERENCIA NORMAL
        # ----------------------------------------------------

        patron = re.compile(
            r"\b\d{1,2}/"
            r"\d{1,2}/"
            r"\d{4}"
            r"(?:\s+\d{1,2}:"
            r"\d{2}:"
            r"\d{2})?",
            re.IGNORECASE
        )

        for d in detecciones:

            match = patron.search(
                self._texto(d)
            )

            if match:

                return self._crear_campo(
                    match.group(0),
                    "regex_fecha",
                    self._confianza(d)
                )

        return None

    # ========================================================
    # DESTINO
    # ========================================================

    def _extraer_destino(
        self,
        detecciones
    ):

        for i, d in enumerate(
            detecciones
        ):

            texto = self._texto(d)

            if not re.match(
                r"^\s*a\s+",
                texto,
                re.IGNORECASE
            ):

                continue

            partes = []

            texto = re.sub(
                r"^\s*a\s+",
                "",
                texto,
                flags=re.IGNORECASE
            )

            if texto:

                partes.append(
                    texto
                )

            usadas = [d]

            for j in range(
                i + 1,
                min(
                    i + 4,
                    len(detecciones)
                )
            ):

                siguiente = self._texto(
                    detecciones[j]
                )

                if not siguiente:

                    continue

                if re.search(
                    r"dato no verificado|HSBC",
                    siguiente,
                    re.IGNORECASE
                ):

                    break

                partes.append(
                    siguiente
                )

                usadas.append(
                    detecciones[j]
                )

            if partes:

                return self._crear_campo(
                    " ".join(partes),
                    "etiqueta_destino",
                    self._promedio_confianza(
                        usadas
                    )
                )

        return None

    # ========================================================
    # HSBC
    # ========================================================

    def _extraer_hsbc(
        self,
        detecciones
    ):

        regex = re.compile(
            r"HSBC\s*-\s*"
            r"(?:\*+\s*)?"
            r"(\d{10,20})",
            re.IGNORECASE
        )

        for d in detecciones:

            match = regex.search(
                self._texto(d)
            )

            if match:

                return self._crear_campo(
                    match.group(1),
                    "regex_hsbc",
                    self._confianza(d)
                )

        # CEP

        indice = self._buscar_indice(
            detecciones,
            r"instituci[oó]n\s+receptora\s+del\s+pago"
        )

        if indice is None:

            return None

        y_base = self._y(
            detecciones[indice]
        )

        candidatos = []

        for d in detecciones:

            texto = self._texto(d)

            if not re.fullmatch(
                r"\d{18}",
                texto
            ):

                continue

            if self._x(d) < 350:

                continue

            if self._y(d) < y_base:

                continue

            if self._y(d) - y_base > 120:

                continue

            candidatos.append(d)

        if candidatos:

            candidatos.sort(
                key=lambda d: (
                    self._y(d),
                    self._x(d)
                )
            )

            d = candidatos[0]

            return self._crear_campo(
                self._texto(d),
                "etiqueta_cuenta_hsbc_cep",
                self._confianza(d)
            )

        return None

    # ========================================================
    # CUENTA SPIN
    # ========================================================

    def _extraer_cuenta_spin(
        self,
        detecciones
    ):

        indice = self._buscar_indice(
            detecciones,
            r"n[uú]mero\s+de\s+cuenta\s+spin"
        )

        if indice is not None:

            y_base = self._y(
                detecciones[indice]
            )

            candidatos = []

            for d in detecciones:

                texto = self._texto(d)

                if not re.fullmatch(
                    r"\d{15,25}",
                    texto
                ):

                    continue

                if self._x(d) <= self._x(
                    detecciones[indice]
                ):

                    continue

                if abs(
                    self._y(d)
                    - y_base
                ) > 60:

                    continue

                candidatos.append(d)

            if candidatos:

                candidatos.sort(
                    key=lambda d: (
                        abs(
                            self._y(d)
                            - y_base
                        ),
                        self._x(d)
                    )
                )

                d = candidatos[0]

                return self._crear_campo(
                    self._texto(d),
                    "etiqueta_cuenta_spin",
                    self._confianza(d)
                )

        # CEP

        candidatos = []

        for d in detecciones:

            texto = self._texto(d)

            if re.fullmatch(
                r"\d{18,25}",
                texto
            ):

                candidatos.append(d)

        for d in candidatos:

            if self._x(d) < 350:

                return self._crear_campo(
                    self._texto(d),
                    "etiqueta_cuenta_spin_cep",
                    self._confianza(d)
                )

        return None

    # ========================================================
    # REFERENCIA
    # ========================================================

    def _extraer_referencia(
        self,
        detecciones
    ):

        indice = self._buscar_indice(
            detecciones,
            r"n[uú]mero\s+de\s+referencia"
        )

        if indice is None:

            return None

        etiqueta = detecciones[indice]

        candidatos = []

        for d in detecciones:

            texto = self._texto(d)

            if not re.fullmatch(
                r"\d{4,10}",
                texto
            ):

                continue

            if self._x(d) <= self._x(
                etiqueta
            ):

                continue

            if abs(
                self._y(d)
                - self._y(etiqueta)
            ) > 60:

                continue

            candidatos.append(d)

        if candidatos:

            candidatos.sort(
                key=lambda d: (
                    abs(
                        self._y(d)
                        - self._y(etiqueta)
                    ),
                    self._x(d)
                )
            )

            d = candidatos[0]

            return self._crear_campo(
                self._texto(d),
                "etiqueta_referencia",
                self._confianza(d)
            )

        return None

    # ========================================================
    # ID MOVIMIENTO
    # ========================================================

    def _extraer_id_movimiento(
        self,
        detecciones
    ):

        indice = self._buscar_indice(
            detecciones,
            r"id\s+de\s+movimiento"
        )

        if indice is None:

            return None

        etiqueta = detecciones[indice]

        candidatos = []

        for i, d in enumerate(
            detecciones
        ):

            texto = self._texto(d)

            if not re.fullmatch(
                r"#[A-Fa-f0-9]+",
                texto
            ):

                continue

            if abs(
                self._y(d)
                - self._y(etiqueta)
            ) > 100:

                continue

            candidatos.append(
                (
                    abs(
                        self._y(d)
                        - self._y(etiqueta)
                    ),
                    i,
                    d
                )
            )

        if not candidatos:

            return None

        candidatos.sort(
            key=lambda x: x[0]
        )

        _, indice_inicio, inicio = (
            candidatos[0]
        )

        partes = [
            self._texto(inicio)
        ]

        usadas = [
            inicio
        ]

        y_inicio = self._y(
            inicio
        )

        x_inicio = self._x(
            inicio
        )

        continuaciones = []

        for i, d in enumerate(
            detecciones
        ):

            if i == indice_inicio:

                continue

            texto = self._texto(d)

            if not re.fullmatch(
                r"[A-Fa-f0-9]+",
                texto
            ):

                continue

            x = self._x(d)
            y = self._y(d)

            if y < y_inicio:

                continue

            if y - y_inicio > 100:

                continue

            if x < x_inicio - 100:

                continue

            if x > x_inicio + 700:

                continue

            continuaciones.append(
                (
                    y,
                    x,
                    d
                )
            )

        continuaciones.sort(
            key=lambda item: (
                item[0],
                item[1]
            )
        )

        for _, _, d in continuaciones:

            partes.append(
                self._texto(d)
            )

            usadas.append(d)

            if len(partes) >= 3:

                break

        valor = "".join(partes)

        valor = re.sub(
            r"\s+",
            "",
            valor
        )

        if not re.fullmatch(
            r"#[A-Fa-f0-9]+",
            valor
        ):

            return None

        return self._crear_campo(
            valor,
            "etiqueta_id_movimiento",
            self._promedio_confianza(
                usadas
            )
        )

    # ========================================================
    # CLAVE DE RASTREO
    # ========================================================

    def _extraer_clave_rastreo(
        self,
        detecciones
    ):

        indice = self._buscar_indice(
            detecciones,
            r"clave\s+de\s+rastreo"
        )

        if indice is None:

            return None

        etiqueta = detecciones[indice]

        y_etiqueta = self._y(
            etiqueta
        )

        candidatos = []

        for i, d in enumerate(
            detecciones
        ):

            texto = self._texto(d)

            match = re.search(
                r"\bSPIN-[A-Za-z0-9]+\b",
                texto,
                re.IGNORECASE
            )

            if not match:

                continue

            if abs(
                self._y(d)
                - y_etiqueta
            ) > 100:

                continue

            candidatos.append(
                (
                    abs(
                        self._y(d)
                        - y_etiqueta
                    ),
                    self._x(d),
                    i,
                    d,
                    match.group(0)
                )
            )

        if not candidatos:

            return None

        candidatos.sort(
            key=lambda item: (
                item[0],
                item[1]
            )
        )

        (
            _,
            _,
            indice_inicio,
            inicio,
            valor_inicio
        ) = candidatos[0]

        partes = [
            valor_inicio
        ]

        usadas = [
            inicio
        ]

        y_inicio = self._y(
            inicio
        )

        x_inicio = self._x(
            inicio
        )

        continuaciones = []

        for i, d in enumerate(
            detecciones
        ):

            if i == indice_inicio:

                continue

            texto = self._texto(d)

            if not re.fullmatch(
                r"[A-Za-z0-9]+",
                texto
            ):

                continue

            x = self._x(d)
            y = self._y(d)

            if y < y_inicio:

                continue

            if y - y_inicio > 100:

                continue

            if x < x_inicio - 50:

                continue

            if x > x_inicio + 800:

                continue

            # ================================================
            # IMPORTANTE:
            #
            # La continuación de la clave debe estar
            # inmediatamente debajo de la primera parte.
            #
            # No tomar Concepto ni sus valores.
            # ================================================

            if self._texto_norm(d) in {

                "concepto",
                "cantidad total",
                "internet",
                "pago de internet",
                "becerril"

            }:

                continue

            continuaciones.append(
                (
                    y,
                    x,
                    d
                )
            )

        continuaciones.sort(
            key=lambda item: (
                item[0],
                item[1]
            )
        )

        if continuaciones:

            _, _, d = continuaciones[0]

            partes.append(
                self._texto(d)
            )

            usadas.append(d)

        valor = "".join(partes)

        valor = re.sub(
            r"\s+",
            "",
            valor
        )

        if not re.fullmatch(
            r"SPIN-[A-Za-z0-9]{10,}",
            valor,
            re.IGNORECASE
        ):

            return None

        return self._crear_campo(
            valor,
            "etiqueta_clave_rastreo",
            self._promedio_confianza(
                usadas
            )
        )

    # ========================================================
    # CONCEPTO
    #
    # CORRECCIÓN PRINCIPAL
    # ========================================================

    def _extraer_concepto(
        self,
        detecciones
    ):

        # ====================================================
        # CEP
        # ====================================================

        indice_cep = self._buscar_indice(
            detecciones,
            r"^\s*concepto\s+del\s+pago\s*$"
        )

        if indice_cep is not None:

            etiqueta = detecciones[
                indice_cep
            ]

            x_etiqueta = self._x(
                etiqueta
            )

            y_etiqueta = self._y(
                etiqueta
            )

            candidatos = []

            for d in detecciones:

                if d is etiqueta:

                    continue

                texto = self._texto(d)

                if not texto:

                    continue

                x = self._x(d)
                y = self._y(d)

                if x <= x_etiqueta:

                    continue

                if abs(
                    y - y_etiqueta
                ) > 35:

                    continue

                if self._texto_norm(d) in {

                    "concepto del pago",
                    "clave de rastreo",
                    "referencia numerica",
                    "institucion emisora del pago",
                    "institucion receptora del pago",
                    "titular de la cuenta",
                    "rfc/curp",
                    "iva"

                }:

                    continue

                candidatos.append(d)

            if candidatos:

                candidatos.sort(
                    key=lambda d: (
                        abs(
                            self._y(d)
                            - y_etiqueta
                        ),
                        self._x(d)
                    )
                )

                d = candidatos[0]

                return self._crear_campo(
                    self._texto(d),
                    "etiqueta_concepto_pago",
                    self._confianza(d)
                )

        # ====================================================
        # TRANSFERENCIA NORMAL
        # ====================================================

        indice = self._buscar_indice(
            detecciones,
            r"^\s*concepto\s*$"
        )

        if indice is None:

            return None

        etiqueta = detecciones[indice]

        x_etiqueta = self._x(
            etiqueta
        )

        y_etiqueta = self._y(
            etiqueta
        )

        # ====================================================
        # PRIMERA PRIORIDAD:
        #
        # Buscar una detección alineada con Concepto.
        #
        # Ejemplo:
        #
        # Concepto       Pago de Internet
        #
        # y(Concepto) = 973
        # y(Pago...)  = 974
        #
        # Diferencia = 1
        #
        # Esto evita tomar G3PE96YT.
        # ====================================================

        candidatos_alineados = []

        for d in detecciones:

            if d is etiqueta:

                continue

            texto = self._texto(d)

            if not texto:

                continue

            x = self._x(d)
            y = self._y(d)

            if x <= x_etiqueta:

                continue

            diferencia_y = abs(
                y - y_etiqueta
            )

            # MUY IMPORTANTE:
            # Para el concepto principal exigimos
            # alineación muy cercana.
            if diferencia_y > 15:

                continue

            texto_norm = self._texto_norm(d)

            # -----------------------------------------------
            # No tomar otras etiquetas.
            # -----------------------------------------------

            if texto_norm in {

                "concepto",
                "cantidad total",
                "id de movimiento",
                "clave de rastreo",
                "numero de referencia",
                "numero de cuenta",
                "numero de cuenta spin",
                "spin",
                "byoxxo",
                "aceptada"

            }:

                continue

            # -----------------------------------------------
            # No tomar dinero.
            # -----------------------------------------------

            if re.fullmatch(
                r"-?\$?\s*[\d,]+(?:\.\d{1,2})?",
                texto
            ):

                continue

            # -----------------------------------------------
            # No tomar clave.
            # -----------------------------------------------

            if re.fullmatch(
                r"SPIN-[A-Za-z0-9]+",
                texto,
                re.IGNORECASE
            ):

                continue

            # -----------------------------------------------
            # No tomar ID.
            # -----------------------------------------------

            if re.fullmatch(
                r"#[A-Fa-f0-9]+",
                texto
            ):

                continue

            candidatos_alineados.append(
                (
                    diferencia_y,
                    x,
                    d
                )
            )

        if candidatos_alineados:

            candidatos_alineados.sort(
                key=lambda item: (
                    item[0],
                    item[1]
                )
            )

            _, _, d = (
                candidatos_alineados[0]
            )

            return self._crear_campo(
                self._texto(d),
                "etiqueta_concepto",
                self._confianza(d)
            )

        # ====================================================
        # SEGUNDA PRIORIDAD:
        #
        # Conceptos partidos en dos detecciones.
        #
        # Ejemplo:
        #
        # Jose Roberto Iglesias
        # Concepto
        # Becerril
        #
        # Aquí no podemos exigir alineación exacta porque
        # las partes están arriba y abajo de la etiqueta.
        # ====================================================

        candidatos = []

        for d in detecciones:

            if d is etiqueta:

                continue

            texto = self._texto(d)

            if not texto:

                continue

            x = self._x(d)
            y = self._y(d)

            if x <= x_etiqueta:

                continue

            if x > 1100:

                continue

            diferencia_y = abs(
                y - y_etiqueta
            )

            if diferencia_y > 40:

                continue

            texto_norm = self._texto_norm(d)

            if texto_norm in {

                "concepto",
                "cantidad total",
                "id de movimiento",
                "clave de rastreo",
                "numero de referencia",
                "numero de cuenta",
                "numero de cuenta spin",
                "spin",
                "byoxxo",
                "aceptada"

            }:

                continue

            if re.fullmatch(
                r"-?\$?\s*[\d,]+(?:\.\d{1,2})?",
                texto
            ):

                continue

            if re.fullmatch(
                r"SPIN-[A-Za-z0-9]+",
                texto,
                re.IGNORECASE
            ):

                continue

            if re.fullmatch(
                r"#[A-Fa-f0-9]+",
                texto
            ):

                continue

            candidatos.append(
                (
                    y,
                    x,
                    d
                )
            )

        if candidatos:

            candidatos.sort(
                key=lambda item: (
                    item[0],
                    item[1]
                )
            )

            partes = []
            usadas = []

            for _, _, d in candidatos:

                texto = self._texto(d)

                if texto in partes:

                    continue

                partes.append(
                    texto
                )

                usadas.append(
                    d
                )

            if partes:

                valor = " ".join(
                    partes
                )

                valor = re.sub(
                    r"\s+",
                    " ",
                    valor
                ).strip()

                return self._crear_campo(
                    valor,
                    "etiqueta_concepto",
                    self._promedio_confianza(
                        usadas
                    )
                )

        return None

    # ========================================================
    # TITULAR CEP
    # ========================================================

    def _extraer_titular(
        self,
        detecciones
    ):

        etiquetas = [

            d
            for d in detecciones
            if self._texto_norm(d)
            == "titular de la cuenta"

        ]

        if not etiquetas:

            return None

        etiqueta = max(
            etiquetas,
            key=lambda d: self._x(d)
        )

        x_etiqueta = self._x(
            etiqueta
        )

        y_etiqueta = self._y(
            etiqueta
        )

        candidatos = []

        for d in detecciones:

            if d is etiqueta:

                continue

            texto = self._texto(d)

            if not texto:

                continue

            x = self._x(d)
            y = self._y(d)

            if x <= x_etiqueta:

                continue

            if y < y_etiqueta - 10:

                continue

            if y > y_etiqueta + 70:

                continue

            if self._texto_norm(d) in {

                "titular de la cuenta",
                "institucion emisora del pago",
                "institucion receptora del pago",
                "rfc/curp"

            }:

                continue

            if re.search(
                r"\d",
                texto
            ):

                continue

            candidatos.append(d)

        if not candidatos:

            return None

        candidatos.sort(
            key=lambda d: (
                self._y(d),
                self._x(d)
            )
        )

        partes = []
        usadas = []

        for d in candidatos:

            partes.append(
                self._texto(d)
            )

            usadas.append(d)

            if len(partes) >= 3:

                break

        return self._crear_campo(
            " ".join(partes),
            "etiqueta_titular_cuenta",
            self._promedio_confianza(
                usadas
            )
        )

    # ========================================================
    # INSTITUCIÓN EMISORA CEP
    # ========================================================

    def _extraer_institucion_emisora(
        self,
        detecciones
    ):

        indice = self._buscar_indice(
            detecciones,
            r"instituci[oó]n\s+emisora\s+del\s+pago"
        )

        if indice is None:

            return None

        etiqueta = detecciones[indice]

        for d in detecciones:

            if (
                self._x(d)
                > self._x(etiqueta)
                and
                abs(
                    self._y(d)
                    - self._y(etiqueta)
                ) <= 25
            ):

                texto = self._texto(d)

                if texto:

                    return self._crear_campo(
                        texto,
                        "etiqueta_institucion_emisora",
                        self._confianza(d)
                    )

        return None

    # ========================================================
    # INSTITUCIÓN RECEPTORA CEP
    # ========================================================

    def _extraer_institucion_receptora(
        self,
        detecciones
    ):

        indice = self._buscar_indice(
            detecciones,
            r"instituci[oó]n\s+receptora\s+del\s+pago"
        )

        if indice is None:

            return None

        etiqueta = detecciones[indice]

        candidatos = []

        for d in detecciones:

            if self._x(d) <= self._x(
                etiqueta
            ):

                continue

            if abs(
                self._y(d)
                - self._y(etiqueta)
            ) > 25:

                continue

            texto = self._texto(d)

            if texto:

                candidatos.append(d)

        if candidatos:

            candidatos.sort(
                key=lambda d: self._x(d)
            )

            d = candidatos[0]

            return self._crear_campo(
                self._texto(d),
                "etiqueta_institucion_receptora",
                self._confianza(d)
            )

        return None

    # ========================================================
    # EXTRAER CEP
    # ========================================================

    def _extraer_cep(
        self,
        detecciones
    ):

        campos = {}

        campo = self._extraer_banco(
            detecciones
        )

        if campo:
            campos["banco"] = campo

        campo = self._extraer_monto(
            detecciones
        )

        if campo:
            campos["monto"] = campo

        campo = self._extraer_fecha(
            detecciones
        )

        if campo:
            campos["fecha"] = campo

        campo = self._extraer_titular(
            detecciones
        )

        if campo:
            campos["titular_cuenta"] = campo

        campo = self._extraer_hsbc(
            detecciones
        )

        if campo:
            campos["cuenta_hsbc"] = campo

        campo = self._extraer_cuenta_spin(
            detecciones
        )

        if campo:
            campos["cuenta_spin"] = campo

        campo = self._extraer_referencia(
            detecciones
        )

        if campo:
            campos["numero_referencia"] = campo

        campo = self._extraer_clave_rastreo(
            detecciones
        )

        if campo:
            campos["clave_rastreo"] = campo

        campo = self._extraer_concepto(
            detecciones
        )

        if campo:
            campos["concepto"] = campo

        campo = self._extraer_institucion_emisora(
            detecciones
        )

        if campo:
            campos["institucion_emisora"] = campo

        campo = self._extraer_institucion_receptora(
            detecciones
        )

        if campo:
            campos["institucion_receptora"] = campo

        return campos

    # ========================================================
    # EXTRAER TRANSFERENCIA
    # ========================================================

    def _extraer_transferencia(
        self,
        detecciones
    ):

        campos = {}

        campo = self._extraer_banco(
            detecciones
        )

        if campo:
            campos["banco"] = campo

        campo = self._extraer_monto(
            detecciones
        )

        if campo:
            campos["monto"] = campo

        campo = self._extraer_fecha(
            detecciones
        )

        if campo:
            campos["fecha"] = campo

        campo = self._extraer_destino(
            detecciones
        )

        if campo:
            campos["destino"] = campo

        campo = self._extraer_hsbc(
            detecciones
        )

        if campo:
            campos["cuenta_hsbc"] = campo

        campo = self._extraer_cuenta_spin(
            detecciones
        )

        if campo:
            campos["cuenta_spin"] = campo

        campo = self._extraer_referencia(
            detecciones
        )

        if campo:
            campos["numero_referencia"] = campo

        campo = self._extraer_id_movimiento(
            detecciones
        )

        if campo:
            campos["id_movimiento"] = campo

        campo = self._extraer_clave_rastreo(
            detecciones
        )

        if campo:
            campos["clave_rastreo"] = campo

        campo = self._extraer_concepto(
            detecciones
        )

        if campo:
            campos["concepto"] = campo

        return campos

    # ========================================================
    # MÉTODO PÚBLICO
    #
    # NO CAMBIAR FIRMA
    # ========================================================

    def extraer(
        self,
        datos
    ):

        detecciones = self._obtener_detecciones(
            datos
        )

        if not detecciones:

            detecciones = self.detecciones

        if self._es_formato_cep(
            detecciones
        ):

            campos = self._extraer_cep(
                detecciones
            )

            tipo = TIPO_CEP

        else:

            campos = self._extraer_transferencia(
                detecciones
            )

            tipo = TIPO_TRANSFERENCIA

        return {

            "banco": BANCO,

            "tipo": tipo,

            "campos": campos

        }

    # ========================================================
    # COMPATIBILIDAD
    # ========================================================

    def extract(
        self,
        datos
    ):

        return self.extraer(
            datos
        )

    def extraer_datos(
        self,
        datos
    ):

        return self.extraer(
            datos
        )


# ============================================================
# FUNCIÓN PÚBLICA
# ============================================================

def extraer(
    datos_json
):

    extractor = SpinByOxxoExtractor()

    return extractor.extraer(
        datos_json
    )


# ============================================================
# FACTORY
# ============================================================

def crear_extractor():

    return SpinByOxxoExtractor()