import re


class BanamexExtractor:

    # ============================================================
    # UTILIDADES
    # ============================================================

    def _obtener_detecciones(self, datos):

        if isinstance(datos, list):
            return datos

        if isinstance(datos, dict):

            if "detecciones" in datos:
                return datos["detecciones"]

            if "resultados" in datos:
                return datos["resultados"]

            if "ocr" in datos:
                return datos["ocr"]

        return []

    # ============================================================
    # BANCO
    # ============================================================

    def extraer_banco(self, detecciones):

        for deteccion in detecciones:

            texto = str(
                deteccion.get("texto", "")
            ).strip()

            if texto.lower() == "banamex":
                return "Banamex"

        return None

    # ============================================================
    # FECHA
    # ============================================================

    def extraer_fecha(self, detecciones):

        patrones_fecha = [
            r"\d{1,2}\s+de\s+[A-Za-záéíóúÁÉÍÓÚ]+\s+de\s+\d{4}",
            r"\d{1,2}\s+[A-Za-záéíóúÁÉÍÓÚ]+\s+\d{4}\s+\d{1,2}:\d{2}(?::\d{2})?\s*h?",
            r"\d{1,2}\s+[A-Za-záéíóúÁÉÍÓÚ]+\s+\d{4}",
            r"\d{1,2}/\d{1,2}/\d{4}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?",
            r"\d{1,2}-\d{1,2}-\d{4}",
        ]

        for i, deteccion in enumerate(detecciones):

            texto = str(
                deteccion.get("texto", "")
            ).strip()

            texto_normalizado = (
                texto
                .lower()
                .replace("®", "")
                .replace("\xa0", " ")
            )

            texto_normalizado = re.sub(
                r"\s+",
                " ",
                texto_normalizado
            ).strip()

            # ----------------------------------------------------
            # SPEI
            # ----------------------------------------------------

            if (
                "fecha de operación en el spei" in texto_normalizado
                or "fecha de operacion en el spei" in texto_normalizado
            ):

                for j in range(
                    i + 1,
                    min(i + 10, len(detecciones))
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if not valor:
                        continue

                    for patron in patrones_fecha:

                        if re.fullmatch(
                            patron,
                            valor
                        ):
                            return valor

            # ----------------------------------------------------
            # CEP
            # ----------------------------------------------------

            if "fecha en la que realizó el" in texto_normalizado:

                for j in range(
                    i + 1,
                    min(i + 8, len(detecciones))
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if not valor:
                        continue

                    for patron in patrones_fecha:

                        if re.fullmatch(
                            patron,
                            valor
                        ):
                            return valor

            # ----------------------------------------------------
            # FECHA Y HORA DE RECEPCIÓN / PROCESAMIENTO
            # ----------------------------------------------------

            if (
                "fecha y hora de recepción" in texto_normalizado
                or "fecha y hora de recepcion" in texto_normalizado
                or "fecha y hora de procesamiento" in texto_normalizado
            ):

                for j in range(
                    i + 1,
                    min(i + 6, len(detecciones))
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if not valor:
                        continue

                    for patron in patrones_fecha:

                        if re.fullmatch(
                            patron,
                            valor
                        ):
                            return valor

            # ----------------------------------------------------
            # FECHA Y HORA
            # ----------------------------------------------------

            if texto_normalizado == "fecha y hora":

                for j in range(
                    i + 1,
                    min(i + 6, len(detecciones))
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if not valor:
                        continue

                    for patron in patrones_fecha:

                        if re.fullmatch(
                            patron,
                            valor
                        ):
                            return valor

                for j in range(
                    max(0, i - 4),
                    i
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if not valor:
                        continue

                    for patron in patrones_fecha:

                        if re.fullmatch(
                            patron,
                            valor
                        ):
                            return valor

        # --------------------------------------------------------
        # BANCANET
        #
        # En algunos comprobantes BancaNet existen dos fechas:
        #
        # 03 Jun 2026 11:29:31
        #
        # Fecha:
        # 03 Jun 2026
        #
        # Para la extracción solicitada se debe preferir la fecha
        # correspondiente al campo "Fecha:".
        # --------------------------------------------------------

        for i, deteccion in enumerate(detecciones):

            texto = str(
                deteccion.get("texto", "")
            ).strip()

            texto_normalizado = (
                texto
                .lower()
                .replace("®", "")
                .replace("\xa0", " ")
            )

            texto_normalizado = re.sub(
                r"\s+",
                " ",
                texto_normalizado
            ).strip()

            if texto_normalizado in (
                "fecha",
                "fecha:"
            ):

                for j in range(
                    i + 1,
                    min(i + 4, len(detecciones))
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if not valor:
                        continue

                    for patron in patrones_fecha:

                        if re.fullmatch(
                            patron,
                            valor
                        ):
                            return valor

        # --------------------------------------------------------
        # ÚLTIMO RECURSO
        # --------------------------------------------------------

        for deteccion in detecciones:

            valor = str(
                deteccion.get("texto", "")
            ).strip()

            if not valor:
                continue

            for patron in patrones_fecha:

                if re.fullmatch(
                    patron,
                    valor
                ):
                    return valor

        return None

    # ============================================================
    # MONTO
    # ============================================================

    def extraer_monto(self, detecciones):

        # --------------------------------------------------------
        # CANTIDADES CON $
        # --------------------------------------------------------

        for deteccion in detecciones:

            texto = str(
                deteccion.get("texto", "")
            ).strip()

            coincidencia = re.search(
                r"\$\s*[\d,]+\.\d{2}",
                texto
            )

            if coincidencia:
                return coincidencia.group(0)

        # --------------------------------------------------------
        # MONTO DEL PAGO
        # --------------------------------------------------------

        for i, deteccion in enumerate(detecciones):

            texto = str(
                deteccion.get("texto", "")
            ).strip()

            texto_lower = texto.lower()

            if "monto del pago" in texto_lower:

                for j in range(
                    i + 1,
                    min(i + 4, len(detecciones))
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if re.fullmatch(
                        r"[\d,]+\.\d{2}",
                        valor
                    ):
                        return valor

        # --------------------------------------------------------
        # VALOR ANTES DE MONTO
        # --------------------------------------------------------

        for i, deteccion in enumerate(detecciones):

            texto = str(
                deteccion.get("texto", "")
            ).strip()

            if texto.lower() == "monto":

                for j in range(
                    max(0, i - 3),
                    i
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if re.fullmatch(
                        r"[\d,]+\.\d{2}",
                        valor
                    ):
                        return valor

        return None

    # ============================================================
    # CUENTA ORIGEN
    # ============================================================

    def extraer_cuenta_origen(self, detecciones):

        # --------------------------------------------------------
        # CUENTA ORIGEN
        # --------------------------------------------------------

        for i, deteccion in enumerate(detecciones):

            texto = str(
                deteccion.get("texto", "")
            ).strip()

            texto_lower = texto.lower()

            if texto_lower == "cuenta origen":

                for j in range(
                    i + 1,
                    min(i + 6, len(detecciones))
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    valor_lower = valor.lower()

                    if (
                        "micuenta banamex" in valor_lower
                        or "priority" in valor_lower
                        or "switch banamex" in valor_lower
                    ):
                        return valor

                    if (
                        "cuenta destino" in valor_lower
                        or "datos de la operación" in valor_lower
                        or "datos de la operacion" in valor_lower
                    ):
                        break

                if i + 1 < len(detecciones):

                    valor = str(
                        detecciones[i + 1].get("texto", "")
                    ).strip()

                    if valor:
                        return valor

        # --------------------------------------------------------
        # BANCANET
        # --------------------------------------------------------

        for i, deteccion in enumerate(detecciones):

            texto = str(
                deteccion.get("texto", "")
            ).strip()

            texto_lower = texto.lower()

            if texto_lower == "cuenta de retiro:":

                for j in range(
                    i + 1,
                    min(i + 4, len(detecciones))
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    valor_lower = valor.lower()

                    if (
                        "micuenta banamex" in valor_lower
                        or "priority" in valor_lower
                        or "switch banamex" in valor_lower
                    ):

                        valor = re.sub(
                            r"\s+mxn$",
                            "",
                            valor,
                            flags=re.IGNORECASE
                        )

                        return valor

                for j in range(
                    max(0, i - 4),
                    i
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    valor_lower = valor.lower()

                    if (
                        "micuenta banamex" in valor_lower
                        or "priority" in valor_lower
                        or "switch banamex" in valor_lower
                    ):

                        valor = re.sub(
                            r"\s+mxn$",
                            "",
                            valor,
                            flags=re.IGNORECASE
                        )

                        return valor

        # --------------------------------------------------------
        # CEP / BANXICO
        # --------------------------------------------------------

        for i, deteccion in enumerate(detecciones):

            texto = str(
                deteccion.get("texto", "")
            ).strip()

            texto_lower = texto.lower()

            if (
                texto_lower
                == "institución emisora del pago"
            ):

                for j in range(
                    i + 1,
                    min(i + 4, len(detecciones))
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if valor.lower() in (
                        "banamex",
                        "hsbc",
                    ):
                        return valor

                for j in range(
                    max(0, i - 4),
                    i
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if valor.lower() in (
                        "banamex",
                        "hsbc",
                    ):
                        return valor

        return None

    # ============================================================
    # CUENTA DESTINO
    # ============================================================

    def extraer_cuenta_destino(self, detecciones):

        # --------------------------------------------------------
        # TRANSFERENCIA NORMAL
        # --------------------------------------------------------

        for i, deteccion in enumerate(detecciones):

            texto = str(
                deteccion.get("texto", "")
            ).strip()

            texto_lower = texto.lower()

            if texto_lower == "cuenta destino":

                for j in range(
                    i + 1,
                    min(i + 6, len(detecciones))
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    valor_lower = valor.lower()

                    if not valor:
                        continue

                    if (
                        "datos de la operación" in valor_lower
                        or "datos de la operacion" in valor_lower
                        or "cuenta destino" in valor_lower
                        or "cuenta origen" in valor_lower
                    ):
                        continue

                    if "hsbc" in valor_lower:
                        return valor

        # --------------------------------------------------------
        # BANCANET
        # --------------------------------------------------------

        for i, deteccion in enumerate(detecciones):

            texto = str(
                deteccion.get("texto", "")
            ).strip()

            if texto.lower() == "cuenta de depósito:":

                # ------------------------------------------------
                # PRIMERO BUSCAR HACIA ADELANTE
                #
                # image_409:
                #
                # Cuenta de depósito:
                # Internet Morelos-HSBC-CLABE-311-
                # IPTVTEL COMUNICACIONES S DE RL
                # (Dato no verificado por esta
                # DE CV
                # institución)
                #
                # Debemos obtener:
                #
                # IPTVTEL COMUNICACIONES S DE RL DE CV
                #
                # El texto de advertencia se ignora, pero NO
                # detiene la búsqueda.
                # ------------------------------------------------

                partes = []

                for j in range(
                    i + 1,
                    min(i + 8, len(detecciones))
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    valor_lower = valor.lower()

                    if not valor:
                        continue

                    if (
                        valor_lower
                        in (
                            "cuenta de depósito:",
                            "cuenta de deposito:",
                        )
                    ):
                        break

                    # Ignorar solamente el aviso OCR.
                    if "dato no verificado" in valor_lower:
                        continue

                    if valor_lower == "institución":
                        continue

                    if valor_lower == "institucion":
                        continue

                    partes.append(valor)

                    texto_completo = " ".join(partes)
                    texto_completo_lower = texto_completo.lower()

                    # En cuanto ya tenemos "DE CV", tenemos completa
                    # la cuenta destino.
                    if (
                        "iptvtel" in texto_completo_lower
                        and re.search(
                            r"\bde\s+cv\b",
                            texto_completo_lower
                        )
                    ):

                        posicion = texto_completo_lower.find(
                            "iptvtel"
                        )

                        return texto_completo[
                            posicion:
                        ]

                # ------------------------------------------------
                # SI NO SE COMPLETÓ HACIA ADELANTE,
                # BUSCAR HACIA ATRÁS
                # ------------------------------------------------

                for j in range(
                    max(0, i - 4),
                    i
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    valor_lower = valor.lower()

                    if not valor:
                        continue

                    if valor_lower == "clabe asociada:":
                        continue

                    if "micuenta banamex" in valor_lower:
                        continue

                    if "iptvtel" in valor_lower:
                        return valor

                    if "hsbc" in valor_lower:
                        return valor

                # ------------------------------------------------
                # ÚLTIMO RECURSO HACIA ADELANTE
                # ------------------------------------------------

                if partes:

                    texto_completo = " ".join(partes)

                    texto_lower = texto_completo.lower()

                    if "iptvtel" in texto_lower:

                        posicion = texto_lower.find(
                            "iptvtel"
                        )

                        return texto_completo[
                            posicion:
                        ]

                    if "hsbc" in texto_lower:

                        posicion = texto_lower.find(
                            "hsbc"
                        )

                        return texto_completo[
                            posicion:
                        ]

        # --------------------------------------------------------
        # CEP / BANXICO
        # --------------------------------------------------------

        for i, deteccion in enumerate(detecciones):

            texto = str(
                deteccion.get("texto", "")
            ).strip()

            texto_lower = texto.lower()

            if (
                texto_lower
                == "institución receptora del pago"
            ):

                for j in range(
                    i + 1,
                    min(i + 4, len(detecciones))
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if valor.lower() in (
                        "banamex",
                        "hsbc",
                    ):
                        return valor

                for j in range(
                    max(0, i - 4),
                    i
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if valor.lower() in (
                        "banamex",
                        "hsbc",
                    ):
                        return valor

        return None

    # ============================================================
    # BENEFICIARIO
    # ============================================================

    def extraer_beneficiario(self, detecciones):

        # --------------------------------------------------------
        # CEP
        # --------------------------------------------------------

        for i, deteccion in enumerate(detecciones):

            texto = str(
                deteccion.get("texto", "")
            ).strip()

            texto_lower = texto.lower()

            if "cuenta beneficiaria" in texto_lower:

                for j in range(
                    i + 1,
                    min(i + 5, len(detecciones))
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if valor:

                        valor = valor.rstrip("*").strip()

                        return valor

        # --------------------------------------------------------
        # SPEI
        # --------------------------------------------------------

        for i, deteccion in enumerate(detecciones):

            texto = str(
                deteccion.get("texto", "")
            ).strip()

            if texto.lower() == "beneficiario":

                partes = []

                for j in range(
                    i + 1,
                    min(i + 15, len(detecciones))
                ):

                    actual = detecciones[j]

                    valor = str(
                        actual.get("texto", "")
                    ).strip()

                    if not valor:
                        continue

                    x = float(
                        actual.get("x", 0)
                    )

                    valor_lower = valor.lower()

                    if x < 550:
                        continue

                    if valor_lower == "hsbc":
                        continue

                    if (
                        "institución receptora" in valor_lower
                        or "institucion receptora" in valor_lower
                        or "institución emisora" in valor_lower
                        or "institucion emisora" in valor_lower
                        or "titular de la cuenta" in valor_lower
                    ):
                        continue

                    if "rfc/curp" in valor_lower:
                        break

                    if (
                        "clabe" in valor_lower
                        or "tarjeta de débito" in valor_lower
                        or "tarjeta de debito" in valor_lower
                    ):
                        break

                    partes.append(valor)

                if partes:
                    return " ".join(partes)

        return None

    # ============================================================
    # CLAVE DE RASTREO
    # ============================================================

    def extraer_clave(self, detecciones):

        for i, deteccion in enumerate(detecciones):

            texto = str(
                deteccion.get("texto", "")
            ).strip()

            texto_lower = texto.lower()

            if "clave de rastreo" in texto_lower:

                for j in range(
                    i + 1,
                    min(i + 5, len(detecciones))
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if re.fullmatch(
                        r"\d{15,20}",
                        valor
                    ):
                        return valor

                for j in range(
                    max(0, i - 3),
                    i
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if re.fullmatch(
                        r"\d{15,20}",
                        valor
                    ):
                        return valor

        return None

    # ============================================================
    # CONCEPTO
    # ============================================================

    def extraer_concepto(self, detecciones):

        etiquetas_concepto = [
            "concepto del pago",
            "concepto de pago:",
            "concepto:",
            "concepto",
        ]

        etiquetas_excluidas = [
            "tipo de beneficiario",
            "tipo de cuenta",
            "datos de la transferencia",
            "datos de la operación",
            "datos de la operacion",
            "clave de rastreo",
            "referencia numérica",
            "referencia numerica",
            "fecha y hora",
            "fecha",
            "fecha:",
            "hora",
            "hora:",
        ]

        def valor_concepto_valido(valor):

            if not valor:
                return False

            valor = valor.strip()

            if not valor:
                return False

            valor_lower = valor.lower()

            if re.fullmatch(
                r"\d+",
                valor
            ):
                return False

            if valor_lower in etiquetas_excluidas:
                return False

            if (
                "clave de rastreo" in valor_lower
                or "referencia numérica" in valor_lower
                or "referencia numerica" in valor_lower
                or valor_lower == "fecha y hora"
                or valor_lower == "fecha"
                or valor_lower == "hora"
            ):
                return False

            if re.fullmatch(
                r"\d{1,2}\s+[A-Za-záéíóúÁÉÍÓÚ]+\s+\d{4}(?:\s+\d{1,2}:\d{2}(?::\d{2})?\s*h?)?",
                valor
            ):
                return False

            if re.fullmatch(
                r"\d{1,2}/\d{1,2}/\d{4}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?",
                valor
            ):
                return False

            if re.fullmatch(
                r"\d{1,2}-\d{1,2}-\d{4}",
                valor
            ):
                return False

            return True

        for i, deteccion in enumerate(detecciones):

            texto = str(
                deteccion.get("texto", "")
            ).strip()

            texto_lower = texto.lower()

            es_concepto = False

            for etiqueta in etiquetas_concepto:

                if texto_lower == etiqueta:
                    es_concepto = True
                    break

                if (
                    etiqueta != "concepto"
                    and etiqueta in texto_lower
                ):
                    es_concepto = True
                    break

            if not es_concepto:
                continue

            # ====================================================
            # BANCANET
            #
            # image_409:
            #
            # Concepto de pago:
            # Pago Internet Junio 2026 Cliente
            # 01699
            #
            # Resultado:
            # Pago Internet Junio 2026 Cliente 01699
            # ====================================================

            if (
                "concepto de pago" in texto_lower
                or texto_lower == "concepto del pago"
            ):

                partes = []

                for j in range(
                    i + 1,
                    min(i + 8, len(detecciones))
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    valor_lower = valor.lower()

                    if not valor:
                        continue

                    # Ya llegamos al siguiente campo.
                    if (
                        valor_lower in (
                            "referencia numérica",
                            "referencia numerica",
                            "fecha",
                            "fecha:",
                            "hora",
                            "hora:",
                            "fecha y hora",
                            "fecha y hora:",
                        )
                        or "referencia numérica" in valor_lower
                        or "referencia numerica" in valor_lower
                    ):
                        break

                    if valor_concepto_valido(valor):
                        partes.append(valor)

                if partes:
                    return " ".join(partes)

            # ====================================================
            # 1. BUSCAR INMEDIATAMENTE DESPUÉS
            # ====================================================

            if i + 1 < len(detecciones):

                valor_siguiente = str(
                    detecciones[i + 1].get("texto", "")
                ).strip()

                if valor_concepto_valido(
                    valor_siguiente
                ):
                    return valor_siguiente

            # ====================================================
            # 2. BUSCAR ANTES
            # ====================================================

            if i > 0:

                valor_anterior = str(
                    detecciones[i - 1].get("texto", "")
                ).strip()

                if valor_concepto_valido(
                    valor_anterior
                ):
                    return valor_anterior

            # ====================================================
            # 3. BUSCAR HACIA ADELANTE
            # ====================================================

            for j in range(
                i + 2,
                min(i + 8, len(detecciones))
            ):

                valor = str(
                    detecciones[j].get("texto", "")
                ).strip()

                if valor_concepto_valido(
                    valor
                ):
                    return valor

        return None

    # ============================================================
    # REFERENCIA
    # ============================================================

    def extraer_referencia(self, detecciones):

        # --------------------------------------------------------
        # REFERENCIA NUMÉRICA
        # --------------------------------------------------------

        for i, deteccion in enumerate(detecciones):

            texto = str(
                deteccion.get("texto", "")
            ).strip()

            texto_lower = texto.lower()

            if (
                "referencia numérica" in texto_lower
                or "referencia numerica" in texto_lower
            ):

                # Primero buscar hacia atrás
                for j in range(
                    max(0, i - 4),
                    i
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if re.fullmatch(
                        r"\d+",
                        valor
                    ):
                        return valor

                # Después buscar hacia adelante
                for j in range(
                    i + 1,
                    min(i + 5, len(detecciones))
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if re.fullmatch(
                        r"\d+",
                        valor
                    ):
                        return valor

        # --------------------------------------------------------
        # NÚMERO DE REFERENCIA
        # CEP / BANXICO
        # --------------------------------------------------------

        for i, deteccion in enumerate(detecciones):

            texto = str(
                deteccion.get("texto", "")
            ).strip()

            texto_lower = texto.lower()

            if (
                texto_lower == "número de referencia"
                or texto_lower == "numero de referencia"
            ):

                # Primero buscar hacia atrás
                for j in range(
                    max(0, i - 3),
                    i
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if re.fullmatch(
                        r"\d+",
                        valor
                    ):
                        return valor

                # Después buscar hacia adelante
                for j in range(
                    i + 1,
                    min(i + 4, len(detecciones))
                ):

                    valor = str(
                        detecciones[j].get("texto", "")
                    ).strip()

                    if re.fullmatch(
                        r"\d+",
                        valor
                    ):
                        return valor

        return None

    # ============================================================
    # EXTRAER TODO
    # ============================================================

    def extraer(self, datos):

        detecciones = self._obtener_detecciones(
            datos
        )

        return {
            "banco": self.extraer_banco(
                detecciones
            ),

            "campos": {

                "fecha": self.extraer_fecha(
                    detecciones
                ),

                "monto": self.extraer_monto(
                    detecciones
                ),

                "cuenta_origen": self.extraer_cuenta_origen(
                    detecciones
                ),

                "cuenta_destino": self.extraer_cuenta_destino(
                    detecciones
                ),

                "beneficiario": self.extraer_beneficiario(
                    detecciones
                ),

                "clave_rastreo": self.extraer_clave(
                    detecciones
                ),

                "concepto": self.extraer_concepto(
                    detecciones
                ),

                "referencia": self.extraer_referencia(
                    detecciones
                ),
            }
        }