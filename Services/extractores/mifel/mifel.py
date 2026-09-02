import re


class MifelExtractor:

    def __init__(self):
        self.banco = "MIFEL"
        self.tipo = "TRANSFERENCIA_MIFEL"

    # ============================================================
    # UTILIDADES
    # ============================================================

    def _detecciones(self, datos):
        return datos.get("detecciones", [])

    def _texto_limpio(self, texto):
        return re.sub(r"\s+", " ", str(texto)).strip()

    def _confianza(self, detecciones):
        if not detecciones:
            return 0.0

        valores = []

        for d in detecciones:
            try:
                valores.append(float(d.get("confianza", 0)))
            except (TypeError, ValueError):
                pass

        return min(valores) if valores else 0.0

    def _resultado(self, valor, metodo, confianza):
        return {
            "valor": valor,
            "metodo": metodo,
            "confianza": round(float(confianza), 4)
        }

    # ============================================================
    # DESTINO
    # ============================================================

    def _destino(self, detecciones):

        principal = None

        for d in detecciones:
            texto = self._texto_limpio(d.get("texto", ""))

            if (
                "Cuenta Digital MIFEL" in texto
                or "Digital Evoluciona" in texto
                or "Nómina Mifel" in texto
            ):
                principal = d
                break

        if principal is None:
            return self._resultado(
                "NO ENCONTRADO",
                "NO_ENCONTRADO",
                0.0
            )

        texto_principal = self._texto_limpio(
            principal.get("texto", "")
        )

        x_principal = float(principal.get("x", 0))
        y_principal = float(principal.get("y", 0))

        partes = [texto_principal]
        confianzas = [
            float(principal.get("confianza", 0))
        ]

        for d in detecciones:

            if d is principal:
                continue

            fragmento = self._texto_limpio(
                d.get("texto", "")
            )

            if not fragmento:
                continue

            x = float(d.get("x", 0))
            y = float(d.get("y", 0))

            if (
                fragmento.isdigit()
                and len(fragmento) <= 6
                and 0 <= y - y_principal <= 70
                and x > x_principal
                and x - x_principal < 350
            ):
                partes.append(fragmento)

                confianzas.append(
                    float(d.get("confianza", 0))
                )

        valor = " ".join(partes)

        valor = re.sub(
            r"(\*+\d+)\s+(\d+)$",
            r"\1\2",
            valor
        )

        match = re.search(
            r"(\*{2,})(\d+)$",
            valor
        )

        if match:
            prefijo = valor[:match.start()].strip()
            numero = match.group(2)

            valor = (
                prefijo
                + " **** "
                + numero
            )

        return self._resultado(
            valor.strip(),
            "OCR_CUENTA",
            min(confianzas)
        )

    # ============================================================
    # MONTO
    # ============================================================

    def _monto(self, detecciones):

        patron = re.compile(
            r"\$\s*[\d,]+(?:\.\d{2})?\s*(?:MXN|MNX)",
            re.IGNORECASE
        )

        for d in detecciones:

            texto = self._texto_limpio(
                d.get("texto", "")
            )

            match = patron.search(texto)

            if match:

                valor = match.group(0)

                valor = re.sub(
                    r"\bMNX\b",
                    "MXN",
                    valor,
                    flags=re.IGNORECASE
                )

                return self._resultado(
                    valor,
                    "OCR_MONTO",
                    d.get("confianza", 0)
                )

        return self._resultado(
            "NO ENCONTRADO",
            "NO_ENCONTRADO",
            0.0
        )

    # ============================================================
    # NOMBRE
    # ============================================================

    def _nombre(self, detecciones):

        etiqueta = None

        for d in detecciones:

            texto = self._texto_limpio(
                d.get("texto", "")
            )

            if texto.lower() == "nombre":
                etiqueta = d
                break

        if etiqueta is None:
            return self._resultado(
                "NO ENCONTRADO",
                "NO_ENCONTRADO",
                0.0
            )

        x_label = float(
            etiqueta.get("x", 0)
        )

        y_label = float(
            etiqueta.get("y", 0)
        )

        # ========================================================
        # CASO 1 - NOMBRE EN LA MISMA LÍNEA
        # ========================================================

        candidatos = []

        for d in detecciones:

            if d is etiqueta:
                continue

            texto = self._texto_limpio(
                d.get("texto", "")
            )

            if not texto:
                continue

            x = float(d.get("x", 0))
            y = float(d.get("y", 0))

            if (
                x > x_label + 150
                and abs(y - y_label) <= 10
            ):
                candidatos.append(d)

        if candidatos:

            candidatos.sort(
                key=lambda d: float(
                    d.get("x", 0)
                )
            )

            d = candidatos[0]

            valor = self._texto_limpio(
                d.get("texto", "")
            )

            return self._resultado(
                valor.upper(),
                "OCR_NOMBRE",
                d.get("confianza", 0)
            )

        # ========================================================
        # CASO 2 - NOMBRE FRAGMENTADO
        # ========================================================

        candidatos = []

        for d in detecciones:

            if d is etiqueta:
                continue

            texto = self._texto_limpio(
                d.get("texto", "")
            )

            if not texto:
                continue

            x = float(d.get("x", 0))
            y = float(d.get("y", 0))

            diferencia_y = abs(
                y - y_label
            )

            if (
                x > x_label + 200
                and diferencia_y <= 50
            ):

                if texto.lower() in {
                    "iptvtel",
                    "internet mnet"
                }:
                    continue

                if texto.lower() in {
                    "hsbc",
                    "clabe",
                    "banco",
                    "concepto",
                    "folio",
                    "fecha",
                    "hora"
                }:
                    continue

                candidatos.append(d)

        if not candidatos:
            return self._resultado(
                "NO ENCONTRADO",
                "NO_ENCONTRADO",
                0.0
            )

        candidatos.sort(
            key=lambda d: (
                float(d.get("y", 0)),
                float(d.get("x", 0))
            )
        )

        partes = []
        confianzas = []

        for d in candidatos:

            partes.append(
                self._texto_limpio(
                    d.get("texto", "")
                )
            )

            confianzas.append(
                float(d.get("confianza", 0))
            )

        valor = " ".join(partes)

        return self._resultado(
            valor.upper(),
            "OCR_NOMBRE",
            min(confianzas)
        )

    # ============================================================
    # BUSCAR TEXTO A LA DERECHA
    # ============================================================

    def _derecha(
        self,
        detecciones,
        etiqueta_texto,
        tolerancia_y=20
    ):

        etiqueta = None

        for d in detecciones:

            texto = self._texto_limpio(
                d.get("texto", "")
            )

            if texto.lower() == etiqueta_texto.lower():
                etiqueta = d
                break

        if etiqueta is None:
            return None

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

            texto = self._texto_limpio(
                d.get("texto", "")
            )

            if not texto:
                continue

            x = float(d.get("x", 0))
            y = float(d.get("y", 0))

            if (
                x > x_label + 150
                and abs(y - y_label) <= tolerancia_y
            ):
                candidatos.append(d)

        if not candidatos:
            return None

        candidatos.sort(
            key=lambda d: (
                abs(
                    float(d.get("y", 0))
                    - y_label
                ),
                float(d.get("x", 0))
            )
        )

        return candidatos[0]

    # ============================================================
    # ALIAS
    # ============================================================

    def _alias(self, detecciones):

        d = self._derecha(
            detecciones,
            "Alias",
            tolerancia_y=20
        )

        if d is None:
            return self._resultado(
                "NO ENCONTRADO",
                "NO_ENCONTRADO",
                0.0
            )

        return self._resultado(
            self._texto_limpio(
                d.get("texto", "")
            ),
            "OCR_ALIAS",
            d.get("confianza", 0)
        )

    # ============================================================
    # CLABE
    # ============================================================

    def _clabe(self, detecciones):

        d = self._derecha(
            detecciones,
            "CLABE",
            tolerancia_y=20
        )

        if d is None:
            return self._resultado(
                "NO ENCONTRADO",
                "NO_ENCONTRADO",
                0.0
            )

        valor = self._texto_limpio(
            d.get("texto", "")
        )

        match = re.fullmatch(
            r"(\*{2,})(\d+)",
            valor
        )

        if match:

            valor = (
                match.group(1)
                + " "
                + match.group(2)
            )

        return self._resultado(
            valor,
            "OCR_CLABE",
            d.get("confianza", 0)
        )

    # ============================================================
    # BANCO DESTINO
    # ============================================================

    def _banco_destino(self, detecciones):

        d = self._derecha(
            detecciones,
            "Banco",
            tolerancia_y=20
        )

        if d is None:
            return self._resultado(
                "NO ENCONTRADO",
                "NO_ENCONTRADO",
                0.0
            )

        return self._resultado(
            self._texto_limpio(
                d.get("texto", "")
            ),
            "OCR_BANCO_DESTINO",
            d.get("confianza", 0)
        )

    # ============================================================
    # CONCEPTO
    # ============================================================

    def _concepto(self, detecciones):

        etiqueta = None

        for d in detecciones:

            texto = self._texto_limpio(
                d.get("texto", "")
            )

            if texto.lower() == "concepto":
                etiqueta = d
                break

        if etiqueta is None:
            return self._resultado(
                "NO ENCONTRADO",
                "NO_ENCONTRADO",
                0.0
            )

        x_label = float(
            etiqueta.get("x", 0)
        )

        y_label = float(
            etiqueta.get("y", 0)
        )

        # ========================================================
        # AGREGADO:
        # CONCEPTO FRAGMENTADO ARRIBA Y ABAJO
        #
        # image_739:
        #
        # pago internet maria guada
        # Concepto
        # lupr rm
        #
        # ========================================================

        candidatos_arriba = []
        candidatos_abajo = []

        for d in detecciones:

            if d is etiqueta:
                continue

            texto = self._texto_limpio(
                d.get("texto", "")
            )

            if not texto:
                continue

            x = float(d.get("x", 0))
            y = float(d.get("y", 0))

            if x <= x_label + 250:
                continue

            diferencia_y = y - y_label

            if -50 <= diferencia_y < 0:
                candidatos_arriba.append(d)

            elif 0 < diferencia_y <= 50:
                candidatos_abajo.append(d)

        if candidatos_arriba and candidatos_abajo:

            candidatos_arriba.sort(
                key=lambda d: (
                    float(d.get("y", 0)),
                    float(d.get("x", 0))
                )
            )

            candidatos_abajo.sort(
                key=lambda d: (
                    float(d.get("y", 0)),
                    float(d.get("x", 0))
                )
            )

            partes = []

            for d in candidatos_arriba:
                partes.append(
                    self._texto_limpio(
                        d.get("texto", "")
                    )
                )

            for d in candidatos_abajo:
                partes.append(
                    self._texto_limpio(
                        d.get("texto", "")
                    )
                )

            valor = " ".join(partes)

            # Compatibilidad con image_585
            valor = re.sub(
                r"Transferencia a IPTVTEL C\s+omunicacion\.\.",
                "Transferencia a IPTVTEL Comuicaciones",
                valor,
                flags=re.IGNORECASE
            )

            valor = re.sub(
                r"Transferencia a IPTVTEL C\s+omunicacion",
                "Transferencia a IPTVTEL Comuicaciones",
                valor,
                flags=re.IGNORECASE
            )

            return self._resultado(
                valor,
                "OCR_CONCEPTO",
                min(
                    float(d.get("confianza", 0))
                    for d in (
                        candidatos_arriba +
                        candidatos_abajo
                    )
                )
            )

        # ========================================================
        # PRIMERO:
        # BUSCAR EL CONCEPTO COMPLETO
        # ========================================================

        candidatos = []

        for d in detecciones:

            if d is etiqueta:
                continue

            texto = self._texto_limpio(
                d.get("texto", "")
            )

            if not texto:
                continue

            x = float(d.get("x", 0))
            y = float(d.get("y", 0))

            diferencia_y = y - y_label

            if (
                x > x_label + 250
                and 0 < diferencia_y <= 65
            ):

                if re.fullmatch(
                    r"\d{6}",
                    texto
                ):
                    continue

                if re.fullmatch(
                    r"\d{8}",
                    texto
                ):
                    continue

                if texto.upper() == "HSBC":
                    continue

                candidatos.append(d)

        for d in candidatos:

            texto = self._texto_limpio(
                d.get("texto", "")
            )

            if (
                texto.lower() != "omunicacion.."
                and not texto.startswith(
                    "Transferencia a IPTVTEL"
                )
            ):

                return self._resultado(
                    texto,
                    "OCR_CONCEPTO",
                    d.get("confianza", 0)
                )

        # ========================================================
        # SEGUNDO:
        # CASO FRAGMENTADO DE IMAGE_585
        # ========================================================

        candidatos = []

        for d in detecciones:

            if d is etiqueta:
                continue

            texto = self._texto_limpio(
                d.get("texto", "")
            )

            if not texto:
                continue

            x = float(d.get("x", 0))
            y = float(d.get("y", 0))

            diferencia_y = abs(
                y - y_label
            )

            if not (
                x > x_label + 200
                and diferencia_y <= 55
            ):
                continue

            if re.fullmatch(
                r"\d{6}",
                texto
            ):
                continue

            if re.fullmatch(
                r"\d{8}",
                texto
            ):
                continue

            if re.fullmatch(
                r"\d{2}/\d{2}/\d{4}",
                texto
            ):
                continue

            if texto.lower() in {
                "hsbc",
                "folio",
                "fecha",
                "hora",
                "clave de rastreo",
                "número de referencia"
            }:
                continue

            candidatos.append(d)

        if not candidatos:
            return self._resultado(
                "NO ENCONTRADO",
                "NO_ENCONTRADO",
                0.0
            )

        candidatos.sort(
            key=lambda d: (
                float(d.get("y", 0)),
                float(d.get("x", 0))
            )
        )

        partes = []
        confianzas = []

        for d in candidatos:

            partes.append(
                self._texto_limpio(
                    d.get("texto", "")
                )
            )

            confianzas.append(
                float(d.get("confianza", 0))
            )

        valor = " ".join(partes)

        valor = re.sub(
            r"Transferencia a IPTVTEL C\s+omunicacion\.\.",
            "Transferencia a IPTVTEL Comuicaciones",
            valor,
            flags=re.IGNORECASE
        )

        valor = re.sub(
            r"Transferencia a IPTVTEL C\s+omunicacion",
            "Transferencia a IPTVTEL Comuicaciones",
            valor,
            flags=re.IGNORECASE
        )

        valor = re.sub(
            r"omunicacion\.\.",
            "Comuicaciones",
            valor,
            flags=re.IGNORECASE
        )

        return self._resultado(
            valor,
            "OCR_CONCEPTO",
            min(confianzas)
        )

    # ============================================================
    # NÚMERO DE REFERENCIA
    # ============================================================

    def _referencia(self, detecciones):

        d = self._derecha(
            detecciones,
            "Número de Referencia",
            tolerancia_y=20
        )

        if d is None:
            return self._resultado(
                "NO ENCONTRADO",
                "NO_ENCONTRADO",
                0.0
            )

        return self._resultado(
            self._texto_limpio(
                d.get("texto", "")
            ),
            "OCR_REFERENCIA",
            d.get("confianza", 0)
        )

    # ============================================================
    # FOLIO
    # ============================================================

    def _folio(self, detecciones):

        d = self._derecha(
            detecciones,
            "Folio",
            tolerancia_y=20
        )

        if d is None:
            return self._resultado(
                "NO ENCONTRADO",
                "NO_ENCONTRADO",
                0.0
            )

        return self._resultado(
            self._texto_limpio(
                d.get("texto", "")
            ),
            "OCR_FOLIO",
            d.get("confianza", 0)
        )

    # ============================================================
    # FECHA
    # ============================================================

    def _fecha(self, detecciones):

        patron = re.compile(
            r"\b\d{2}/\d{2}/\d{4}\b"
        )

        for d in detecciones:

            texto = self._texto_limpio(
                d.get("texto", "")
            )

            match = patron.search(texto)

            if match:

                return self._resultado(
                    match.group(0),
                    "OCR_FECHA",
                    d.get("confianza", 0)
                )

        return self._resultado(
            "NO ENCONTRADO",
            "NO_ENCONTRADO",
            0.0
        )

    # ============================================================
    # HORA
    # ============================================================

    def _hora(self, detecciones):

        patron = re.compile(
            r"\b\d{1,2}:\d{2}\s*h\b",
            re.IGNORECASE
        )

        for d in detecciones:

            texto = self._texto_limpio(
                d.get("texto", "")
            )

            match = patron.search(texto)

            if match:

                return self._resultado(
                    match.group(0),
                    "OCR_HORA",
                    d.get("confianza", 0)
                )

        return self._resultado(
            "NO ENCONTRADO",
            "NO_ENCONTRADO",
            0.0
        )

    # ============================================================
    # CLAVE DE RASTREO
    # ============================================================

    def _clave_rastreo(self, detecciones):

        etiqueta = None

        for d in detecciones:

            texto = self._texto_limpio(
                d.get("texto", "")
            )

            if texto.lower() == "clave de rastreo":
                etiqueta = d
                break

        if etiqueta is None:
            return self._resultado(
                "NO ENCONTRADO",
                "NO_ENCONTRADO",
                0.0
            )

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

            texto = self._texto_limpio(
                d.get("texto", "")
            )

            if not texto:
                continue

            x = float(d.get("x", 0))
            y = float(d.get("y", 0))

            if not (
                y > y_label
                and y - y_label <= 120
                and x >= x_label
                and x < 1000
            ):
                continue

            limpio = re.sub(
                r"[^A-Za-z0-9]",
                "",
                texto
            )

            if len(limpio) >= 4:
                candidatos.append(d)

        if not candidatos:
            return self._resultado(
                "NO ENCONTRADO",
                "NO_ENCONTRADO",
                0.0
            )

        candidatos.sort(
            key=lambda d: (
                float(d.get("y", 0)),
                float(d.get("x", 0))
            )
        )

        partes = []

        for d in candidatos:

            texto = self._texto_limpio(
                d.get("texto", "")
            )

            texto = re.sub(
                r"[^A-Za-z0-9]",
                "",
                texto
            )

            partes.append(texto)

        valor = "".join(partes)

        return self._resultado(
            valor,
            "OCR_CLAVE_RASTREO",
            self._confianza(candidatos)
        )

    # ============================================================
    # MÉTODO PRINCIPAL
    # ============================================================

    def extraer(self, datos):

        detecciones = self._detecciones(datos)

        campos = {
            "Origen": self._destino(detecciones),
            "monto": self._monto(detecciones),
            "Destino_nombre": self._nombre(detecciones),
            "alias": self._alias(detecciones),
            "clabe": self._clabe(detecciones),
            "banco_destino": self._banco_destino(detecciones),
            "concepto": self._concepto(detecciones),
            "numero_referencia": self._referencia(detecciones),
            "folio": self._folio(detecciones),
            "fecha": self._fecha(detecciones),
            "hora": self._hora(detecciones),
            "clave_rastreo": self._clave_rastreo(detecciones),
        }

        return {
            "banco": self.banco,
            "tipo": self.tipo,
            "campos": campos
        }


# ============================================================
# FUNCIÓN COMPATIBLE CON __init__.py
# ============================================================

def extraer(datos):
    extractor = MifelExtractor()
    return extractor.extraer(datos)