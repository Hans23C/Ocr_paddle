import re


class PlataExtractor:

    def __init__(self):
        pass

    # ============================================================
    # UTILIDADES
    # ============================================================

    def _detecciones(self, datos):
        return datos.get("detecciones", [])

    def _normalizar(self, texto):
        if not texto:
            return ""

        texto = str(texto).strip().lower()

        reemplazos = {
            "í": "i",
            "ó": "o",
            "é": "e",
            "á": "a",
            "ú": "u",
        }

        for origen, destino in reemplazos.items():
            texto = texto.replace(origen, destino)

        return texto

    def _campo(self, valor=None, metodo="N/A", confianza=0.0):
        return {
            "valor": valor,
            "metodo": metodo,
            "confianza": confianza
        }

    def _texto(self, deteccion):
        return str(
            deteccion.get("texto", "")
        ).strip()

    # ============================================================
    # BUSQUEDAS
    # ============================================================

    def _buscar_exacto(self, detecciones, texto):

        objetivo = self._normalizar(texto)

        for d in detecciones:

            if self._normalizar(
                self._texto(d)
            ) == objetivo:

                return d

        return None

    def _buscar_contiene(self, detecciones, texto):

        objetivo = self._normalizar(texto)

        for d in detecciones:

            if objetivo in self._normalizar(
                self._texto(d)
            ):

                return d

        return None

    def _valor_derecha(
        self,
        detecciones,
        etiqueta,
        excluir=None
    ):

        excluir = excluir or []

        etiqueta_norm = self._normalizar(
            etiqueta
        )

        etiqueta_det = None

        for d in detecciones:

            texto = self._normalizar(
                self._texto(d)
            )

            if texto == etiqueta_norm:

                etiqueta_det = d
                break

        if not etiqueta_det:
            return None

        x_label = float(
            etiqueta_det.get("x", 0)
        )

        y_label = float(
            etiqueta_det.get("y", 0)
        )

        h_label = float(
            etiqueta_det.get("h", 0)
        )

        mejor = None
        mejor_distancia = None

        for d in detecciones:

            texto = self._texto(d)

            if not texto:
                continue

            texto_norm = self._normalizar(
                texto
            )

            if texto_norm in excluir:
                continue

            if d is etiqueta_det:
                continue

            x = float(
                d.get("x", 0)
            )

            y = float(
                d.get("y", 0)
            )

            if x <= x_label:
                continue

            diferencia_y = abs(
                y - y_label
            )

            tolerancia_y = max(
                15,
                h_label * 1.5
            )

            if diferencia_y > tolerancia_y:
                continue

            distancia = x - x_label

            if (
                mejor is None
                or distancia < mejor_distancia
            ):

                mejor = d
                mejor_distancia = distancia

        return mejor

    def _buscar_por_y(
        self,
        detecciones,
        y_referencia,
        excluir_textos=None,
        margen=10
    ):

        excluir_textos = excluir_textos or []

        resultado = []

        for d in detecciones:

            texto = self._texto(d)

            if not texto:
                continue

            if self._normalizar(
                texto
            ) in excluir_textos:
                continue

            y = float(
                d.get("y", 0)
            )

            if abs(
                y - y_referencia
            ) <= margen:

                resultado.append(d)

        return resultado

    # ============================================================
    # BANCO
    # ============================================================

    def _extraer_banco(self, detecciones):

        d = self._buscar_exacto(
            detecciones,
            "PLATA"
        )

        if d:

            return self._campo(
                "PLATA",
                "OCR_DIRECTO",
                float(
                    d.get(
                        "confianza",
                        0
                    )
                )
            )

        return self._campo()

    # ============================================================
    # TIPO DE TRANSFERENCIA
    # ============================================================

    def _extraer_tipo_transferencia(
        self,
        detecciones
    ):

        for d in detecciones:

            texto = self._normalizar(
                self._texto(d)
            )

            if (
                "transferencia por spei"
                in texto
            ):

                return self._campo(
                    "TRANSFERENCIA_SPEI",
                    "OCR_DIRECTO",
                    float(
                        d.get(
                            "confianza",
                            0
                        )
                    )
                )

        return self._campo()

    # ============================================================
    # ESTATUS
    # ============================================================

    def _extraer_estatus(
        self,
        detecciones
    ):

        etiqueta = self._buscar_exacto(
            detecciones,
            "Estatus"
        )

        if etiqueta:

            x_label = float(
                etiqueta.get("x", 0)
            )

            y_label = float(
                etiqueta.get("y", 0)
            )

            candidatos = []

            for d in detecciones:

                if d is etiqueta:
                    continue

                texto = self._normalizar(
                    self._texto(d)
                )

                if texto not in (
                    "completa",
                    "en progreso",
                    "pendiente",
                    "cancelada",
                    "rechazada"
                ):
                    continue

                x = float(
                    d.get("x", 0)
                )

                y = float(
                    d.get("y", 0)
                )

                if (
                    x > x_label
                    and abs(
                        y - y_label
                    ) <= 15
                ):

                    candidatos.append(d)

            if candidatos:

                d = min(
                    candidatos,
                    key=lambda item:
                    float(
                        item.get("x", 0)
                    )
                )

                return self._campo(
                    self._texto(d),
                    "BBOX_DERECHA",
                    float(
                        d.get(
                            "confianza",
                            0
                        )
                    )
                )

        return self._campo()

    # ============================================================
    # MONTO
    # ============================================================

    def _extraer_monto(
        self,
        detecciones
    ):

        patron = re.compile(
            r"^\$?\s*[\d,]+(?:\.\d{2})?$"
        )

        for d in detecciones:

            texto = self._texto(d)

            if not patron.match(texto):
                continue

            if "." not in texto:
                continue

            valor_limpio = (
                texto
                .replace("$", "")
                .replace(",", "")
                .strip()
            )

            try:
                float(valor_limpio)
            except ValueError:
                continue

            return self._campo(
                texto,
                "REGEX",
                float(
                    d.get(
                        "confianza",
                        0
                    )
                )
            )

        return self._campo()

    # ============================================================
    # FECHA PRINCIPAL
    # ============================================================

    def _extraer_fecha(
        self,
        detecciones
    ):

        patron = re.compile(
            r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
            r"\s+\d{1,2},\s+\d{4}\s+"
            r"\d{1,2}:\d{2}\s+\(CST\)$",
            re.IGNORECASE
        )

        for d in detecciones:

            texto = self._texto(d)

            if patron.match(texto):

                return self._campo(
                    texto,
                    "REGEX",
                    float(
                        d.get(
                            "confianza",
                            0
                        )
                    )
                )

        return self._campo()

    # ============================================================
    # COMPLETADA EN
    # ============================================================

        # --------------------------------------------------------
        # FECHA
        # --------------------------------------------------------

        patron_fecha = re.compile(
            r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
            r"\s+\d{1,2},\s+\d{4}$",
            re.IGNORECASE
        )

        candidatos_fecha = []

        for d in detecciones:

            if d is etiqueta:
                continue

            texto = self._texto(d)

            if not patron_fecha.match(texto):
                continue

            x = float(
                d.get("x", 0)
            )

            y = float(
                d.get("y", 0)
            )

            if (
                x > x_label
                and abs(
                    y - y_label
                ) <= 15
            ):

                candidatos_fecha.append(d)

        if candidatos_fecha:

            fecha = min(
                candidatos_fecha,
                key=lambda d:
                float(
                    d.get("x", 0)
                )
            )

        # --------------------------------------------------------
        # HORA
        # --------------------------------------------------------

        if fecha:

            x_fecha = float(
                fecha.get("x", 0)
            )

            y_fecha = float(
                fecha.get("y", 0)
            )

            patron_hora = re.compile(
                r"^\d{1,2}:\d{2}\s+\(CST\)$",
                re.IGNORECASE
            )

            candidatos_hora = []

            for d in detecciones:

                texto = self._texto(d)

                if not patron_hora.match(texto):
                    continue

                x = float(
                    d.get("x", 0)
                )

                y = float(
                    d.get("y", 0)
                )

                if (
                    x >= x_fecha - 10
                    and y >= y_fecha
                    and y - y_fecha <= 25
                ):

                    candidatos_hora.append(d)

            if candidatos_hora:

                hora = min(
                    candidatos_hora,
                    key=lambda d:
                    float(
                        d.get("y", 0)
                    )
                )

        # --------------------------------------------------------
        # RESULTADO
        # --------------------------------------------------------

        if fecha and hora:

            valor = (
                f"{self._texto(fecha)} "
                f"{self._texto(hora)}"
            )

            confianza = min(
                float(
                    fecha.get(
                        "confianza",
                        0
                    )
                ),
                float(
                    hora.get(
                        "confianza",
                        0
                    )
                )
            )

            return self._campo(
                valor,
                "BBOX_COMBINADO",
                confianza
            )

        if fecha:

            return self._campo(
                self._texto(fecha),
                "BBOX_DERECHA",
                float(
                    fecha.get(
                        "confianza",
                        0
                    )
                )
            )

        return self._campo()

    # ============================================================
    # NÚMERO DE RASTREO
    # ============================================================

    def _extraer_rastreo(
        self,
        detecciones
    ):

        etiqueta = self._buscar_exacto(
            detecciones,
            "No. de rastreo"
        )

        if not etiqueta:
            return self._campo()

        x_label = float(
            etiqueta.get("x", 0)
        )

        y_label = float(
            etiqueta.get("y", 0)
        )

        candidatos = []

        patron = re.compile(
            r"^\d{7}$"
        )

        for d in detecciones:

            if d is etiqueta:
                continue

            texto = self._texto(d)

            if not patron.match(texto):
                continue

            x = float(
                d.get("x", 0)
            )

            y = float(
                d.get("y", 0)
            )

            if (
                x > x_label
                and abs(
                    y - y_label
                ) <= 15
            ):

                candidatos.append(d)

        if candidatos:

            d = min(
                candidatos,
                key=lambda item:
                float(
                    item.get("x", 0)
                )
            )

            return self._campo(
                self._texto(d),
                "BBOX_DERECHA",
                float(
                    d.get(
                        "confianza",
                        0
                    )
                )
            )

        return self._campo()

    # ============================================================
    # FOLIO
    # ============================================================

    def _extraer_folio(
        self,
        detecciones
    ):

        etiqueta = self._buscar_exacto(
            detecciones,
            "Folio"
        )

        if not etiqueta:
            return self._campo()

        x_label = float(
            etiqueta.get("x", 0)
        )

        y_label = float(
            etiqueta.get("y", 0)
        )

        for d in detecciones:

            if d is etiqueta:
                continue

            x = float(
                d.get("x", 0)
            )

            y = float(
                d.get("y", 0)
            )

            texto = self._texto(d)

            if (
                x > x_label
                and abs(
                    y - y_label
                ) <= 15
                and re.match(
                    r"^[a-fA-F0-9]{8}$",
                    texto
                )
            ):

                return self._campo(
                    texto,
                    "BBOX_DERECHA",
                    float(
                        d.get(
                            "confianza",
                            0
                        )
                    )
                )

        return self._campo()

    # ============================================================
    # TIPO DE CUENTA
    # ============================================================

    def _extraer_tipo_cuenta(
        self,
        detecciones
    ):

        etiquetas = []

        for d in detecciones:

            texto = self._normalizar(
                self._texto(d)
            )

            if texto == "tipo de cuenta":

                etiquetas.append(d)

        if not etiquetas:
            return self._campo()

        # La primera corresponde a Cuenta de origen
        etiqueta = etiquetas[0]

        x_label = float(
            etiqueta.get("x", 0)
        )

        y_label = float(
            etiqueta.get("y", 0)
        )

        candidatos = []

        for d in detecciones:

            if d is etiqueta:
                continue

            texto = self._normalizar(
                self._texto(d)
            )

            if texto not in (
                "credito",
                "cuenta"
            ):
                continue

            x = float(
                d.get("x", 0)
            )

            y = float(
                d.get("y", 0)
            )

            if (
                x > x_label
                and abs(
                    y - y_label
                ) <= 15
            ):

                candidatos.append(d)

        if candidatos:

            d = min(
                candidatos,
                key=lambda item:
                float(
                    item.get("x", 0)
                )
            )

            valor = self._texto(d)

            if self._normalizar(
                valor
            ) == "credito":

                valor = "Credito"

            return self._campo(
                valor,
                "BBOX_DERECHA",
                float(
                    d.get(
                        "confianza",
                        0
                    )
                )
            )

        return self._campo()

    # ============================================================
    # TITULAR ORIGEN
    # ============================================================

    def _extraer_titular_origen(
        self,
        detecciones
    ):

        for d in detecciones:

            texto = self._normalizar(
                self._texto(d)
            )

            if texto != "titular":
                continue

            x_label = float(
                d.get("x", 0)
            )

            y_label = float(
                d.get("y", 0)
            )

            candidatos = []

            for valor in detecciones:

                if valor is d:
                    continue

                x = float(
                    valor.get("x", 0)
                )

                y = float(
                    valor.get("y", 0)
                )

                if (
                    x > x_label
                    and abs(
                        y - y_label
                    ) <= 15
                ):

                    texto_valor = self._texto(
                        valor
                    )

                    if texto_valor:

                        candidatos.append(
                            valor
                        )

            if candidatos:

                valor = min(
                    candidatos,
                    key=lambda item:
                    float(
                        item.get("x", 0)
                    )
                )

                return self._campo(
                    self._texto(valor),
                    "BBOX_DERECHA",
                    float(
                        valor.get(
                            "confianza",
                            0
                        )
                    )
                )

        return self._campo()

    # ============================================================
    # TITULAR BENEFICIARIO
    # ============================================================

    def _extraer_titular_beneficiario(
        self,
        detecciones
    ):

        etiqueta = self._buscar_exacto(
            detecciones,
            "Beneficiario"
        )

        if not etiqueta:
            return self._campo()

        y_beneficiario = float(
            etiqueta.get("y", 0)
        )

        candidatos = []

        for d in detecciones:

            y = float(
                d.get("y", 0)
            )

            if y <= y_beneficiario:
                continue

            texto = self._texto(d)

            texto_norm = self._normalizar(
                texto
            )

            if not texto:
                continue

            if texto_norm.startswith(
                "titular"
            ):

                candidatos.append(d)

        if not candidatos:
            return self._campo()

        titular = min(
            candidatos,
            key=lambda d:
            float(
                d.get("y", 0)
            )
        )

        texto = self._texto(
            titular
        )

        texto_norm = self._normalizar(
            texto
        )

        if texto_norm.startswith(
            "titular"
        ):

            valor = texto[
                len("Titular"):
            ].strip()

        else:
            valor = texto

        # --------------------------------------------------------
        # Continuación del titular
        # --------------------------------------------------------

        y_titular = float(
            titular.get("y", 0)
        )

        continuacion = None

        for d in detecciones:

            texto_cont = self._normalizar(
                self._texto(d)
            )

            y = float(
                d.get("y", 0)
            )

            if (
                texto_cont == "de c"
                and y > y_titular
                and y - y_titular <= 20
            ):

                continuacion = d
                break

        if continuacion:

            valor = (
                f"{valor} "
                f"{self._texto(continuacion)}"
            )

        return self._campo(
            valor,
            "BBOX_COMBINADO",
            float(
                titular.get(
                    "confianza",
                    0
                )
            )
        )

    # ============================================================
    # INSTITUCIÓN
    # ============================================================

    def _extraer_institucion(
        self,
        detecciones
    ):

        etiqueta = self._buscar_exacto(
            detecciones,
            "Institución"
        )

        if not etiqueta:
            return self._campo()

        x_label = float(
            etiqueta.get("x", 0)
        )

        y_label = float(
            etiqueta.get("y", 0)
        )

        for d in detecciones:

            if d is etiqueta:
                continue

            x = float(
                d.get("x", 0)
            )

            y = float(
                d.get("y", 0)
            )

            texto = self._texto(d)

            if (
                x > x_label
                and abs(
                    y - y_label
                ) <= 15
                and self._normalizar(
                    texto
                ) == "hsbc"
            ):

                return self._campo(
                    texto,
                    "BBOX_DERECHA",
                    float(
                        d.get(
                            "confianza",
                            0
                        )
                    )
                )

        return self._campo()

    # ============================================================
    # CLABE BENEFICIARIO
    # ============================================================

    def _extraer_clabe_beneficiario(
        self,
        detecciones
    ):

        # --------------------------------------------------------
        # CLABE mexicana:
        #
        # 18 dígitos
        #
        # En este OCR aparece:
        #
        # 021 453 0406 2409 1311
        #
        # 3 + 3 + 4 + 4 + 4 = 18
        # --------------------------------------------------------

        patron_clabe = re.compile(
            r"^\d{3}\s+\d{3}\s+\d{4}\s+\d{4}\s+\d{4}$"
        )

        # --------------------------------------------------------
        # Localizar Beneficiario
        # --------------------------------------------------------

        beneficiario = self._buscar_exacto(
            detecciones,
            "Beneficiario"
        )

        if not beneficiario:
            return self._campo()

        y_beneficiario = float(
            beneficiario.get("y", 0)
        )

        # --------------------------------------------------------
        # Buscar CLABEs después de Beneficiario
        # --------------------------------------------------------

        candidatos = []

        for d in detecciones:

            texto = self._texto(d)

            if not patron_clabe.match(texto):
                continue

            y = float(
                d.get("y", 0)
            )

            if y > y_beneficiario:

                candidatos.append(d)

        # --------------------------------------------------------
        # La primera CLABE después de Beneficiario
        # corresponde al beneficiario.
        # --------------------------------------------------------

        if candidatos:

            d = min(
                candidatos,
                key=lambda item:
                float(
                    item.get("y", 0)
                )
            )

            return self._campo(
                self._texto(d),
                "OCR_DIRECTO",
                float(
                    d.get(
                        "confianza",
                        0
                    )
                )
            )

        return self._campo()

    # ============================================================
    # REFERENCIA
    # ============================================================

    def _extraer_referencia(
        self,
        detecciones
    ):

        etiqueta = self._buscar_exacto(
            detecciones,
            "Referencia"
        )

        if not etiqueta:
            return self._campo()

        x_label = float(
            etiqueta.get("x", 0)
        )

        y_label = float(
            etiqueta.get("y", 0)
        )

        patron = re.compile(
            r"^\d+$"
        )

        candidatos = []

        for d in detecciones:

            if d is etiqueta:
                continue

            texto = self._texto(d)

            if not patron.match(texto):
                continue

            x = float(
                d.get("x", 0)
            )

            y = float(
                d.get("y", 0)
            )

            if (
                x > x_label
                and abs(
                    y - y_label
                ) <= 15
            ):

                candidatos.append(d)

        if candidatos:

            d = min(
                candidatos,
                key=lambda item:
                float(
                    item.get("x", 0)
                )
            )

            return self._campo(
                self._texto(d),
                "BBOX_DERECHA",
                float(
                    d.get(
                        "confianza",
                        0
                    )
                )
            )

        return self._campo()

    # ============================================================
    # CONCEPTO
    # ============================================================

    def _extraer_concepto(
        self,
        detecciones
    ):

        etiqueta = self._buscar_exacto(
            detecciones,
            "Concepto"
        )

        if not etiqueta:
            return self._campo()

        x_label = float(
            etiqueta.get("x", 0)
        )

        y_label = float(
            etiqueta.get("y", 0)
        )

        candidatos = []

        for d in detecciones:

            if d is etiqueta:
                continue

            x = float(
                d.get("x", 0)
            )

            y = float(
                d.get("y", 0)
            )

            texto = self._texto(d)

            if (
                x > x_label
                and abs(
                    y - y_label
                ) <= 15
                and texto
            ):

                candidatos.append(d)

        if candidatos:

            d = min(
                candidatos,
                key=lambda item:
                float(
                    item.get("x", 0)
                )
            )

            return self._campo(
                self._texto(d),
                "BBOX_DERECHA",
                float(
                    d.get(
                        "confianza",
                        0
                    )
                )
            )

        return self._campo()

    # ============================================================
    # MÉTODO PRINCIPAL
    # ============================================================

    def extraer(self, datos):

        detecciones = self._detecciones(
            datos
        )

        banco = self._extraer_banco(
            detecciones
        )

        tipo = self._extraer_tipo_transferencia(
            detecciones
        )

        estatus = self._extraer_estatus(
            detecciones
        )

        monto = self._extraer_monto(
            detecciones
        )

        fecha = self._extraer_fecha(
            detecciones
        )

        numero_rastreo = self._extraer_rastreo(
            detecciones
        )

        folio = self._extraer_folio(
            detecciones
        )

        tipo_cuenta = self._extraer_tipo_cuenta(
            detecciones
        )

        titular_origen = self._extraer_titular_origen(
            detecciones
        )

        titular_destino = self._extraer_titular_beneficiario(
            detecciones
        )

        institucion = self._extraer_institucion(
            detecciones
        )

        clabe = self._extraer_clabe_beneficiario(
            detecciones
        )

        referencia = self._extraer_referencia(
            detecciones
        )

        concepto = self._extraer_concepto(
            detecciones
        )

        return {
            "banco": banco,

            "tipo": tipo,

            "campos": {

                "estatus": estatus,

                "monto": monto,

                "fecha": fecha,

                "numero_rastreo": numero_rastreo,

                "folio": folio,

                "tipo_cuenta": tipo_cuenta,

                "titular_Origen": titular_origen,

                "titular_Destino": titular_destino,

                "institucion": institucion,

                "clabe": clabe,

                "referencia": referencia,

                "concepto": concepto
            }
        }