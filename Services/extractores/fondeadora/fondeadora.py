import re
import unicodedata


class FondeadoraExtractor:

    def __init__(self):
        self.nombre_banco = "FONDEADORA"

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
        texto = texto.replace("®", "")
        return re.sub(r"\s+", " ", texto).strip()

    def _limpiar(self, texto):
        return re.sub(r"\s+", " ", str(texto or "")).strip()

    # ============================================================
    # CAMPOS
    # ============================================================

    def extraer_banco(self, detecciones):
        for d in detecciones:
            t = self._normalizar(d.get("texto", ""))
            if "fondeadora" in t:
                return "FONDEADORA"
            if re.fullmatch(r"fon\d{18,26}", t):
                return "FONDEADORA"
        return None

    def extraer_monto(self, detecciones):
        # En Fondeadora el monto aparece al inicio como "400" y "$" separados o juntos
        for i, d in enumerate(detecciones[:5]):
            texto = self._limpiar(d.get("texto", ""))
            m_completo = re.fullmatch(r"\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)", texto)
            if m_completo:
                num = m_completo.group(1)
                if "." not in num:
                    num = f"{num}.00"
                return f"${num}"
        return None

    def extraer_fecha(self, detecciones):
        patron = r"\d{1,2}\s+de\s+[a-záéíóú]+\s+a\s+las\s+\d{1,2}:\d{2}\s*(?:am|pm|a\.m\.|p\.m\.)?"
        for d in detecciones:
            texto = self._limpiar(d.get("texto", ""))
            m = re.search(patron, texto, re.IGNORECASE)
            if m:
                return m.group(0).strip()
        return None

    def extraer_transferencia_para(self, detecciones):
        for i, d in enumerate(detecciones):
            t_norm = self._normalizar(d.get("texto", ""))
            if t_norm == "transferencia para":
                partes = []
                for sig in detecciones[i + 1:i + 5]:
                    s_txt = self._limpiar(sig.get("texto", ""))
                    s_norm = self._normalizar(s_txt)
                    if not s_txt:
                        continue
                    # Cortar cuando empieza el banco receptor o la CLABE o siguiente etiqueta
                    if (
                        s_norm in ("hsbc", "estatus", "concepto")
                        or re.fullmatch(r"(?:\d{4}\s+){4}\d{2}|\d{18}", s_txt)
                    ):
                        break
                    partes.append(s_txt)
                if partes:
                    return " ".join(partes).strip()
        return None

    def extraer_banco_receptor(self, detecciones):
        banco_rec = None
        clabe_rec = None
        for i, d in enumerate(detecciones):
            s_txt = self._limpiar(d.get("texto", ""))
            s_norm = self._normalizar(s_txt)
            if re.fullmatch(r"(?:\d{4}\s+){4}\d{2}|\d{18}", s_txt):
                clabe_rec = s_txt
                if i > 0:
                    prev_txt = self._limpiar(detecciones[i - 1].get("texto", ""))
                    prev_norm = self._normalizar(prev_txt)
                    if prev_norm not in ("transferencia para", "cv"):
                        banco_rec = prev_txt
                break
        if banco_rec and clabe_rec:
            return f"{banco_rec} {clabe_rec}"
        return clabe_rec or banco_rec

    def extraer_estatus(self, detecciones):
        for i, d in enumerate(detecciones):
            if self._normalizar(d.get("texto", "")) == "estatus":
                if i + 1 < len(detecciones):
                    return self._limpiar(detecciones[i + 1].get("texto", ""))
        return None

    def extraer_concepto(self, detecciones):
        for i, d in enumerate(detecciones):
            if self._normalizar(d.get("texto", "")) == "concepto":
                partes = []
                for sig in detecciones[i + 1:i + 4]:
                    s_txt = self._limpiar(sig.get("texto", ""))
                    s_norm = self._normalizar(s_txt)
                    if not s_txt:
                        continue
                    if "clave de rastreo" in s_norm or "fondeadora" in s_norm:
                        break
                    partes.append(s_txt)
                if partes:
                    return " ".join(partes).strip()
        return None

    def extraer_clave_rastreo(self, detecciones):
        for i, d in enumerate(detecciones):
            s_txt = self._limpiar(d.get("texto", ""))
            s_norm = self._normalizar(s_txt)
            if "clave de rastreo" in s_norm:
                if i + 1 < len(detecciones):
                    cand = self._limpiar(detecciones[i + 1].get("texto", ""))
                    if cand:
                        return cand
            if re.fullmatch(r"FON\d{18,26}", s_txt, re.IGNORECASE):
                return s_txt
        return None

    def extraer(self, datos):
        detecciones = self._obtener_detecciones(datos)
        banco = self.extraer_banco(detecciones)

        return {
            "banco": banco,
            "campos": {
                "banco": banco,
                "monto": self.extraer_monto(detecciones),
                "fecha": self.extraer_fecha(detecciones),
                "transferencia_para": self.extraer_transferencia_para(detecciones),
                "banco_receptor": self.extraer_banco_receptor(detecciones),
                "estatus": self.extraer_estatus(detecciones),
                "concepto": self.extraer_concepto(detecciones),
                "clave_rastreo": self.extraer_clave_rastreo(detecciones),
            },
        }


def crear_extractor():
    return FondeadoraExtractor()
