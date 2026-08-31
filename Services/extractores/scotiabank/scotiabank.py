import re


class ScotiabankExtractor:

    def __init__(self):
        pass

    # ========================================================
    # UTILIDADES
    # ========================================================

    def _crear_campo(
        self,
        valor,
        metodo,
        confianza=1.0
    ):
        if valor is None:
            return None

        valor = str(valor).strip()

        if not valor:
            return None

        return {
            "valor": valor,
            "metodo": metodo,
            "confianza": float(confianza)
        }

    def _obtener_detecciones(self, datos):
        return datos.get(
            "detecciones",
            []
        )

    # ========================================================
    # BUSCAR VALOR DESPUÉS DE ETIQUETA
    # ========================================================

    def _buscar_despues_de_etiqueta(
        self,
        detecciones,
        etiquetas,
        permitir_multilinea=False
    ):
        """
        Busca el valor que aparece después de una etiqueta.

        Si permitir_multilinea=True, permite unir varias
        detecciones consecutivas que pertenecen al mismo valor.

        Ejemplo:

        Cuenta Destino
        IPTVTEL COMUNICACIONES S DE RL DE C
        *1311

        Resultado:

        IPTVTEL COMUNICACIONES S DE RL DE C *1311
        """

        etiquetas_normalizadas = [
            e.lower().strip()
            for e in etiquetas
        ]

        for i, deteccion in enumerate(detecciones):

            texto = str(
                deteccion.get(
                    "texto",
                    ""
                )
            ).strip()

            texto_lower = texto.lower()

            for etiqueta in etiquetas_normalizadas:

                if texto_lower != etiqueta:
                    continue

                if i + 1 >= len(detecciones):
                    continue

                siguiente = detecciones[i + 1]

                valor = str(
                    siguiente.get(
                        "texto",
                        ""
                    )
                ).strip()

                if not valor:
                    continue

                confianza = float(
                    siguiente.get(
                        "confianza",
                        0
                    )
                )

                # ------------------------------------------------
                # VALOR MULTILÍNEA
                # ------------------------------------------------

                if permitir_multilinea:

                    partes = [
                        valor
                    ]

                    confianzas = [
                        confianza
                    ]

                    j = i + 2

                    while j < len(detecciones):

                        siguiente_texto = str(
                            detecciones[j].get(
                                "texto",
                                ""
                            )
                        ).strip()

                        if not siguiente_texto:
                            j += 1
                            continue

                        siguiente_lower = (
                            siguiente_texto.lower()
                        )

                        # ----------------------------------------
                        # NO UNIR OTRA ETIQUETA
                        # ----------------------------------------

                        etiquetas_bloqueo = [
                            "desde",
                            "cuenta destino",
                            "para",
                            "concepto",
                            "referencia",
                            "referencia numérica",
                            "folio"
                        ]

                        if siguiente_lower in etiquetas_bloqueo:
                            break

                        # ----------------------------------------
                        # NO UNIR TEXTOS DEL PIE DEL COMPROBANTE
                        # ----------------------------------------

                        if (
                            siguiente_texto.lower().startswith(
                                "tu comprobante"
                            )
                            or siguiente_texto.lower().startswith(
                                "de méxico"
                            )
                            or siguiente_texto.lower().startswith(
                                "en 45 días"
                            )
                        ):
                            break

                        partes.append(
                            siguiente_texto
                        )

                        confianzas.append(
                            float(
                                detecciones[j].get(
                                    "confianza",
                                    0
                                )
                            )
                        )

                        j += 1

                    valor = " ".join(
                        partes
                    )

                    confianza = min(
                        confianzas
                    )

                # ------------------------------------------------
                # RESULTADO
                # ------------------------------------------------

                return self._crear_campo(
                    valor=valor,
                    metodo=(
                        "etiqueta_"
                        + etiqueta.replace(
                            " ",
                            "_"
                        )
                    ),
                    confianza=confianza
                )

        return None

    # ========================================================
    # BANCO
    # ========================================================

    def _extraer_banco(
        self,
        detecciones
    ):

        for deteccion in detecciones:

            texto = str(
                deteccion.get(
                    "texto",
                    ""
                )
            ).strip()

            if texto.lower() == "scotiabank":

                return self._crear_campo(
                    valor="SCOTIABANK",
                    metodo="deteccion_banco",
                    confianza=float(
                        deteccion.get(
                            "confianza",
                            0
                        )
                    )
                )

        return self._crear_campo(
            valor="SCOTIABANK",
            metodo="metadato",
            confianza=1.0
        )

    # ========================================================
    # MONTO
    # ========================================================

    def _extraer_monto(
        self,
        detecciones
    ):

        patron = re.compile(
            r"""
            [-+]?
            \$?\s*
            \d+(?:,\d{3})*
            (?:\.\d{2})?
            """,
            re.VERBOSE
        )

        for deteccion in detecciones:

            texto = str(
                deteccion.get(
                    "texto",
                    ""
                )
            ).strip()

            if (
                "$" in texto
                and re.search(
                    r"\d",
                    texto
                )
            ):

                coincidencia = patron.search(
                    texto
                )

                if coincidencia:

                    return self._crear_campo(
                        valor=coincidencia.group(
                            0
                        ).strip(),
                        metodo="deteccion_monto",
                        confianza=float(
                            deteccion.get(
                                "confianza",
                                0
                            )
                        )
                    )

        return None

    # ========================================================
    # FECHA
    # ========================================================

    def _extraer_fecha(
        self,
        detecciones
    ):

        patron = re.compile(
            r"""
            \b
            \d{1,2}
            \s+
            (?:de\s+)?
            [A-Za-zÁÉÍÓÚáéíóú]+
            \s+
            (?:de\s+)?
            \d{2,4}
            (?:\s*,?\s*
                \d{1,2}:
                \d{2}:
                \d{2}
            )?
            (?:\s*h)?
            \b
            """,
            re.IGNORECASE |
            re.VERBOSE
        )

        for deteccion in detecciones:

            texto = str(
                deteccion.get(
                    "texto",
                    ""
                )
            ).strip()

            coincidencia = patron.search(
                texto
            )

            if coincidencia:

                return self._crear_campo(
                    valor=coincidencia.group(
                        0
                    ).strip(),
                    metodo="regex_fecha",
                    confianza=float(
                        deteccion.get(
                            "confianza",
                            0
                        )
                    )
                )

        return None

    # ========================================================
    # EXTRACCIÓN PRINCIPAL
    # ========================================================

    def extraer(
        self,
        datos
    ):

        detecciones = self._obtener_detecciones(
            datos
        )

        campos = {}

        # ----------------------------------------------------
        # BANCO
        # ----------------------------------------------------

        banco = self._extraer_banco(
            detecciones
        )

        if banco:
            campos["banco"] = banco

        # ----------------------------------------------------
        # MONTO
        # ----------------------------------------------------

        monto = self._extraer_monto(
            detecciones
        )

        if monto:
            campos["monto"] = monto

        # ----------------------------------------------------
        # FECHA
        # ----------------------------------------------------

        fecha = self._extraer_fecha(
            detecciones
        )

        if fecha:
            campos["fecha"] = fecha

        # ----------------------------------------------------
        # DESDE
        # ----------------------------------------------------

        desde = self._buscar_despues_de_etiqueta(
            detecciones,
            [
                "Desde"
            ],
            permitir_multilinea=False
        )

        if desde:
            campos["cuenta_ordenante"] = desde

        # ----------------------------------------------------
        # CUENTA DESTINO / PARA
        # ----------------------------------------------------

        destino = self._buscar_despues_de_etiqueta(
            detecciones,
            [
                "Cuenta Destino",
                "Para"
            ],
            permitir_multilinea=True
        )

        if destino:
            campos["cuenta_beneficiario"] = destino

        # ----------------------------------------------------
        # CONCEPTO
        # ----------------------------------------------------

        concepto = self._buscar_despues_de_etiqueta(
            detecciones,
            [
                "Concepto"
            ],
            permitir_multilinea=False
        )

        if concepto:
            campos["concepto"] = concepto

        # ----------------------------------------------------
        # REFERENCIA
        # ----------------------------------------------------

        referencia = self._buscar_despues_de_etiqueta(
            detecciones,
            [
                "Referencia",
                "Referencia numérica"
            ],
            permitir_multilinea=False
        )

        if referencia:
            campos["referencia"] = referencia

        # ----------------------------------------------------
        # FOLIO
        # ----------------------------------------------------

        folio = self._buscar_despues_de_etiqueta(
            detecciones,
            [
                "Folio"
            ],
            permitir_multilinea=False
        )

        if folio:
            campos["folio"] = folio

        # ----------------------------------------------------
        # RESULTADO
        # ----------------------------------------------------

        return {
            "banco": "SCOTIABANK",
            "tipo": "TRANSFERENCIA_SCOTIABANK",
            "campos": campos
        }