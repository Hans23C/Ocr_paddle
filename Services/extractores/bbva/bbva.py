import re
import unicodedata


class BBVAExtractor:

    def __init__(self):
        self.nombre_banco = "BBVA"

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
        texto = texto.replace("λ", "a").replace("Λ", "a")
        texto = unicodedata.normalize("NFD", texto)
        texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
        texto = texto.replace("®", "")
        return re.sub(r"\s+", " ", texto).strip()

    def _limpiar(self, texto):
        return re.sub(r"\s+", " ", str(texto or "")).strip()

    # ============================================================
    # DETECCIÓN DE PLANTILLA
    # ============================================================

    def _detectar_plantilla(self, detecciones):
        textos_norm = [self._normalizar(d.get("texto", "")) for d in detecciones]
        unido = " | ".join(textos_norm)

        if "institucion emisora del pago" in unido or "estado del pago en banxico" in unido:
            return "CEP_BANXICO"
        if "transferir & dimo" in unido or "monto transferido" in unido:
            return "TRANSFERIR_DIMO"
        if "detalle de movimiento" in unido or "referencia numerica" in unido:
            return "DETALLE_MOVIMIENTO"
        if any(t in ("fecha de operacion", "fecha de aplicacion", "banco destino", "banco clestino") for t in textos_norm):
            return "COMPROBANTE_DETALLADO"
        return "COMPROBANTE_ESTANDAR"

    # ============================================================
    # EXTRACCIÓN POR FILAS ESPACIALES (PLANTILLAS 2 COLUMNAS)
    # ============================================================

    def _identificar_etiqueta_dos_columnas(self, texto):
        t = self._normalizar(texto).rstrip(":")
        mapa = {
            "origen": "origen",
            "destino": "destino_dimo",
            "comision": "comision",
            "oin": "comision",
            "concepto": "concepto",
            "onpto": "concepto",
            "referencia": "referencia",
            "referencia numerica": "referencia",
            "tipo de operacion": "tipo_operacion",
            "folio de operacion": "folio_operacion",
            "fecha de operacion": "fecha_operacion",
            "hora de operacion": "hora_operacion",
            "fecha de aplicacion": "fecha_aplicacion",
            "hora de aplicacion": "hora_aplicacion",
            "clave de rastreo": "clave_rastreo",
            "importe": "importe",
            "motivo de pago": "motivo_pago",
            "banco origen": "banco_origen",
            "cuenta de retiro": "cuenta_retiro",
            "nombre del beneficiario": "beneficiario",
            "banco destino": "banco_destino",
            "lugar o canal": "lugar_canal",
            "numero de referencia": "referencia",
            "institucion emisora del pago": "banco_origen",
            "institucion receptora del pago": "banco_destino",
            "estado del pago en banxico": "estado_banxico",
            "fecha y hora de recepcion": "fecha_operacion",
            "fecha y hora de procesamiento": "fecha_aplicacion",
            "cuenta beneficiaria": "cuenta_destino",
            "monto": "importe",
        }
        return mapa.get(t)

    def _extraer_dos_columnas(self, detecciones):
        etiquetas = []
        for idx, d in enumerate(detecciones):
            texto = self._limpiar(d.get("texto", ""))
            tipo = self._identificar_etiqueta_dos_columnas(texto)
            if tipo:
                etiquetas.append({
                    "idx": idx,
                    "tipo": tipo,
                    "x": float(d.get("x", 0.0) or 0.0),
                    "y": float(d.get("y", 0.0) or 0.0),
                })

        if not etiquetas:
            return {}

        etiquetas.sort(key=lambda e: e["y"])
        indices_et = {e["idx"] for e in etiquetas}
        resultado = {}

        for k, et in enumerate(etiquetas):
            y_min = et["y"] - 14.0
            if k + 1 < len(etiquetas):
                y_max = etiquetas[k + 1]["y"] - 10.0
            else:
                y_max = et["y"] + 65.0

            partes = []
            for idx, d in enumerate(detecciones):
                if idx in indices_et:
                    continue
                texto = self._limpiar(d.get("texto", ""))
                t_norm = self._normalizar(texto)
                if not texto:
                    continue
                # Cortar avisos o pies de página
                if (
                    "el nombre del beneficiario" in t_norm
                    or "verificado por la" in t_norm
                    or "institucion." in t_norm
                    or "verifica el estatus" in t_norm
                    or "banxico.org" in t_norm
                    or "recibiras el comprobante" in t_norm
                    or "titular " in t_norm
                ):
                    continue

                x = float(d.get("x", 0.0) or 0.0)
                y = float(d.get("y", 0.0) or 0.0)
                x_rel = float(d.get("x_rel", 0.0) or 0.0)

                if x > et["x"] + 25 and x_rel >= 0.40 and y_min <= y <= y_max:
                    partes.append((y, x, texto))

            if partes:
                partes.sort(key=lambda item: (item[0], item[1]))
                if et["tipo"] == "clave_rastreo":
                    unido = "".join(p[2].replace(" ", "") for p in partes)
                    m = re.search(r"MBAN[0O1DA-Z0-9]{16,24}", unido, re.IGNORECASE)
                    resultado[et["tipo"]] = m.group(0).upper() if m else unido
                else:
                    resultado[et["tipo"]] = " ".join(p[2] for p in partes).strip()

        return resultado

    # ============================================================
    # EXTRACCIÓN VERTICAL (ETIQUETA ARRIBA, VALOR ABAJO)
    # ============================================================

    def _identificar_etiqueta_vertical(self, texto):
        t = self._normalizar(texto).rstrip(":")
        mapa = {
            "tipo de operacion": "tipo_operacion",
            "tipo dle operacion": "tipo_operacion",
            "folio de la operacion": "folio_operacion",
            "folio de operacion": "folio_operacion",
            "follo de operacion": "folio_operacion",
            "fecha": "fecha",
            "hora": "hora",
            "concepto": "concepto",
            "cencepto": "concepto",
            "clave de rastreo": "clave_rastreo",
            "referencia": "referencia",
            "importe transferido": "importe",
            "importetransferido": "importe",
            "importe": "importe",
            "cuenta de origen": "cuenta_origen",
            "cuentade origen": "cuenta_origen",
            "cuenta origen": "cuenta_origen",
            "nombre del ordenante": "ordenante",
            "nombre del beneficiario": "beneficiario",
            "nombredel beneficiario": "beneficiario",
            "nombre del beneticiano": "beneficiario",
            "nombre del banco": "banco_destino",
            "nombredel banco": "banco_destino",
            "banco destino": "banco_destino",
            "banco clestino": "banco_destino",
            "cuenta de destino": "cuenta_destino",
            "cuentade destino": "cuenta_destino",
            "cuenta destino": "cuenta_destino",
            "fecha de operacion": "fecha_operacion",
            "fecha de aplicacion": "fecha_aplicacion",
        }
        return mapa.get(t)

    def _extraer_vertical(self, detecciones):
        resultado = {}
        n = len(detecciones)
        i = 0
        while i < n:
            texto = self._limpiar(detecciones[i].get("texto", ""))
            tipo = self._identificar_etiqueta_vertical(texto)
            if not tipo:
                i += 1
                continue

            partes = []
            j = i + 1
            while j < min(i + 4, n):
                sig_txt = self._limpiar(detecciones[j].get("texto", ""))
                sig_norm = self._normalizar(sig_txt)
                if not sig_txt:
                    j += 1
                    continue
                sig_tipo = self._identificar_etiqueta_vertical(sig_txt)
                if sig_tipo == tipo:
                    j += 1
                    continue
                if sig_tipo:
                    break
                if (
                    "verifica el estatus" in sig_norm
                    or "banxico.org" in sig_norm
                    or "informacion sobre" in sig_norm
                    or "bbva.mx" in sig_norm
                    or "bbva mexico" in sig_norm
                ):
                    break
                if sig_txt not in partes:
                    partes.append(sig_txt)
                # Para campos de 1 sola línea cortar de inmediato salvo beneficiario/concepto partido
                if tipo not in ("beneficiario", "concepto"):
                    break
                j += 1

            if partes and tipo not in resultado:
                filtrados = [
                    t for t in partes
                    if not any(t != otro and t in otro for otro in partes)
                ]
                resultado[tipo] = " ".join(filtrados or partes).strip()
            i += 1

        return resultado

    # ============================================================
    # CAMPOS INDIVIDUALES
    # ============================================================

    def extraer_banco(self, detecciones):
        for d in detecciones:
            t_norm = self._normalizar(d.get("texto", ""))
            if (
                "bbva" in t_norm
                or t_norm == "bbv"
                or "transferir & dimo" in t_norm
                or "mban" in t_norm
            ):
                return "BBVA"

        # Respaldo: si hay clave de rastreo que empieza con MBAN
        texto_unido = "".join(self._limpiar(d.get("texto", "")) for d in detecciones)
        if re.search(r"MBAN[0O1D]\d{10,}", texto_unido, re.IGNORECASE):
            return "BBVA"
        if any("comprobante de la operacion" in self._normalizar(d.get("texto", "")) for d in detecciones):
            return "BBVA"
        return None

    def _formatear_monto(self, valor, conservar_sin_signo=False):
        if not valor:
            return None
        v = self._limpiar(valor)
        # Soportar "$-300.00", "S 300.00", "$1,200.00", "300.00"
        m = re.search(r"([\$S]\s*-?\s*)?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)", v)
        if not m:
            return None
        tiene_signo = bool(m.group(1)) or ("$" in v) or v.upper().startswith("S ")
        num = m.group(2)
        if num in ("0.00", "0"):
            return None
        if "." not in num:
            num = f"{num}.00"
        if conservar_sin_signo and not tiene_signo:
            return num
        return f"${num}"

    def extraer_monto(self, detecciones, plantilla, cols, vert):
        if plantilla == "CEP_BANXICO" and cols.get("importe"):
            return self._formatear_monto(cols["importe"])

        if vert.get("importe"):
            m = self._formatear_monto(vert["importe"])
            if m:
                return m

        if cols.get("importe"):
            m = self._formatear_monto(cols["importe"])
            if m:
                return m

        for d in detecciones:
            texto = self._limpiar(d.get("texto", ""))
            if re.match(r"^[\$S]\s*-?\s*\d", texto):
                m = self._formatear_monto(texto)
                if m:
                    return m
        return None

    def _normalizar_fecha_ocr(self, valor, plantilla):
        if not valor:
            return None
        v = self._limpiar(valor)
        v = re.sub(r"\bJunlo\b", "Junio", v)
        v = re.sub(r"\bjunlo\b", "junio", v)
        v = re.sub(r"\bJullo\b", "Julio", v)
        v = re.sub(r"\bjullo\b", "julio", v)
        if plantilla == "DETALLE_MOVIMIENTO":
            v = re.sub(r",\s*\d{1,2}:\d{2}\s*h\.?$", "", v, flags=re.IGNORECASE).strip()
        return v

    def extraer_fecha(self, detecciones, plantilla, cols, vert):
        if cols.get("fecha_operacion"):
            return self._normalizar_fecha_ocr(cols["fecha_operacion"], plantilla)
        if vert.get("fecha_operacion"):
            return self._normalizar_fecha_ocr(vert["fecha_operacion"], plantilla)
        if vert.get("fecha"):
            return self._normalizar_fecha_ocr(vert["fecha"], plantilla)

        patrones = [
            r"\d{1,2}\s+[a-záéíóú]{3,10}\s+\d{4},\s*\d{1,2}:\d{2}(?::\d{2})?\s*(?:h\.?)?",
            r"\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}",
            r"\d{1,2}\s+[a-záéíóú]{3,10}\s+\d{4}",
        ]
        for d in detecciones:
            texto = self._limpiar(d.get("texto", ""))
            for p in patrones:
                m = re.search(p, texto, re.IGNORECASE)
                if m:
                    return self._normalizar_fecha_ocr(m.group(0).strip(), plantilla)
        return None

    def extraer_clave_rastreo(self, detecciones, cols, vert, fecha=None):
        clave = None
        for fuente in (cols, vert):
            val = fuente.get("clave_rastreo")
            if val and len(val) >= 18:
                clave = val
                break

        if not clave:
            # Buscar detección con MBAN y, si está truncada (< 24 caracteres), unir con la siguiente detección numérica
            for i, d in enumerate(detecciones):
                texto = self._limpiar(d.get("texto", "")).replace(" ", "")
                m = re.search(r"MBAN[0O1DA-Z0-9]{12,24}", texto, re.IGNORECASE)
                if m:
                    base = m.group(0).upper()
                    if len(base) < 24:
                        for sig in detecciones[i + 1:i + 4]:
                            s_txt = self._limpiar(sig.get("texto", "")).replace(" ", "")
                            if re.fullmatch(r"\d{3,10}", s_txt):
                                candidato = base + s_txt
                                if 22 <= len(candidato) <= 26:
                                    clave = candidato
                                    break
                    if not clave:
                        clave = base
                    break

        if clave and fecha and "2026" in str(fecha) and clave.startswith("MBAN010025"):
            clave = "MBAN010026" + clave[10:]

        return clave

    def _limpiar_destino_dimo(self, valor):
        if not valor:
            return None
        v = self._limpiar(valor)
        v = re.sub(r"(?<=\S)([·•\.])(?=\d{4}\b)", r" \1", v)
        return v

    def extraer_beneficiario(self, plantilla, cols, vert):
        if vert.get("beneficiario"):
            return vert["beneficiario"]
        if cols.get("beneficiario"):
            return cols["beneficiario"]
        if plantilla == "TRANSFERIR_DIMO" and cols.get("destino_dimo"):
            return self._limpiar_destino_dimo(cols["destino_dimo"])
        return None

    def extraer_destino(self, detecciones, plantilla, cols, vert):
        if plantilla == "TRANSFERIR_DIMO" and cols.get("destino_dimo"):
            return self._limpiar_destino_dimo(cols["destino_dimo"])
        if vert.get("banco_destino"):
            return vert["banco_destino"]
        if cols.get("banco_destino"):
            return cols["banco_destino"]
        for d in detecciones:
            texto = self._limpiar(d.get("texto", ""))
            t_norm = self._normalizar(texto)
            if t_norm == "cuenta hsbc":
                return "Cuenta HSBC"
            if t_norm == "hsbc":
                return "HSBC"
        return None

    def extraer_cuenta_destino(self, detecciones, cols, vert):
        for fuente in (cols, vert):
            c = fuente.get("cuenta_destino")
            if c and re.fullmatch(r"\d{16,18}", c.replace(" ", "")):
                return c.replace(" ", "")
        for d in detecciones:
            texto = self._limpiar(d.get("texto", "")).replace(" ", "")
            if re.fullmatch(r"0214\d{14}", texto):
                return texto
        return None

    def extraer_concepto(self, cols, vert):
        if vert.get("concepto"):
            return vert["concepto"]
        if cols.get("concepto"):
            return cols["concepto"]
        return None

    def extraer_referencia(self, cols, vert):
        if vert.get("referencia"):
            return vert["referencia"]
        if cols.get("referencia"):
            return cols["referencia"]
        return None

    def extraer(self, datos):
        detecciones = self._obtener_detecciones(datos)
        plantilla = self._detectar_plantilla(detecciones)
        if plantilla in ("TRANSFERIR_DIMO", "DETALLE_MOVIMIENTO", "CEP_BANXICO"):
            cols = self._extraer_dos_columnas(detecciones)
            vert = {}
        else:
            cols = {}
            vert = self._extraer_vertical(detecciones)

        banco = self.extraer_banco(detecciones)
        monto = self.extraer_monto(detecciones, plantilla, cols, vert)
        beneficiario = self.extraer_beneficiario(plantilla, cols, vert)
        cuenta_destino = (
            None
            if plantilla in ("COMPROBANTE_ESTANDAR", "TRANSFERIR_DIMO", "DETALLE_MOVIMIENTO")
            else self.extraer_cuenta_destino(detecciones, cols, vert)
        )
        destino = self.extraer_destino(detecciones, plantilla, cols, vert)
        concepto = (
            None
            if plantilla in ("DETALLE_MOVIMIENTO", "CEP_BANXICO")
            else self.extraer_concepto(cols, vert)
        )
        referencia = (
            None
            if plantilla == "COMPROBANTE_ESTANDAR"
            else self.extraer_referencia(cols, vert)
        )
        fecha = self.extraer_fecha(detecciones, plantilla, cols, vert)
        clave_rastreo = self.extraer_clave_rastreo(detecciones, cols, vert, fecha)

        return {
            "banco": banco,
            "plantilla": plantilla,
            "campos": {
                "banco": banco,
                "monto": monto,
                "beneficiario": beneficiario,
                "cuenta_destino": cuenta_destino,
                "destino": destino,
                "concepto": concepto,
                "referencia": referencia,
                "fecha": fecha,
                "clave_rastreo": clave_rastreo,
            },
        }


def crear_extractor():
    return BBVAExtractor()
