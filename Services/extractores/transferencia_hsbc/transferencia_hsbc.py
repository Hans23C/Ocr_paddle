import re


class TransferenciaHSBCExtractor:

    def __init__(self):
        self.nombre_banco = "TRANSFERENCIA_HSBC"

    # ============================================================
    # UTILIDADES
    # ============================================================

    def _texto(self, deteccion):
        return str(
            deteccion.get("texto", "")
        ).strip()

    def _confianza(self, deteccion):
        try:
            return float(
                deteccion.get("confianza", 0.0)
            )
        except (TypeError, ValueError):
            return 0.0

    def _resultado(
        self,
        valor,
        metodo,
        confianza
    ):
        if valor is None:
            return {
                "valor": None,
                "metodo": metodo,
                "confianza": 0.0
            }

        valor = str(valor).strip()

        if not valor:
            return {
                "valor": None,
                "metodo": metodo,
                "confianza": 0.0
            }

        return {
            "valor": valor,
            "metodo": metodo,
            "confianza": round(
                float(confianza),
                4
            )
        }

    def _promedio_confianza(
        self,
        detecciones
    ):
        if not detecciones:
            return 0.0

        return sum(
            self._confianza(d)
            for d in detecciones
        ) / len(detecciones)

    # ============================================================
    # TIPO DE OPERACIÓN
    # ============================================================

    def _extraer_tipo_operacion(
        self,
        detecciones
    ):

        for i, d in enumerate(detecciones):

            texto = self._texto(d)

            if (
                texto.lower()
                == "transferencia a tercero hsbc"
            ):
                return self._resultado(
                    texto,
                    "deteccion_directa",
                    self._confianza(d)
                )

            if (
                texto.lower()
                == "transferencia a tercero"
            ):

                for siguiente in detecciones[
                    i + 1:i + 4
                ]:

                    texto_siguiente = (
                        self._texto(siguiente)
                    )

                    if (
                        texto_siguiente.upper()
                        == "HSBC"
                    ):

                        confianza = (
                            self._promedio_confianza(
                                [
                                    d,
                                    siguiente
                                ]
                            )
                        )

                        return self._resultado(
                            "Transferencia a tercero HSBC",
                            "detecciones_consecutivas",
                            confianza
                        )

        return self._resultado(
            None,
            "no_encontrado",
            0.0
        )

    # ============================================================
    # CUENTA ORIGEN
    # ============================================================

    def _extraer_cuenta_origen(
        self,
        detecciones
    ):

        indice_cuenta = None
        indice_origen = None

        for i, d in enumerate(detecciones):

            texto = self._texto(d).lower()

            if texto == "cuenta origen":

                indice_cuenta = i
                indice_origen = i
                break

            if texto == "cuenta":

                for j in range(
                    i + 1,
                    min(
                        i + 4,
                        len(detecciones)
                    )
                ):

                    if (
                        self._texto(
                            detecciones[j]
                        ).lower()
                        == "origen"
                    ):

                        indice_cuenta = i
                        indice_origen = j
                        break

            if indice_origen is not None:
                break

        if indice_origen is None:
            return self._resultado(
                None,
                "etiqueta_cuenta_origen_no_encontrada",
                0.0
            )

        partes = []
        detecciones_usadas = []

        if indice_cuenta > 0:

            anterior = detecciones[
                indice_cuenta - 1
            ]

            texto_anterior = self._texto(
                anterior
            )

            if texto_anterior:

                texto_lower = (
                    texto_anterior.lower()
                )

                if (
                    texto_lower
                    not in {
                        "resumen",
                        "de operación",
                        "tipo de",
                        "operación",
                        "folio",
                        "monto",
                        "banco",
                        "banco receptor",
                        "receptor"
                    }
                    and
                    "transferencia a tercero"
                    not in texto_lower
                ):

                    partes.append(
                        texto_anterior
                    )

                    detecciones_usadas.append(
                        anterior
                    )

        for i in range(
            indice_origen + 1,
            len(detecciones)
        ):

            texto = self._texto(
                detecciones[i]
            )

            if not texto:
                continue

            texto_lower = texto.lower()

            if (
                texto_lower
                in {
                    "cuenta",
                    "destino",
                    "banco",
                    "receptor",
                    "banco receptor",
                    "monto",
                    "fecha",
                    "fecha de",
                    "fecha de operación",
                    "folio"
                }
            ):
                break

            if (
                "cuenta destino"
                in texto_lower
            ):
                break

            partes.append(texto)
            detecciones_usadas.append(
                detecciones[i]
            )

            if re.search(
                r"\d{3,4}",
                texto
            ):
                break

        if not partes:
            return self._resultado(
                None,
                "valor_cuenta_origen_no_encontrado",
                0.0
            )

        valor = " ".join(partes)

        confianza = (
            self._promedio_confianza(
                detecciones_usadas
            )
        )

        return self._resultado(
            valor,
            "detecciones_alrededor_cuenta_origen",
            confianza
        )

    # ============================================================
    # CUENTA DESTINO
    # ============================================================

    def _extraer_cuenta_destino(
        self,
        detecciones
    ):

        indice_cuenta = None
        indice_destino = None

        for i, d in enumerate(detecciones):

            texto = self._texto(d).lower()

            if texto == "cuenta destino":

                indice_cuenta = i
                indice_destino = i
                break

            if texto == "cuenta":

                for j in range(
                    i + 1,
                    min(
                        i + 4,
                        len(detecciones)
                    )
                ):

                    if (
                        self._texto(
                            detecciones[j]
                        ).lower()
                        == "destino"
                    ):

                        indice_cuenta = i
                        indice_destino = j
                        break

            if indice_destino is not None:
                break

        if indice_destino is None:
            return self._resultado(
                None,
                "etiqueta_cuenta_destino_no_encontrada",
                0.0
            )

        partes = []
        detecciones_usadas = []

        # ========================================================
        # image_293
        #
        # Cuenta
        # Transferencia Express
        # destino
        # Otra cuenta HSBC: *******131
        # ========================================================

        if indice_cuenta != indice_destino:

            textos_entre = []
            detecciones_entre = []

            for i in range(
                indice_cuenta + 1,
                indice_destino
            ):

                texto = self._texto(
                    detecciones[i]
                )

                if not texto:
                    continue

                textos_entre.append(
                    texto
                )

                detecciones_entre.append(
                    detecciones[i]
                )

            es_transferencia_express = any(
                "transferencia express"
                in texto.lower()
                for texto in textos_entre
            )

            if es_transferencia_express:

                for texto, deteccion in zip(
                    textos_entre,
                    detecciones_entre
                ):

                    partes.append(
                        texto
                    )

                    detecciones_usadas.append(
                        deteccion
                    )

            # ====================================================
            # image_521
            #
            # IPTVTEL COMUNICACIONES S
            # Cuenta
            # DE RL DE CV
            # destino
            # ====================================================

            else:

                if indice_cuenta > 0:

                    anterior = detecciones[
                        indice_cuenta - 1
                    ]

                    texto_anterior = self._texto(
                        anterior
                    )

                    if texto_anterior:

                        texto_lower = (
                            texto_anterior.lower()
                        )

                        if (
                            texto_lower
                            not in {
                                "resumen",
                                "de operación",
                                "tipo de",
                                "operación",
                                "folio",
                                "monto",
                                "banco",
                                "banco receptor",
                                "receptor"
                            }
                            and
                            "transferencia a tercero"
                            not in texto_lower
                        ):

                            partes.append(
                                texto_anterior
                            )

                            detecciones_usadas.append(
                                anterior
                            )

                for texto, deteccion in zip(
                    textos_entre,
                    detecciones_entre
                ):

                    partes.append(
                        texto
                    )

                    detecciones_usadas.append(
                        deteccion
                    )

        # ========================================================
        # image_301
        #
        # IPTVTEL COMUNIONES SD
        # Cuenta destino
        # RL DE CV
        # Cuenta HSBC * 9131
        # ========================================================

        else:

            if indice_cuenta > 0:

                anterior = detecciones[
                    indice_cuenta - 1
                ]

                texto_anterior = self._texto(
                    anterior
                )

                if texto_anterior:

                    texto_lower = (
                        texto_anterior.lower()
                    )

                    if (
                        texto_lower
                        not in {
                            "resumen",
                            "de operación",
                            "tipo de",
                            "operación",
                            "folio",
                            "monto",
                            "banco",
                            "banco receptor",
                            "receptor"
                        }
                        and
                        "transferencia a tercero"
                        not in texto_lower
                    ):

                        partes.append(
                            texto_anterior
                        )

                        detecciones_usadas.append(
                            anterior
                        )

        # ========================================================
        # INFORMACIÓN DESPUÉS DE DESTINO
        # ========================================================

        for i in range(
            indice_destino + 1,
            len(detecciones)
        ):

            texto = self._texto(
                detecciones[i]
            )

            if not texto:
                continue

            texto_lower = texto.lower()

            if (
                texto_lower
                in {
                    "banco",
                    "receptor",
                    "banco receptor",
                    "monto",
                    "fecha",
                    "fecha de",
                    "fecha de operación",
                    "folio"
                }
            ):
                break

            if (
                texto.upper() == "HSBC"
                and i + 1 < len(detecciones)
            ):

                siguiente = self._texto(
                    detecciones[i + 1]
                ).lower()

                if siguiente == "banco receptor":
                    break

            if (
                texto_lower
                == "operación"
            ):
                break

            partes.append(texto)

            detecciones_usadas.append(
                detecciones[i]
            )

        if not partes:
            return self._resultado(
                None,
                "valor_cuenta_destino_no_encontrado",
                0.0
            )

        valor = " ".join(partes)

        confianza = (
            self._promedio_confianza(
                detecciones_usadas
            )
        )

        return self._resultado(
            valor,
            "detecciones_alrededor_cuenta_destino",
            confianza
        )

    # ============================================================
    # BANCO RECEPTOR
    # ============================================================

    def _extraer_banco_receptor(
        self,
        detecciones
    ):

        for i, d in enumerate(detecciones):

            texto = self._texto(d)

            if texto.lower() == "banco":

                for siguiente in detecciones[
                    i + 1:i + 4
                ]:

                    texto_siguiente = (
                        self._texto(siguiente)
                    )

                    if (
                        texto_siguiente.upper()
                        == "HSBC"
                    ):

                        return self._resultado(
                            "HSBC",
                            "deteccion_despues_de_banco",
                            self._confianza(
                                siguiente
                            )
                        )

        for i, d in enumerate(detecciones):

            texto = self._texto(d)

            if texto.upper() != "HSBC":
                continue

            for siguiente in detecciones[
                i + 1:i + 4
            ]:

                if (
                    self._texto(
                        siguiente
                    ).lower()
                    == "banco receptor"
                ):

                    confianza = (
                        self._promedio_confianza(
                            [
                                d,
                                siguiente
                            ]
                        )
                    )

                    return self._resultado(
                        "HSBC",
                        "deteccion_antes_de_banco_receptor",
                        confianza
                    )

        return self._resultado(
            None,
            "banco_receptor_no_encontrado",
            0.0
        )

    # ============================================================
    # MONTO
    # ============================================================

    def _extraer_monto(
        self,
        detecciones
    ):

        patron = re.compile(
            r"^\d+(?:,\d{3})*"
            r"(?:\.\d{2})?"
            r"\s*MXN$",
            re.IGNORECASE
        )

        for d in detecciones:

            texto = self._texto(d)

            if patron.fullmatch(texto):

                return self._resultado(
                    texto,
                    "deteccion_directa_monto",
                    self._confianza(d)
                )

        return self._resultado(
            None,
            "monto_no_encontrado",
            0.0
        )

    # ============================================================
    # FECHA DE OPERACIÓN
    # ============================================================

    def _extraer_fecha(
        self,
        detecciones
    ):

        patron = re.compile(
            r"\b\d{1,2}\s+"
            r"(?:ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)"
            r"\s+\d{4},\s+"
            r"\d{1,2}:\d{2}"
            r"(?::\d{2})?"
            r"(?:\s+[ap]\.\s*m\.)?",
            re.IGNORECASE
        )

        # ========================================================
        # CASO ESPECIAL:
        #
        # 06 jul 2026, 12:31 p.
        # m.
        #
        # Se revisa ANTES de devolver la fecha normal.
        # ========================================================

        for i, d in enumerate(detecciones):

            texto = self._texto(d)

            coincidencia = patron.search(
                texto
            )

            if not coincidencia:
                continue

            fecha = coincidencia.group(
                0
            ).strip()

            # La fecha termina en "p."
            if texto.lower().endswith(" p."):

                if i + 1 < len(detecciones):

                    siguiente = self._texto(
                        detecciones[i + 1]
                    )

                    if siguiente.lower() == "m.":

                        fecha = (
                            fecha[:-2].rstrip()
                            + " p. m."
                        )

                        confianza = (
                            self._promedio_confianza(
                                [
                                    d,
                                    detecciones[i + 1]
                                ]
                            )
                        )

                        return self._resultado(
                            fecha,
                            "detecciones_fecha_separada",
                            confianza
                        )

            # La fecha termina en "a."
            if texto.lower().endswith(" a."):

                if i + 1 < len(detecciones):

                    siguiente = self._texto(
                        detecciones[i + 1]
                    )

                    if siguiente.lower() == "m.":

                        fecha = (
                            fecha[:-2].rstrip()
                            + " a. m."
                        )

                        confianza = (
                            self._promedio_confianza(
                                [
                                    d,
                                    detecciones[i + 1]
                                ]
                            )
                        )

                        return self._resultado(
                            fecha,
                            "detecciones_fecha_separada",
                            confianza
                        )

        # ========================================================
        # CASOS QUE YA FUNCIONABAN
        #
        # 02 jul 2026, 09:53:25
        # 06 jul 2026, 08:49 a. m.
        # etc.
        # ========================================================

        for d in detecciones:

            texto = self._texto(d)

            coincidencia = patron.search(
                texto
            )

            if coincidencia:

                fecha = coincidencia.group(
                    0
                ).strip()

                return self._resultado(
                    fecha,
                    "deteccion_directa_fecha",
                    self._confianza(d)
                )

        # ========================================================
        # FECHA DE OPERACIÓN
        # ========================================================

        for i, d in enumerate(detecciones):

            texto = self._texto(d).lower()

            if (
                texto == "fecha de"
                or texto == "fecha de operación"
            ):

                partes = []
                usadas = []

                for siguiente in detecciones[
                    i + 1:
                ]:

                    texto_siguiente = (
                        self._texto(siguiente)
                    )

                    if not texto_siguiente:
                        continue

                    if (
                        texto_siguiente.lower()
                        == "operación"
                    ):
                        continue

                    if (
                        texto_siguiente.lower()
                        == "folio"
                    ):
                        break

                    partes.append(
                        texto_siguiente
                    )

                    usadas.append(
                        siguiente
                    )

                    combinado = " ".join(
                        partes
                    )

                    coincidencia = (
                        patron.search(
                            combinado
                        )
                    )

                    if coincidencia:

                        fecha = (
                            coincidencia.group(
                                0
                            ).strip()
                        )

                        return self._resultado(
                            fecha,
                            "detecciones_fecha_operacion",
                            self._promedio_confianza(
                                usadas
                            )
                        )

        return self._resultado(
            None,
            "fecha_operacion_no_encontrada",
            0.0
        )

    # ============================================================
    # FOLIO
    # ============================================================

    def _extraer_folio(
        self,
        detecciones
    ):

        patron = re.compile(
            r"^\d{4,8}$"
        )

        for i, d in enumerate(detecciones):

            texto = self._texto(d)

            # ----------------------------------------------------
            # Folio
            # 52846
            # ----------------------------------------------------

            if texto.lower() == "folio":

                for siguiente in detecciones[
                    i + 1:i + 4
                ]:

                    valor = self._texto(
                        siguiente
                    )

                    if patron.fullmatch(
                        valor
                    ):

                        return self._resultado(
                            valor,
                            "deteccion_despues_de_folio",
                            self._confianza(
                                siguiente
                            )
                        )

            # ----------------------------------------------------
            # 97605
            # Folio
            # ----------------------------------------------------

            if patron.fullmatch(texto):

                for siguiente in detecciones[
                    i + 1:i + 4
                ]:

                    etiqueta = self._texto(
                        siguiente
                    )

                    if (
                        etiqueta.lower()
                        == "folio"
                    ):

                        confianza = (
                            self._promedio_confianza(
                                [
                                    d,
                                    siguiente
                                ]
                            )
                        )

                        return self._resultado(
                            texto,
                            "deteccion_antes_de_folio",
                            confianza
                        )

        return self._resultado(
            None,
            "folio_no_encontrado",
            0.0
        )

    # ============================================================
    # EXTRACCIÓN PRINCIPAL
    # ============================================================

    def extraer(
        self,
        datos
    ):

        detecciones = datos.get(
            "detecciones",
            []
        )

        tipo_operacion = (
            self._extraer_tipo_operacion(
                detecciones
            )
        )

        cuenta_origen = (
            self._extraer_cuenta_origen(
                detecciones
            )
        )

        cuenta_destino = (
            self._extraer_cuenta_destino(
                detecciones
            )
        )

        banco_receptor = (
            self._extraer_banco_receptor(
                detecciones
            )
        )

        monto = (
            self._extraer_monto(
                detecciones
            )
        )

        fecha_operacion = (
            self._extraer_fecha(
                detecciones
            )
        )

        folio = (
            self._extraer_folio(
                detecciones
            )
        )

        return {
            "banco": self.nombre_banco,
            "tipo": self.nombre_banco,
            "campos": {
                "tipo_operacion":
                    tipo_operacion,

                "cuenta_origen":
                    cuenta_origen,

                "cuenta_destino":
                    cuenta_destino,

                "banco_receptor":
                    banco_receptor,

                "monto":
                    monto,

                "fecha_operacion":
                    fecha_operacion,

                "folio":
                    folio
            }
        }


# ============================================================
# FACTORY
# ============================================================

def crear_extractor():
    return TransferenciaHSBCExtractor()