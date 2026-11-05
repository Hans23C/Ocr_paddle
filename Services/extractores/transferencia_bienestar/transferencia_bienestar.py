import re
import unicodedata


class TransferenciaBienestarExtractor:

    def __init__(self):
        self.nombre_banco = "Banco del Bienestar"

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

    def _identificar_etiqueta(self, texto):
        t = self._normalizar(texto).rstrip(":")
        if t == "recibe":
            return "recibe"
        if t == "beneficiario":
            return "beneficiario"
        if t == "desde tu cuenta":
            return "desde_tu_cuenta"
        if "referencia" in t:
            return "referencia"
        if t == "concepto":
            return "concepto"
        return None

    def _extraer_secciones(self, detecciones):
        etiquetas = []
        for idx, d in enumerate(detecciones):
            tipo = self._identificar_etiqueta(d.get("texto", ""))
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
            y_min = et["y"] - 8.0
            if k + 1 < len(etiquetas):
                y_max = etiquetas[k + 1]["y"] - 8.0
            else:
                y_max = et["y"] + 65.0

            partes = []
            for idx, d in enumerate(detecciones):
                if idx in indices_et:
                    continue
                texto = self._limpiar(d.get("texto", ""))
                t_norm = self._normalizar(texto)
                if not texto or t_norm in ("banco del", "bienestar"):
                    continue
                x = float(d.get("x", 0.0) or 0.0)
                y = float(d.get("y", 0.0) or 0.0)
                if x > et["x"] + 20 and y_min <= y <= y_max:
                    partes.append((y, x, texto))

            if partes:
                partes.sort(key=lambda item: (item[0], item[1]))
                valor = " ".join(p[2] for p in partes).strip()
                if et["tipo"] == "desde_tu_cuenta":
                    valor = re.sub(r"[…\.]+", "....", valor)
                resultado[et["tipo"]] = valor

        return resultado

    # ============================================================
    # CAMPOS
    # ============================================================

    def extraer_banco(self, detecciones):
        textos = [self._normalizar(d.get("texto", "")) for d in detecciones]
        unido = " ".join(textos)
        if "banco del bienestar" in unido or ("banco del" in unido and "bienestar" in unido):
            return "Banco del Bienestar"
        return None

    def extraer_monto(self, detecciones):
        for d in detecciones:
            texto = self._limpiar(d.get("texto", ""))
            m = re.fullmatch(r"\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2}))", texto)
            if m:
                return f"${m.group(1)}"
        return None

    def extraer_fecha(self, detecciones):
        patron = r"\d{1,2}\s+[a-záéíóú]{3,10}\s+\d{4}\s*-\s*\d{2}:\d{2}:\d{2}"
        for d in detecciones:
            texto = self._limpiar(d.get("texto", ""))
            m = re.search(patron, texto, re.IGNORECASE)
            if m:
                return m.group(0)
        return None

    def extraer(self, datos):
        detecciones = self._obtener_detecciones(datos)
        secciones = self._extraer_secciones(detecciones)
        banco = self.extraer_banco(detecciones)

        return {
            "banco": banco,
            "campos": {
                "banco": banco,
                "monto": self.extraer_monto(detecciones),
                "fecha": self.extraer_fecha(detecciones),
                "recibe": secciones.get("recibe"),
                "beneficiario": secciones.get("beneficiario"),
                "desde_tu_cuenta": secciones.get("desde_tu_cuenta"),
                "referencia": secciones.get("referencia"),
                "concepto": secciones.get("concepto"),
            },
        }


def crear_extractor():
    return TransferenciaBienestarExtractor()
