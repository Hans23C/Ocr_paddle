import re
import unicodedata


class HeyBancoExtractor:

    def __init__(self):
        self.nombre_banco = "hey,banco"

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

    # ============================================================
    # EMPAREJAMIENTO ESPACIAL POR FILAS (ETIQUETA IZQ / VALOR DER)
    # ============================================================

    def _identificar_etiqueta(self, texto):
        t = self._normalizar(texto).rstrip(":")
        mapa = {
            "descripcion": "descripcion",
            "desde": "desde",
            "tipo de transferencia": "tipo_transferencia",
            "comision": "comision",
            "total": "total",
            "referencia": "referencia",
            "clave de rastreo": "clave_rastreo",
            "cep (comprobante electronico de pago)": "corte_cep",
        }
        return mapa.get(t)

    def _extraer_filas(self, detecciones):
        etiquetas = []
        for idx, d in enumerate(detecciones):
            texto = self._limpiar(d.get("texto", ""))
            tipo = self._identificar_etiqueta(texto)
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
        indices_etiquetas = {e["idx"] for e in etiquetas}

        diffs = [
            etiquetas[k + 1]["y"] - etiquetas[k]["y"]
            for k in range(len(etiquetas) - 1)
            if etiquetas[k + 1]["y"] - etiquetas[k]["y"] > 10
        ]
        espaciado = sum(diffs) / len(diffs) if diffs else 30.0
        umbral_y = max(16.0, espaciado * 0.55)

        valores = {k: [] for k in range(len(etiquetas))}
        for idx, d in enumerate(detecciones):
            if idx in indices_etiquetas:
                continue
            texto = self._limpiar(d.get("texto", ""))
            if not texto:
                continue
            x = float(d.get("x", 0.0) or 0.0)
            y = float(d.get("y", 0.0) or 0.0)

            mejor_k = None
            menor_dist = float("inf")
            for k, et in enumerate(etiquetas):
                if x <= et["x"] + 20:
                    continue
                dist = abs(y - et["y"])
                if dist < menor_dist:
                    menor_dist = dist
                    mejor_k = k

            if mejor_k is not None and menor_dist <= umbral_y:
                valores[mejor_k].append((y, x, texto))

        resultado = {}
        for k, et in enumerate(etiquetas):
            tipo = et["tipo"]
            if tipo == "corte_cep":
                continue
            items = valores[k]
            if not items:
                continue
            items.sort(key=lambda item: (item[0], item[1]))
            if tipo == "clave_rastreo":
                # En Hey Banco la clave de rastreo se parte en dos renglones sin espacio
                valor = "".join(item[2].replace(" ", "") for item in items)
            elif tipo == "desde":
                valor = "".join(item[2] for item in items)
            else:
                valor = " ".join(item[2] for item in items)
            resultado[tipo] = valor.strip()

        return resultado

    # ============================================================
    # CAMPOS
    # ============================================================

    def extraer_banco(self, detecciones):
        for d in detecciones:
            t = self._normalizar(d.get("texto", ""))
            if "hey" in t or "nebanco" in t or "heybanco" in t:
                return "hey,banco"
        return None

    def extraer_fecha(self, detecciones):
        patron = r"\d{1,2}/[A-Za-z]{3}/\d{4},?\s*\d{1,2}:\d{2}\s*(?:a\.m\.|p\.m\.|am|pm)?"
        for d in detecciones:
            texto = self._limpiar(d.get("texto", ""))
            m = re.search(patron, texto, re.IGNORECASE)
            if m:
                return m.group(0).strip()
        return None

    def extraer_monto(self, detecciones):
        # El monto principal aparece arriba antes de la CLABE/Descripción
        for d in detecciones:
            texto = self._limpiar(d.get("texto", ""))
            if re.fullmatch(r"\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})", texto):
                return texto.replace(" ", "").replace(",", "")
        return None

    def extraer(self, datos):
        detecciones = self._obtener_detecciones(datos)
        filas = self._extraer_filas(detecciones)
        banco = self.extraer_banco(detecciones)
        monto = self.extraer_monto(detecciones)
        total_raw = filas.get("total")
        total = total_raw.replace(" ", "").replace(",", "") if total_raw else monto

        return {
            "banco": banco,
            "campos": {
                "banco": banco,
                "fecha": self.extraer_fecha(detecciones),
                "monto": monto,
                "descripcion": filas.get("descripcion"),
                "tipo_transferencia": filas.get("tipo_transferencia"),
                "comision": filas.get("comision"),
                "total": total,
                "referencia": filas.get("referencia"),
                "clave_rastreo": filas.get("clave_rastreo"),
            },
        }


def crear_extractor():
    return HeyBancoExtractor()
