import re
import unicodedata


class AlboExtractor:

    def __init__(self):
        self.nombre_banco = "albo"

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
        texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
        return re.sub(r"\s+", " ", texto).strip()

    def _limpiar(self, texto):
        return re.sub(r"\s+", " ", str(texto or "")).strip()

    def _buscar_por_etiqueta(self, detecciones, etiquetas):
        etiquetas_norm = [self._normalizar(e) for e in etiquetas]

        for i, d in enumerate(detecciones):
            texto = self._limpiar(d.get("texto", ""))
            t_norm = self._normalizar(texto)
            y_et = float(d.get("y", 0.0) or 0.0)
            x_et = float(d.get("x", 0.0) or 0.0)

            for et in etiquetas_norm:
                # Caso 1: La etiqueta contiene el valor en la misma detección
                if t_norm.startswith(et) and len(t_norm) > len(et):
                    resto = re.sub(
                        rf"^{re.escape(et)}\s*[:\-]?\s*",
                        "",
                        texto,
                        flags=re.IGNORECASE,
                    ).strip()
                    if resto:
                        return resto

                # Caso 2: Coincidencia exacta de la etiqueta; buscar en la misma fila (Y cercano) o siguiente detección
                if t_norm.rstrip(":") == et.rstrip(":"):
                    candidatos = []
                    for j, cand in enumerate(detecciones):
                        if j == i:
                            continue
                        c_texto = self._limpiar(cand.get("texto", ""))
                        if not c_texto:
                            continue
                        c_x = float(cand.get("x", 0.0) or 0.0)
                        c_y = float(cand.get("y", 0.0) or 0.0)
                        if c_x > x_et + 20 and abs(c_y - y_et) <= 25:
                            candidatos.append((abs(c_y - y_et), c_x, c_texto))
                    if candidatos:
                        candidatos.sort(key=lambda item: (item[0], item[1]))
                        return candidatos[0][2]

                    if i + 1 < len(detecciones):
                        sig = self._limpiar(detecciones[i + 1].get("texto", ""))
                        if sig:
                            return sig

        return None

    # ============================================================
    # CAMPOS
    # ============================================================

    def extraer_banco(self, detecciones):
        for d in detecciones:
            t_norm = self._normalizar(d.get("texto", ""))
            if t_norm == "albo" or "albo" in t_norm:
                return "albo"
        return None

    def extraer_monto(self, detecciones):
        for d in detecciones:
            texto = self._limpiar(d.get("texto", ""))
            m = re.search(r"\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})", texto)
            if m:
                return re.sub(r"\s+", "", m.group(0))
        return None

    def extraer_nombre(self, detecciones):
        return self._buscar_por_etiqueta(
            detecciones,
            ["nombre", "beneficiario", "destinatario"],
        )

    def extraer_fecha(self, detecciones):
        valor = self._buscar_por_etiqueta(
            detecciones,
            ["fecha y hora", "fecha"],
        )
        if valor:
            return valor

        for d in detecciones:
            texto = self._limpiar(d.get("texto", ""))
            if re.search(r"\d{1,2}\s+de\s+[a-záéíóú]{3,10}\s+\d{4}", texto, re.I):
                return texto
        return None

    def extraer_clabe(self, detecciones):
        valor = self._buscar_por_etiqueta(detecciones, ["clabe", "cuenta"])
        if valor:
            return valor

        for d in detecciones:
            texto = self._limpiar(d.get("texto", ""))
            if re.fullmatch(r"(?:\d{4}\s+){4}\d{2}|\d{18}", texto):
                return texto
        return None

    def extraer_concepto(self, detecciones):
        return self._buscar_por_etiqueta(detecciones, ["concepto"])

    def extraer_clave_rastreo(self, detecciones):
        valor = self._buscar_por_etiqueta(detecciones, ["clave de rastreo"])
        if valor:
            return valor

        for d in detecciones:
            texto = self._limpiar(d.get("texto", ""))
            m = re.search(r"\b\d{8,14}ALBO\d{8,16}\b", texto, re.I)
            if m:
                return m.group(0)
        return None

    # ============================================================
    # EXTRAER TODO
    # ============================================================

    def extraer(self, datos):
        detecciones = self._obtener_detecciones(datos)
        banco = self.extraer_banco(detecciones)

        return {
            "banco": banco,
            "campos": {
                "banco": banco,
                "nombre": self.extraer_nombre(detecciones),
                "fecha": self.extraer_fecha(detecciones),
                "clabe": self.extraer_clabe(detecciones),
                "concepto": self.extraer_concepto(detecciones),
                "clave_rastreo": self.extraer_clave_rastreo(detecciones),
            },
        }


def crear_extractor():
    return AlboExtractor()
