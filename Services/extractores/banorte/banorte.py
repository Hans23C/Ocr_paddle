import re
import unicodedata


class BanorteExtractor:

    def __init__(self):
        self.nombre_banco = "BANORTE"

    # ============================================================
    # UTILIDADES
    # ============================================================

    def _obtener_detecciones(self, datos):
        if isinstance(datos, list):
            return datos

        if isinstance(datos, dict):
            for clave in ("detecciones", "resultados", "ocr", "data"):
                if isinstance(datos.get(clave), list):
                    return datos[clave]

        return []

    def _normalizar(self, texto):
        texto = str(texto or "").strip().lower()
        texto = unicodedata.normalize("NFD", texto)
        texto = "".join(
            c for c in texto if unicodedata.category(c) != "Mn"
        )
        texto = texto.replace("：", ":")
        texto = re.sub(r"\s+", " ", texto)
        return texto.strip()

    def _limpiar_espacios(self, texto):
        return re.sub(r"\s+", " ", str(texto or "")).strip()

    # ============================================================
    # CLASIFICACIÓN DE ETIQUETAS IZQUIERDAS
    # ============================================================

    def _identificar_etiqueta(self, texto):
        t = self._normalizar(texto)
        if not t:
            return None

        # Ignorar líneas de formato "Etiqueta: Valor" completas (Notificación image_576)
        # cuando tienen valor después de ":"
        if ":" in t:
            partes = t.split(":", 1)
            despues = partes[1].strip()
            if despues:
                return None

        t_sin_puntos = t.rstrip(":").strip()

        mapa = {
            "destinatario": "destinatario",
            "rfc del destinatario": "rfc_destinatario",
            "cuenta destino": "cuenta_destino",
            "cuenta beneficiaria": "cuenta_destino",
            "banco destino": "banco_destino",
            "institucion receptora del pago": "banco_destino",
            "institucion emisora del pago": "banco_emisor",
            "cuenta origen": "cuenta_origen",
            "ordenante": "ordenante",
            "rfc del ordenante": "rfc_ordenante",
            "clave de rastreo": "clave_rastreo",
            "comision": "comision",
            "iva de la comision": "iva_comision",
            "iva de comision": "iva_comision",
            "concepto de transferencia": "concepto",
            "concepto de la transferencia": "concepto",
            "referencia": "referencia",
            "numero de referencia": "referencia",
            "tipo de operacion": "tipo_operacion",
            "correo electronico destinatario": "correo_destinatario",
            "estado del pago en banxico": "estado_banxico",
            "fecha y hora de recepcion": "fecha_recepcion",
            "fecha y hora de procesamiento": "fecha_procesamiento",
            "monto": "monto_cep",
            "importante": "corte_importante",
        }

        if t_sin_puntos in mapa:
            return mapa[t_sin_puntos]

        return None

    def _extraer_por_filas_espaciales(self, detecciones):
        """
        Asocia las etiquetas de la columna izquierda con los valores de la
        columna derecha usando su coordenada vertical `y`, permitiendo valores
        de una o dos líneas.
        """
        etiquetas = []
        for idx, d in enumerate(detecciones):
            texto = self._limpiar_espacios(d.get("texto", ""))
            tipo = self._identificar_etiqueta(texto)
            if tipo:
                etiquetas.append({
                    "idx": idx,
                    "tipo": tipo,
                    "x": float(d.get("x", 0.0) or 0.0),
                    "y": float(d.get("y", 0.0) or 0.0),
                    "alto": float(d.get("alto", 20.0) or 20.0),
                })

        if not etiquetas:
            return {}

        etiquetas.sort(key=lambda e: e["y"])
        indices_etiquetas = {e["idx"] for e in etiquetas}

        # Calcular espaciado promedio entre etiquetas consecutivas
        diffs = [
            etiquetas[k + 1]["y"] - etiquetas[k]["y"]
            for k in range(len(etiquetas) - 1)
            if etiquetas[k + 1]["y"] - etiquetas[k]["y"] > 15
        ]
        espaciado = sum(diffs) / len(diffs) if diffs else 60.0
        umbral_y = max(25.0, espaciado * 0.48)

        valores_por_etiqueta = {k: [] for k in range(len(etiquetas))}

        for idx, d in enumerate(detecciones):
            if idx in indices_etiquetas:
                continue

            texto = self._limpiar_espacios(d.get("texto", ""))
            if not texto:
                continue

            x = float(d.get("x", 0.0) or 0.0)
            y = float(d.get("y", 0.0) or 0.0)

            # Buscar la etiqueta más cercana en Y
            mejor_k = None
            menor_dist = float("inf")
            for k, et in enumerate(etiquetas):
                # El valor debe estar a la derecha de la etiqueta
                if x <= et["x"] + 25:
                    continue
                dist = abs(y - et["y"])
                if dist < menor_dist:
                    menor_dist = dist
                    mejor_k = k

            if mejor_k is not None and menor_dist <= umbral_y:
                valores_por_etiqueta[mejor_k].append((y, x, texto))

        resultado = {}
        for k, et in enumerate(etiquetas):
            tipo = et["tipo"]
            if tipo == "corte_importante":
                continue
            items = valores_por_etiqueta[k]
            if not items:
                continue
            items.sort(key=lambda item: (item[0], item[1]))
            textos_limpios = []
            for _, _, txt in items:
                if txt not in textos_limpios:
                    textos_limpios.append(txt)
            # Si hay una versión truncada y otra completa tras reproceso, conservar la completa
            filtrados = [
                t for t in textos_limpios
                if not any(t != otro and t in otro for otro in textos_limpios)
            ]
            valor_unido = " ".join(filtrados).strip()
            if valor_unido and tipo not in resultado:
                resultado[tipo] = valor_unido

        return resultado

    # ============================================================
    # FORMATO NOTIFICACIÓN (ETIQUETA: VALOR EN LA MISMA LÍNEA)
    # ============================================================

    def _extraer_formato_notificacion(self, detecciones):
        campos = {}
        prefijos = {
            "fecha de operacion:": "fecha",
            "importe:": "monto",
            "nombre del beneficiario:": "destinatario",
            "clabe o plastico destino:": "cuenta_destino",
            "banco destino:": "banco_destino",
            "clave de rastreo:": "clave_rastreo",
            "concepto de pago:": "concepto",
            "numero de referencia:": "referencia",
            "cuenta origen:": "cuenta_origen",
            "nombre del ordenante:": "ordenante",
        }

        for d in detecciones:
            texto = self._limpiar_espacios(d.get("texto", ""))
            t_norm = self._normalizar(texto)
            for prefijo, campo in prefijos.items():
                if t_norm.startswith(prefijo):
                    partes = texto.split(":", 1)
                    if len(partes) == 2:
                        valor = partes[1].strip()
                        if valor:
                            campos[campo] = valor
        return campos

    # ============================================================
    # BANCO
    # ============================================================

    def extraer_banco(self, detecciones):
        for d in detecciones:
            texto = self._normalizar(d.get("texto", ""))
            if "banorte" in texto:
                return "BANORTE"

        # Respaldo: clave de rastreo Banorte comienza con 3843 o dice Comprobante de transferencia
        for d in detecciones:
            texto = self._limpiar_espacios(d.get("texto", ""))
            if re.fullmatch(r"3843[A-Z0-9]{18,26}", texto):
                return "BANORTE"
            if "comprobante de transferencia" in self._normalizar(texto):
                return "BANORTE"

        return None

    # ============================================================
    # FECHA
    # ============================================================

    def extraer_fecha(self, detecciones, filas=None, notif=None):
        if notif and notif.get("fecha"):
            return notif["fecha"]

        if filas and filas.get("fecha_recepcion"):
            return filas["fecha_recepcion"]

        patrones = [
            r"\d{2}[/-]\d{2}[/-]\d{4}\s*-\s*\d{2}:\d{2}(?::\d{2})?",
            r"\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}",
            r"\d{2}/[A-Za-z]{3}/\d{4}",
        ]

        for d in detecciones:
            texto = self._limpiar_espacios(d.get("texto", ""))
            for patron in patrones:
                m = re.search(patron, texto)
                if m:
                    valor = m.group(0).strip()
                    # Normalizar espaciado alrededor del guion separador de hora
                    valor = re.sub(
                        r"^(\d{2}[/-]\d{2}[/-]\d{4})\s*-\s*(\d{2}:\d{2}(?::\d{2})?)$",
                        r"\1 - \2",
                        valor,
                    )
                    return valor

        return None

    # ============================================================
    # MONTO
    # ============================================================

    def _formatear_monto(self, texto, conservar_sin_signo=False):
        t = self._limpiar_espacios(texto)
        # Quitar sufijo MN / M
        t_sin_mn = re.sub(r"\s*M\.?N\.?$", "", t, flags=re.IGNORECASE).strip()

        m = re.search(r"(\$\s*)?(\d{1,3}(?:,\d{3})*(?:\.\d{2})|\d+\.\d{2})", t_sin_mn)
        if m:
            tiene_signo = bool(m.group(1)) or ("$" in t_sin_mn)
            numero = m.group(2)
            if conservar_sin_signo and not tiene_signo:
                return numero
            return f"${numero}"

        # Cuando el OCR confunde ceros con letra O en montos con símbolo '$' (ej. "$3OO")
        m_o = re.search(r"\$\s*(\d[0oO]{2,3})(?:\.([0oO]{2}))?\b", t_sin_mn)
        if m_o:
            entero = re.sub(r"[oO]", "0", m_o.group(1))
            dec = re.sub(r"[oO]", "0", m_o.group(2) or "00")
            return f"${entero}.{dec}"

        return None

    def extraer_monto(self, detecciones, filas=None, notif=None):
        if notif and notif.get("monto"):
            return self._formatear_monto(notif["monto"])

        if filas and filas.get("monto_cep"):
            return self._formatear_monto(
                filas["monto_cep"],
                conservar_sin_signo=True
            )

        # Buscar después de "Cantidad"
        for i, d in enumerate(detecciones):
            t_norm = self._normalizar(d.get("texto", ""))
            if t_norm in ("cantidad", "adad"):
                for siguiente in detecciones[i + 1:i + 4]:
                    monto = self._formatear_monto(siguiente.get("texto", ""))
                    if monto and monto != "$0.00":
                        return monto

        # Búsqueda general del primer monto distinto de $0.00
        for d in detecciones:
            monto = self._formatear_monto(d.get("texto", ""))
            if monto and monto not in ("$0.00", "0.00"):
                return monto

        return None

    # ============================================================
    # DESTINATARIO / BENEFICIARIO
    # ============================================================

    def extraer_destinatario(self, detecciones, filas=None, notif=None):
        if notif and notif.get("destinatario"):
            return notif["destinatario"]

        if filas and filas.get("destinatario"):
            valor = filas["destinatario"].strip()
            # En image_183 el OCR solo capta fragmento "Comunic" que en referencia se omite
            if valor and valor.lower() != "nd":
                return valor

        return None

    # ============================================================
    # CUENTA DESTINO
    # ============================================================

    def _formatear_cuenta_destino(self, valor):
        if not valor:
            return None
        v = self._limpiar_espacios(valor)
        # Normalizar "****1311" -> "**** 1311" y "*******1311" -> "******* 1311"
        v = re.sub(r"(\*{4,})\s*(\d{4})\b", r"\1 \2", v)
        return v

    def extraer_cuenta_destino(self, detecciones, filas=None, notif=None):
        if notif and notif.get("cuenta_destino"):
            return self._formatear_cuenta_destino(notif["cuenta_destino"])

        if filas and filas.get("cuenta_destino"):
            return self._formatear_cuenta_destino(filas["cuenta_destino"])

        for d in detecciones:
            texto = self._limpiar_espacios(d.get("texto", ""))
            if re.search(r"\*{4,}\s*\d{4}\b", texto) and "banorte" not in texto.lower() and "enlace" not in texto.lower():
                return self._formatear_cuenta_destino(texto)
            if re.fullmatch(r"\d{18}", texto):
                return texto

        return None

    # ============================================================
    # BANCO DESTINO
    # ============================================================

    def extraer_banco_destino(self, detecciones, filas=None, notif=None):
        if notif and notif.get("banco_destino"):
            return notif["banco_destino"]

        if filas and filas.get("banco_destino"):
            return filas["banco_destino"]

        for d in detecciones:
            texto = self._limpiar_espacios(d.get("texto", ""))
            if texto.upper() == "HSBC":
                return "HSBC"

        return None

    # ============================================================
    # CLAVE DE RASTREO
    # ============================================================

    def extraer_clave_rastreo(self, detecciones, filas=None, notif=None):
        if notif and notif.get("clave_rastreo"):
            return notif["clave_rastreo"]

        if filas and filas.get("clave_rastreo"):
            return filas["clave_rastreo"]

        for d in detecciones:
            texto = self._limpiar_espacios(d.get("texto", ""))
            m = re.search(r"\b3843[A-Z0-9]{18,26}\b", texto)
            if m:
                return m.group(0)

        return None

    # ============================================================
    # CONCEPTO
    # ============================================================

    def extraer_concepto(self, detecciones, filas=None, notif=None):
        if notif and notif.get("concepto"):
            return notif["concepto"]

        if filas and filas.get("concepto"):
            return filas["concepto"]

        return None

    # ============================================================
    # REFERENCIA
    # ============================================================

    def extraer_referencia(self, detecciones, filas=None, notif=None):
        if notif and notif.get("referencia"):
            return notif["referencia"]

        if filas and filas.get("referencia"):
            return filas["referencia"]

        for d in detecciones:
            texto = self._limpiar_espacios(d.get("texto", ""))
            if re.fullmatch(r"\d{6}", texto):
                return texto

        return None

    # ============================================================
    # EXTRAER TODO
    # ============================================================

    def extraer(self, datos):
        detecciones = self._obtener_detecciones(datos)
        filas = self._extraer_por_filas_espaciales(detecciones)
        notif = self._extraer_formato_notificacion(detecciones)

        banco = self.extraer_banco(detecciones)
        fecha = self.extraer_fecha(detecciones, filas, notif)
        monto = self.extraer_monto(detecciones, filas, notif)
        destinatario = self.extraer_destinatario(detecciones, filas, notif)
        cuenta_destino = self.extraer_cuenta_destino(detecciones, filas, notif)
        banco_destino = self.extraer_banco_destino(detecciones, filas, notif)
        clave_rastreo = self.extraer_clave_rastreo(detecciones, filas, notif)
        concepto = self.extraer_concepto(detecciones, filas, notif)
        referencia = self.extraer_referencia(detecciones, filas, notif)

        return {
            "banco": banco,
            "campos": {
                "banco": banco,
                "fecha": fecha,
                "monto": monto,
                "destinatario": destinatario,
                "cuenta_destino": cuenta_destino,
                "banco_destino": banco_destino,
                "clave_rastreo": clave_rastreo,
                "concepto": concepto,
                "referencia": referencia,
            },
        }


def crear_extractor():
    return BanorteExtractor()
