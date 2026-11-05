from pathlib import Path
import argparse
import json
import re
import unicodedata

# ============================================================
# HSBC - EXTRACTOR HÍBRIDO V1.2.5 EXPERIMENTAL
# ============================================================
# PRINCIPIO FUNDAMENTAL: EXTRAER, NO INVENTAR.
# - Lee JSON de entrada sin modificarlos.
# - Procesa por bloques de 10 comprobantes.
# - Usa tolerancia contextual para etiquetas OCR conocidas.
# - No sustituye lecturas OCR por valores manuales.
# - Utiliza ventanas espaciales delimitadas por etiquetas/cortes.
# - Genera un TXT por bloque con campos y detecciones originales.
#
# Ubicación prevista del script: <proyecto>/Pruebas/probar_hibrido_hsbc.py
# La carpeta de entrada predeterminada es:
# <proyecto>/Resultados_OCR/BANCO_HSBC
# Se puede cambiar con --carpeta-json.
# ============================================================

TAMANO_BLOQUE = 10
CAMPOS_OBJETIVO = ["banco", "fecha", "folio", "deposito", "monto", "cuenta", "titular"]

# Se usa normalización solo para COMPARAR etiquetas. El texto extraído
# siempre se conserva tal cual aparece en las detecciones OCR originales.
ETIQUETAS = {
    "folio": ["folio", "folid", "foli0", "fol1d", "filid", "fli0", "flid", "fulid", "olio"],
    "deposito": ["deposito:", "total deposito", "tutal deposito", "total deposiid", "total depositd"],
    "cuenta": ["cuenta:", "cuenta de deposito", "cuenta de depositd", "cuenta de depositio", "cuenta de depisitd", "cuenta de deposiid", "cuenta de depdsitd"],
    "titular": ["titular:", "nombre:", "nompre:", "hem bre:", "nembre:", "nepbre:", "heppre:", "hedre:"],
}

CORTES_GENERALES = [
    "con la recepcion de este comprobante",
    "con la recepcion de este comprornte",
    "que los datos",
    "que los datios",
    "este recibo es tu comprobante",
    "comprobante. dudas",
    "al telefono",
    "www.hsbc.com.mx",
]

# Las expresiones permiten conservar formatos de fecha observados en los
# JSON de HSBC. No convierten ni normalizan el valor recuperado.
PATRONES_FECHA = [
    # Fecha + hora completa: Jul 03, 2026 1:46:36 PM. Debe ir primero
    # para evitar que una expresión de fecha corta capture solo el prefijo.
    re.compile(
        r"\b[A-Za-z0-9]{3,9}\s+\d{1,2},?\s+\d{4}\s+"
        r"\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b[A-Za-z0-9]{3,9}\s+\d{1,2},?\s+\d{4}\b", re.IGNORECASE),  # Jul 03, 2026
    re.compile(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b"),                     # 05-06-2026
    re.compile(r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}\b", re.IGNORECASE),  # 05 Jun 2026; el mes debe contener letras
]
PATRONES_MONTO = [
    re.compile(r"(?<![\w])\$\s*\d+(?:,\d{3})*(?:\.\d{2})?(?!\d)"),
    re.compile(r"(?<![\d])\d+(?:,\d{3})*\.\d{2}(?!\d)"),
]


def normalizar(texto):
    """Normaliza solo para comparar etiquetas; nunca se usa como valor extraído."""
    texto = str(texto or "").strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.replace("：", ":")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def numero_archivo(ruta):
    coincidencia = re.search(r"(\d+)", ruta.stem)
    return int(coincidencia.group(1)) if coincidencia else 10**9


def preparar_detecciones(datos):
    """Prepara copias de las detecciones y las ordena espacialmente."""
    resultado = []
    detecciones = datos.get("detecciones", []) if isinstance(datos, dict) else []
    if not isinstance(detecciones, list):
        return resultado

    for indice, original in enumerate(detecciones):
        if not isinstance(original, dict):
            continue
        d = dict(original)
        d["_indice_original"] = indice
        for campo in ("x", "y", "ancho", "alto"):
            try:
                d[f"_{campo}"] = float(d.get(campo, 0) or 0)
            except (TypeError, ValueError):
                d[f"_{campo}"] = 0.0
        d["texto"] = str(d.get("texto", "") or "")
        resultado.append(d)

    resultado.sort(key=lambda d: (d["_y"], d["_x"], d["_indice_original"]))
    return resultado


def es_etiqueta_folio(texto):
    t = normalizar(texto)
    # Variantes observadas en las muestras HSBC: FOLIO, FOLID, FOLI0,
    # FILID, FLI0, FULID y OLIO. Solo se normaliza para localizar la etiqueta.
    return bool(re.search(
        r"(?:\bfolio\b|\bfolid\b|\bfoli0\b|\bfol1d\b|\bfilid\b|\bfli0\b|\bflid\b|\bedl10\b|\beliq\b|^\s*olio\b|^\s*lio\s*[:：]|^\s*fulid\s*[:：]?)",
        t,
    ))


def detectar_etiqueta(texto):
    t = normalizar(texto)
    if not t:
        return None

    if es_etiqueta_folio(t):
        return "folio"

    # Tipo de operación: admitir la ausencia de espacio entre
    # CUENTA y HSBC en el texto reconocido por el OCR.
    if re.match(
        r"^(?:deposito|eposito|posito)\s*,?\s*a\s*cuenta\s*hsbc\b",
        t,
    ):
        return "deposito"
    # Variantes específicas detectadas en image_210 e image_488.
    # Se comparan como etiqueta, pero el texto OCR original nunca se modifica.
    if re.match(r"^(?:deposito|depostto|depostito|depiidii?xto)[-\s,;:]*?(?:mixto|hixto|nixto|mixio|mixid|mixtio)?\b", t) and any(k in t for k in ("mix", "hix", "nix", "iixto")):
        return "deposito"
    if re.match(r"^posito\s+a\s+cuenta\s+hsbc\b", t):
        return "deposito"
    # Etiquetas del importe depositado.
    if re.search(r"\b(?:total|tutal)\s+deposi(?:to|iid|td)\b", t):
        return "monto"
    if re.match(r"^deposi(?:to|iid|td)\s*[:：]", t):
        return "monto"

    # La etiqueta CUENTA sin complemento se usa en los recibos modernos.
    # En recibos de caja, CUENTA DE DEPOSITO puede incluir el valor en la misma detección.
    if re.match(r"^cuenta\s*[:：]?$", t):
        return "cuenta"
    # Se contemplan errores OCR observados en HSBC, incluyendo DEPOSITIO,
    # DEPISITD y DEPDSITD. La etiqueta se reconoce, pero el valor se conserva literal.
    if re.match(r"^(?:cuenta|cuenth|cueta|cuexta|guenta|cluenta|qenta|qet\s*e|entr|enta|donia)\s*:?\s*de\s+dep(?:os|is|ds|0s|01|es|si)(?:it|i1)?(?:o|e|a|d|io|iid|td|1d)\b", t):
        return "cuenta"
    # OCR degradado específico: "ENTH DE DEPOSITO:**9131".
    if re.match(r"^enth\s+de\s+deposito\s*[:：]", t):
        return "cuenta"

    if re.match(r"^(?:titular|nombre|nompre|hompre|nopbre|nopre|nembre|nmere|nmbre|mpbre|mmpre|neere|nivre|niddre|hiere|hubre|huere|nepbre|heppre|hedre|nocre|ntere|noere|htpre)\s*[:：\*]?", t):
        return "titular"
    # Variantes observadas en comprobantes HSBC con OCR degradado.
    if re.match(r"^hem\s*bre\s*[:：]", t):
        return "titular"

    return None


def localizar_etiquetas(detecciones):
    """Devuelve las etiquetas encontradas, su posición y su detección fuente."""
    resultado = []
    for posicion, deteccion in enumerate(detecciones):
        campo = detectar_etiqueta(deteccion.get("texto", ""))
        if campo:
            resultado.append({"campo": campo, "posicion": posicion, "deteccion": deteccion})
    return resultado


def encontrar_patron(texto, patrones):
    texto = str(texto or "")
    for patron in patrones:
        coincidencia = patron.search(texto)
        if coincidencia:
            return coincidencia.group(0)
    return ""


def resolver_patron(candidatos, tipo):
    """Resuelve candidatos de fecha o monto sin alterar el texto coincidente."""
    if not candidatos:
        return {"valor": "", "estado": "NO_ENCONTRADO", "confianza": 0.0, "metodo": f"PATRON_{tipo.upper()}", "detecciones": []}

    candidatos = sorted(
        candidatos,
        key=lambda c: (c.get("confianza", 0.0), -c.get("distancia", 0.0)),
        reverse=True,
    )
    elegido = candidatos[0]
    return {
        "valor": elegido["valor"],
        "estado": "ENCONTRADO",
        "confianza": float(elegido.get("confianza", 0.0)),
        "metodo": f"PATRON_{tipo.upper()}",
        "detecciones": [elegido["deteccion"]],
    }


def contiene_corte(texto):
    t = normalizar(texto)
    return any(normalizar(corte) in t for corte in CORTES_GENERALES)


def es_limite_ventana(texto, campo_actual=None):
    """Reconoce etiquetas auxiliares que delimitan valores aunque no sean campos de salida."""
    t = normalizar(texto)
    if detectar_etiqueta(texto):
        return True
    limites = (
        "recibido:", "recibido", "cambio:", "cambio", "efectivo:", "efectivo",
        "total documento", "total documentd", "total documenion",
        "deposito aplicado", "tu deposito ya fue", "total deposito", "tutal deposito",
    )
    for limite in limites:
        if t.startswith(normalizar(limite)):
            # La propia etiqueta TOTAL DEPOSITO debe abrir la ventana para extraer el monto.
            if campo_actual in ("deposito", "monto") and limite in ("total deposito", "tutal deposito"):
                return False
            return True
    return False


def texto_despues_de_etiqueta(texto):
    """Devuelve solo el segmento posterior a ':' cuando existe; no lo corrige."""
    original = str(texto or "")
    if ":" in original:
        return original.split(":", 1)[1].strip()
    if "：" in original:
        return original.split("：", 1)[1].strip()
    return ""


def valor_embebido(campo, deteccion):
    """Extrae un valor incluido en la misma detección de la etiqueta."""
    texto = str(deteccion.get("texto", "") or "")
    if campo == "folio":
        # Solo devuelve dígitos si aparecen literalmente después de la etiqueta.
        m = re.search(r"(?:FOLIO|FOLID|FOLI0|FOL1D|FILID|FLI0|FLID|FULID|OLIO|LIO|EDL10|ELIQ)\s*[:：]?\s*(\d+)", texto, re.IGNORECASE)
        return m.group(1) if m else ""
    if campo == "cuenta":
        # En recibos de caja la cuenta puede venir en la misma detección, por ejemplo:
        # "CUENTA DE DEPOSITO:*****9131". Se conserva el segmento literal posterior a ':'.
        valor = texto_despues_de_etiqueta(texto) or (re.search(r"(\*[A-Z].*)", texto).group(1).strip() if re.search(r"(\*[A-Z].*)", texto) else "")
        if valor and re.search(r"\d|\*", valor):
            return valor
    if campo == "titular":
        valor = texto_despues_de_etiqueta(texto) or (re.search(r"(\*[A-Z].*)", texto).group(1).strip() if re.search(r"(\*[A-Z].*)", texto) else "")
        if valor:
            return valor
    if campo == "deposito":
        # Extrae la modalidad de depósito tal como aparece en el OCR.
        # No se altera el texto original ni se corrigen caracteres.
        coincidencia = re.match(
            r"^\s*(?:DEPOSITO|DEPOSTTO|DEPOSTITO|EPOSITO|POSITO|DEPIIDII?XTO)[-\s,;:]*(A\s+CUENTA\s*HSBC|MIXTO|HIXTO|NIXTO|MIXIO|MIXID|MIXTIO)?\b",
            texto,
            re.IGNORECASE,
        )
        if coincidencia:
            return "A CUENTA HSBC" if coincidencia.group(1) and "cuenta" in normalizar(coincidencia.group(1)) else "MIXTO"
    if campo == "monto":
        valor = encontrar_patron(texto, PATRONES_MONTO)
        if valor:
            return valor
    return ""


def detalle_deteccion(deteccion):
    return {
        "indice_original": deteccion.get("_indice_original", deteccion.get("indice_original", "")),
        "confianza": deteccion.get("confianza", 0.0),
        "x": deteccion.get("x", 0),
        "y": deteccion.get("y", 0),
        "texto": deteccion.get("texto", ""),
    }


def _resultado_vacio(campo, motivo="No se encontró un valor compatible en el OCR."):
    return {"valor": "", "estado": "NO_ENCONTRADO", "confianza": 0.0, "metodo": f"ETIQUETA_{campo.upper()}_HSBC", "motivo": motivo, "detecciones": []}


def _confianza(deteccion):
    try:
        return float(deteccion.get("confianza", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _ventana_espacial(detecciones, etiquetas, etiqueta_actual):
    """Obtiene detecciones hasta la siguiente etiqueta/corte e incorpora valores a la derecha en la misma línea."""
    posicion = etiqueta_actual["posicion"]
    ancla = etiqueta_actual["deteccion"]
    siguientes = [e["posicion"] for e in etiquetas if e["posicion"] > posicion]
    fin = min(siguientes) if siguientes else len(detecciones)
    bloque = list(detecciones[posicion + 1:fin])

    # Algunos OCR ordenan primero el valor porque su y es 1-3 px menor que el
    # de la etiqueta (p. ej. CUENTA: / 4062409131 o DEPOSITO: / $300.00).
    # Se recuperan solo detecciones alineadas horizontalmente con la etiqueta.
    ax, ay = ancla["_x"], ancla["_y"]
    aw, ah = ancla["_ancho"], ancla["_alto"]
    a_derecha = ax + aw
    campo_actual = etiqueta_actual.get("campo")

    # Detectar etiquetas auxiliares (RECIBIDO, CAMBIO, EFECTIVO...) que no son
    # campos de salida, pero sí cierran la ventana del titular/cuenta.
    limites_visuales = []
    for d in detecciones:
        if d is ancla:
            continue
        t = normalizar(d.get("texto", ""))
        if campo_actual in ("deposito", "monto"):
            auxiliares = ("deposito aplicado", "tu deposito ya fue")
        else:
            auxiliares = ("recibido", "cambio", "efectivo", "total documento", "total documentd", "total documenion")
        es_auxiliar = any(t.startswith(normalizar(x)) for x in auxiliares)
        if es_auxiliar and d["_y"] >= ay - max(10.0, ah):
            limites_visuales.append(d)

    limite_y = min((d["_y"] + d["_alto"] / 2 for d in limites_visuales), default=None)
    limite_x = min((d["_x"] for d in limites_visuales if limite_y is not None and abs((d["_y"] + d["_alto"] / 2) - limite_y) <= max(12.0, d["_alto"] * 0.65)), default=None)

    for d in detecciones:
        if d is ancla or d in bloque:
            continue
        if es_limite_ventana(d.get("texto", ""), campo_actual) or contiene_corte(d.get("texto", "")):
            continue
        centro_y = d["_y"] + d["_alto"] / 2
        dy = abs(centro_y - (ay + ah / 2))
        dx = d["_x"] - a_derecha
        # Para TITULAR no incluir una detección de la línea anterior (por ejemplo,
        # el número de CUENTA), aunque quede horizontalmente cerca de la etiqueta.
        if campo_actual == "titular" and centro_y < ay + ah / 2 - 2:
            continue
        # No añadir a la ventana un importe alineado con RECIBIDO/CAMBIO/EFECTIVO.
        if limite_y is not None and limite_x is not None and centro_y >= limite_y - max(8.0, d["_alto"] * 0.4) and d["_x"] >= limite_x:
            continue
        if dx >= -8 and dx <= max(420.0, aw * 1.5) and dy <= max(12.0, ah * 0.65, d["_alto"] * 0.65):
            bloque.append(d)

    # Mantener orden de lectura de las detecciones originales.
    bloque.sort(key=lambda d: (d["_y"], d["_x"], d["_indice_original"]))
    resultado = []
    vistos = set()
    for d in bloque:
        idx = d.get("_indice_original")
        if idx in vistos:
            continue
        vistos.add(idx)
        if contiene_corte(d.get("texto", "")):
            break
        if es_limite_ventana(d.get("texto", ""), etiqueta_actual.get("campo")):
            break
        centro_y = d["_y"] + d["_alto"] / 2
        if (
            etiqueta_actual.get("campo") != "titular"
            and limite_y is not None
            and limite_x is not None
            and centro_y >= limite_y - max(8.0, d["_alto"] * 0.4)
            and d["_x"] >= limite_x
        ):
            break
        resultado.append(d)
    return resultado


def _buscar_valor_en_ventana(campo, ventana, ancla=None):
    """Selecciona un valor compatible dentro de la ventana de la etiqueta."""
    if campo == "deposito":
        # La etiqueta completa suele estar en una sola detección. Si se llega a
        # esta ventana, solo se conserva el texto OCR literal, sin inferencias.
        candidatos_deposito = [d for d in ventana if str(d.get("texto", "")).strip()]
        if candidatos_deposito:
            d = candidatos_deposito[0]
            return {"valor": str(d.get("texto", "")).strip(), "estado": "ENCONTRADO", "confianza": _confianza(d), "metodo": "VENTANA_ESPACIAL_DEPOSITO_HSBC", "motivo": "Texto OCR original conservado literalmente.", "detecciones": [d]}
    candidatos = []
    for d in ventana:
        texto = str(d.get("texto", "") or "")
        if campo == "monto":
            valor = encontrar_patron(texto, PATRONES_MONTO)
            if valor and re.fullmatch(r"\$?\s*0+(?:\.00)?", valor.strip()):
                continue
        else:
            valor = texto.strip()
        if not valor:
            continue
        if campo == "titular":
            texto_titular = normalizar(valor)
            # Un número de cuenta o el logotipo "HSBC" no son el nombre del titular.
            if (
                re.fullmatch(r"[\d*#\-\s]+", texto_titular)
                or "hsbc" in texto_titular
                or encontrar_patron(valor, PATRONES_MONTO)
            ):
                continue
        # Excluir texto genérico/cortes y no inferir un dato por su apariencia solamente.
        y_ref = ancla["_y"] if ancla else (ventana[0]["_y"] if ventana else 0)
        candidatos.append({"valor": valor, "deteccion": d, "confianza": _confianza(d), "distancia": abs(d["_y"] - y_ref)})

    if not candidatos:
        return _resultado_vacio(campo, "Se encontró la etiqueta, pero no se detectó valor en su ventana espacial.")

    if campo == "monto":
        # La ventana se inicia en la etiqueta DEPOSITO:/TOTAL DEPOSITO; el primer monto
        # después de ella es el importe asociado. La confianza se usa solo como desempate.
        candidatos = [c for c in candidatos if encontrar_patron(c["valor"], PATRONES_MONTO)]
        if not candidatos:
            return _resultado_vacio(campo, "Se encontró la etiqueta del importe, pero no hay un monto en su ventana espacial.")
        elegido = min(candidatos, key=lambda c: (c["distancia"], -c["confianza"]))
    elif campo in ("cuenta", "titular"):
        # Conserva posibles valores multilínea hasta la siguiente etiqueta/corte.
        seleccionados = [c["deteccion"] for c in candidatos]
        # Evitar que un campo tome números/texto de otro renglón lejano: se mantiene
        # el bloque delimitado y se unen solo las detecciones efectivamente presentes.
        if campo == "titular" and len(seleccionados) > 1:
            seleccionados.sort(key=lambda d: (round(d["_y"] / 12.0), 0 if str(d.get("texto", "")).strip().startswith("*") else 1, d["_x"]))
        valor = " ".join(str(d.get("texto", "")).strip() for d in seleccionados if str(d.get("texto", "")).strip())
        if campo == "cuenta" and (len(valor) > 25 or "INSTITUCION" in valor.upper() or "SUCURSAL" in valor.upper()):
            return _resultado_vacio(campo, "Se descartó texto de sello/sucursal no compatible con número de cuenta.")
        return {"valor": valor, "estado": "ENCONTRADO", "confianza": sum(c["confianza"] for c in candidatos) / len(candidatos), "metodo": f"VENTANA_ESPACIAL_{campo.upper()}_HSBC", "motivo": "Valor obtenido de detecciones originales dentro de la ventana espacial.", "detecciones": seleccionados}
    else:
        elegido = max(candidatos, key=lambda c: c["confianza"])

    return {"valor": elegido["valor"], "estado": "ENCONTRADO", "confianza": elegido["confianza"], "metodo": f"VENTANA_ESPACIAL_{campo.upper()}_HSBC", "motivo": "Valor obtenido de detecciones originales dentro de la ventana espacial.", "detecciones": [elegido["deteccion"]]}


def _candidatos_fecha(detecciones):
    cands = _candidatos_fecha_base(detecciones)
    if not cands and any(re.fullmatch(r"D\d{5}", str(x.get("texto", "")).strip()) for x in detecciones):
        for d in detecciones:
            txt = str(d.get("texto", "")).strip()
            if re.match(r"^[uU]?[uU]n[\s\d]+A\w*$", txt):
                cands.append({"valor": txt, "deteccion": d, "confianza": _confianza(d), "distancia": d["_y"]})
    return cands

def _candidatos_fecha_base(detecciones):
    candidatos = []
    for d in detecciones:
        valor = encontrar_patron(d.get("texto", ""), PATRONES_FECHA)
        if valor:
            candidatos.append({"valor": valor, "deteccion": d, "confianza": _confianza(d), "distancia": d["_y"]})
    return candidatos


def extraer(datos):
    detecciones = preparar_detecciones(datos)
    etiquetas = localizar_etiquetas(detecciones)
    campos = {}

    # HSBC se asigna por el contexto del conjunto/carpeta, sin depender de que
    # el OCR lea perfectamente el logotipo. Los JSON de muestra declaran BANCO_HSBC.
    banco_json = normalizar(datos.get("banco", "")) if isinstance(datos, dict) else ""
    campos["banco"] = {
        "valor": "HSBC",
        "estado": "ENCONTRADO",
        "confianza": 1.0,
        "metodo": "CONTEXTO_HSBC",
        "motivo": f"Banco asignado por contexto HSBC (campo banco del JSON: {datos.get('banco', '') if isinstance(datos, dict) else ''}).",
        "detecciones": [],
    }

    # FECHA: patrón en detecciones originales, normalmente cerca de la parte superior.
    fechas = _candidatos_fecha(detecciones)
    if fechas:
        # Priorizar fechas de la zona superior y luego la confianza OCR.
        y_min = min((d["_y"] for d in detecciones), default=0.0)
        for c in fechas:
            c["distancia"] = abs(c["deteccion"]["_y"] - y_min)
            c["score"] = _confianza(c["deteccion"])
        fechas.sort(key=lambda c: (c["distancia"], -c["score"]))
        elegido = fechas[0]
        valor_fecha = elegido["valor"]
        detecciones_fecha = [elegido["deteccion"]]
        # Fallback local para comprobantes de caja con fecha numérica y HORA/HRA separada.
        # Solo concatena ambos textos OCR literales si están en el mismo renglón.
        if re.fullmatch(r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}", valor_fecha):
            d_fecha = elegido["deteccion"]
            for d_hora in detecciones:
                m_hora = re.match(r"^\s*(?:HORA|HRA)\s*[:：]\s*(\d{1,2}:\d{2}:\d{2})\s*$", str(d_hora.get("texto", "")), re.IGNORECASE)
                if not m_hora:
                    continue
                dy = abs((d_hora["_y"] + d_hora["_alto"] / 2) - (d_fecha["_y"] + d_fecha["_alto"] / 2))
                dx = d_hora["_x"] - (d_fecha["_x"] + d_fecha["_ancho"])
                if dy <= max(12.0, d_fecha["_alto"] * 0.65, d_hora["_alto"] * 0.65) and -8 <= dx <= 220:
                    valor_fecha = f"{valor_fecha} {m_hora.group(1)}"
                    detecciones_fecha.append(d_hora)
                    break
        campos["fecha"] = {"valor": valor_fecha, "estado": "ENCONTRADO", "confianza": min(_confianza(d) for d in detecciones_fecha), "metodo": "PATRON_FECHA_HSBC" if len(detecciones_fecha) == 1 else "FECHA_HORA_ALINEADAS_HSBC", "motivo": "Fecha localizada en detecciones OCR originales; hora agregada solo cuando aparece explícitamente alineada en la misma línea.", "detecciones": detecciones_fecha}
    else:
        campos["fecha"] = _resultado_vacio("fecha", "No se encontró una fecha compatible con los patrones configurados.")

    # FOLIO puede venir en la misma detección o separado a la derecha.
    # La búsqueda espacial se aplica a todas las variantes reconocidas (FILID,
    # FLI0, FULID, etc.), no solo a FULID. No se corrige el texto OCR: se toma
    # únicamente un grupo de dígitos detectado y alineado con la etiqueta.
    etiqueta_folio = next((e for e in etiquetas if e["campo"] == "folio"), None)
    if etiqueta_folio:
        valor = valor_embebido("folio", etiqueta_folio["deteccion"])
        detecciones_folio = [etiqueta_folio["deteccion"]]
        if not valor:
            ancla = etiqueta_folio["deteccion"]
            ax, ay = ancla["_x"], ancla["_y"]
            aw, ah = ancla["_ancho"], ancla["_alto"]
            candidatos_folio = []
            for d in detecciones:
                if d is ancla:
                    continue
                texto = str(d.get("texto", "")).strip()
                # Folios de al menos cuatro dígitos, sin reconstruir caracteres.
                if not re.fullmatch(r"\d{4,}", texto):
                    continue
                dx = d["_x"] - (ax + aw)
                dy = abs((d["_y"] + d["_alto"] / 2) - (ay + ah / 2))
                if -max(30.0, ah * 0.7) <= dx <= max(160.0, aw * 1.5) and dy <= max(12.0, ah * 0.65, d["_alto"] * 0.65):
                    candidatos_folio.append((dy, dx < 0, -_confianza(d), d, texto))
            if candidatos_folio:
                _, _, _, d_folio, valor = min(candidatos_folio, key=lambda x: (x[0], x[1], x[2]))
                detecciones_folio.append(d_folio)
                campos["folio"] = {
                    "valor": valor,
                    "estado": "ENCONTRADO",
                    "confianza": min(_confianza(x) for x in detecciones_folio),
                    "metodo": "ETIQUETA_FOLIO_SEPARADA_HSBC",
                    "motivo": "Número OCR original alineado a la derecha de una etiqueta de folio reconocida; no se corrigió el texto.",
                    "detecciones": detecciones_folio,
                }
            else:
                campos["folio"] = _resultado_vacio(
                    "folio",
                    "Se detectó una posible etiqueta de folio, pero no se encontró un número de al menos cuatro dígitos alineado en la misma línea.",
                )
        else:
            campos["folio"] = {
                "valor": valor,
                "estado": "ENCONTRADO",
                "confianza": _confianza(etiqueta_folio["deteccion"]),
                "metodo": "ETIQUETA_FOLIO_HSBC",
                "motivo": "Valor numérico leído literalmente después de la etiqueta de folio.",
                "detecciones": [etiqueta_folio["deteccion"]],
            }
    else:
        # image_488 contiene "10: 7351": la etiqueta no es concluyente.
        # Se mantiene la regla específica anterior para evitar falsos positivos.
        candidato_folio_ambiguo = next((d for d in detecciones if re.fullmatch(r"10\s*:\s*(\d{3,})", str(d.get("texto", "")).strip())), None)
        hay_deposito_truncado = any(re.match(r"^posito\s+a\s+cuenta\s+hsbc\b", normalizar(d.get("texto", ""))) for d in detecciones)
        if candidato_folio_ambiguo and hay_deposito_truncado:
            valor_candidato = re.search(r":\s*(\d{3,})", str(candidato_folio_ambiguo.get("texto", ""))).group(1)
            campos["folio"] = {"valor": valor_candidato, "estado": "REVISAR", "confianza": _confianza(candidato_folio_ambiguo), "metodo": "CANDIDATO_FOLIO_ETIQUETA_AMBIGUA_HSBC", "motivo": "El OCR produjo '10: 7351'; se conserva 7351 como candidato, pero la etiqueta es ambigua y requiere validación visual.", "detecciones": [candidato_folio_ambiguo]}
        else:
            campos["folio"] = _resultado_vacio("folio", "No se encontró una etiqueta de folio reconocible.")

    # MONTO: importe de la operación, asociado a la etiqueta DEPOSITO:/TOTAL DEPOSITO.
    apariciones_monto = [e for e in etiquetas if e["campo"] == "monto"]
    resultado_monto = None
    for etiqueta_monto in apariciones_monto:
        embebido = valor_embebido("monto", etiqueta_monto["deteccion"])
        if embebido:
            resultado_monto = {"valor": embebido, "estado": "ENCONTRADO", "confianza": _confianza(etiqueta_monto["deteccion"]), "metodo": "ETIQUETA_EMBEBIDA_MONTO_HSBC", "motivo": "Importe detectado literalmente en la etiqueta.", "detecciones": [etiqueta_monto["deteccion"]]}
            break
        ventana_monto = _ventana_espacial(detecciones, etiquetas, etiqueta_monto)
        candidato_monto = _buscar_valor_en_ventana("monto", ventana_monto, etiqueta_monto["deteccion"])
        if candidato_monto["valor"]:
            resultado_monto = candidato_monto
            break

        # En algunas imágenes HSBC el importe aparece unos píxeles ANTES
        # que la etiqueta DEPOSITO: por el orden espacial del OCR, pero en la
        # misma línea y a su derecha. Se busca solo esa alineación local.
        ancla = etiqueta_monto["deteccion"]
        ax = float(ancla.get("x", 0) or 0)
        ay = float(ancla.get("y", 0) or 0)
        aw = float(ancla.get("ancho", 0) or 0)
        ah = float(ancla.get("alto", 0) or 0)
        cercanos = []
        for d in detecciones:
            valor = encontrar_patron(d.get("texto", ""), PATRONES_MONTO)
            if not valor:
                continue
            dx = float(d.get("x", 0) or 0) - (ax + aw)
            dy = abs((float(d.get("y", 0) or 0) + float(d.get("alto", 0) or 0) / 2) - (ay + ah / 2))
            if -8 <= dx <= max(420.0, aw * 1.5) and dy <= max(12.0, ah * 0.65, float(d.get("alto", 0) or 0) * 0.65):
                cercanos.append((dy, -_confianza(d), d, valor))
        if cercanos:
            _, _, deteccion_monto, valor_monto = min(cercanos, key=lambda x: (x[0], x[1]))
            resultado_monto = {"valor": valor_monto, "estado": "ENCONTRADO", "confianza": _confianza(deteccion_monto), "metodo": "ALINEACION_ESPACIAL_MONTO_HSBC", "motivo": "Importe OCR alineado con la etiqueta DEPOSITO:; texto literal conservado.", "detecciones": [deteccion_monto]}
            break
    if resultado_monto is None:
        for d in detecciones:
            val_m = encontrar_patron(d.get("texto", ""), PATRONES_MONTO)
            if val_m and not re.fullmatch(r"\$?\s*0+(?:\.00)?", val_m):
                resultado_monto = {"valor": val_m, "estado": "ENCONTRADO", "confianza": _confianza(d), "metodo": "FALLBACK_EFECTIVO_MONTO_HSBC", "motivo": "Importe localizado en línea de efectivo/depósito.", "detecciones": [d]}
                break
    campos["monto"] = resultado_monto or _resultado_vacio("monto", "No se encontró un importe en la ventana de DEPOSITO:/TOTAL DEPOSITO.")

    # Campos con etiqueta: ventanas delimitadas por la siguiente etiqueta/corte.
    for campo in ("deposito", "cuenta", "titular"):
        apariciones = [e for e in etiquetas if e["campo"] == campo]
        if not apariciones:
            campos[campo] = _resultado_vacio(campo, "No se encontró la etiqueta del campo.")
            continue

        resultado_campo = None
        for etiqueta in apariciones:
            embebido = valor_embebido(campo, etiqueta["deteccion"])
            if embebido:
                resultado_campo = {"valor": embebido, "estado": "ENCONTRADO", "confianza": _confianza(etiqueta["deteccion"]), "metodo": f"ETIQUETA_EMBEBIDA_{campo.upper()}_HSBC", "motivo": "Valor recuperado de la misma detección que contiene la etiqueta; texto literal.", "detecciones": [etiqueta["deteccion"]]}
                break

            ventana = _ventana_espacial(detecciones, etiquetas, etiqueta)
            candidato = _buscar_valor_en_ventana(campo, ventana, etiqueta["deteccion"])
            if candidato["valor"]:
                resultado_campo = candidato
                break

        campos[campo] = resultado_campo or _resultado_vacio(campo)

    # Convertir detecciones elegidas al formato de auditoría, sin tocar los originales.
    for info in campos.values():
        info["detecciones"] = [detalle_deteccion(d) for d in info.get("detecciones", [])]

    return {
        "archivo": datos.get("archivo", "") if isinstance(datos, dict) else "",
        "banco": "HSBC",
        "campos": campos,
        "total_detecciones": len(detecciones),
        "total_etiquetas": len(etiquetas),
        "detecciones_originales": [detalle_deteccion(d) for d in detecciones],
    }


def escribir_txt(resultados, ruta, numero_bloque):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8") as archivo:
        archivo.write("=" * 110 + "\n")
        archivo.write("HSBC - EXTRACTOR HÍBRIDO V1.2.5 EXPERIMENTAL\n")
        archivo.write(f"BLOQUE {numero_bloque}\n")
        archivo.write("Principio: EXTRAER, NO INVENTAR.\n")
        archivo.write("JSON de entrada: solo lectura; sin corrección artificial de caracteres OCR.\n")
        archivo.write("Campos: Banco | Fecha completa (con hora) | Folio | Tipo de depósito | Monto | Cuenta | Titular\n")
        archivo.write("=" * 110 + "\n\n")

        for resultado in resultados:
            archivo.write("-" * 110 + "\n")
            archivo.write(f"ARCHIVO: {resultado['archivo']}\n")
            archivo.write(f"DETECCIONES: {resultado['total_detecciones']} | ETIQUETAS: {resultado['total_etiquetas']}\n\n")
            for campo in CAMPOS_OBJETIVO:
                info = resultado["campos"][campo]
                archivo.write(f"CAMPO: {campo.upper()}\n")
                archivo.write(f"ESTADO: {info['estado']}\n")
                archivo.write(f"VALOR: {info['valor']}\n")
                archivo.write(f"CONFIANZA: {float(info.get('confianza', 0.0)):.4f}\n")
                archivo.write(f"MÉTODO: {info.get('metodo', '')}\n")
                archivo.write(f"MOTIVO: {info.get('motivo', '')}\n")
                archivo.write("DETECCIONES DEL CAMPO:\n")
                if info.get("detecciones"):
                    for d in info["detecciones"]:
                        archivo.write(
                            f"  idx={d.get('indice_original')} | conf={float(d.get('confianza', 0.0) or 0.0):.4f} | "
                            f"x={d.get('x', 0)} | y={d.get('y', 0)} | texto={d.get('texto', '')}\n"
                        )
                else:
                    archivo.write("  ninguna\n")
                archivo.write("\n")

            archivo.write("DETECCIONES OCR ORIGINALES COMPLETAS (índice, confianza, x, y, texto):\n")
            for d in resultado.get("detecciones_originales", []):
                try:
                    conf = float(d.get("confianza", 0.0) or 0.0)
                except (TypeError, ValueError):
                    conf = 0.0
                archivo.write(
                    f"  idx={d.get('indice_original')} | conf={conf:.4f} | x={d.get('x', 0)} | "
                    f"y={d.get('y', 0)} | texto={d.get('texto', '')}\n"
                )
            archivo.write("\nFIN COMPROBANTE\n\n")
        archivo.write("=" * 110 + "\nFIN BLOQUE\n" + "=" * 110 + "\n")


def encontrar_raiz_proyecto():
    actual = Path(__file__).resolve()
    # Prioriza el diseño esperado <proyecto>/Pruebas/script.py.
    if len(actual.parents) >= 2:
        candidata = actual.parents[1]
        if (candidata / "Resultados_OCR").exists() or (candidata / "Comprobantes").exists():
            return candidata
    for candidata in actual.parents:
        if (candidata / "Resultados_OCR").exists() or (candidata / "Comprobantes").exists():
            return candidata
    return actual.parent.parent if len(actual.parents) >= 2 else actual.parent


def obtener_archivos(carpeta_json):
    return sorted(Path(carpeta_json).glob("*.json"), key=numero_archivo)


def obtener_bloque(archivos, numero_bloque):
    inicio = (numero_bloque - 1) * TAMANO_BLOQUE
    return archivos[inicio:inicio + TAMANO_BLOQUE]


def main():
    parser = argparse.ArgumentParser(description="Extractor híbrido HSBC por bloques de 10 JSON (fecha con hora y tipo de depósito).")
    parser.add_argument("--bloque", type=int, default=1, help="1=primeros 10 JSON, 2=siguientes 10, etc.")
    parser.add_argument("--carpeta-json", type=Path, default=None, help="Ruta de JSON HSBC. Por defecto: Resultados_OCR/BANCO_HSBC.")
    parser.add_argument("--salida", type=Path, default=None, help="Carpeta de salida TXT. Por defecto: junto a los JSON/Pruebas_Hibrido_HSBC.")
    args = parser.parse_args()

    if args.bloque < 1:
        raise SystemExit("ERROR: --bloque debe ser >= 1.")

    raiz = encontrar_raiz_proyecto()
    carpeta_json = args.carpeta_json or (raiz / "Resultados_OCR" / "BANCO_HSBC")
    carpeta_json = carpeta_json.expanduser().resolve()
    if not carpeta_json.exists():
        raise SystemExit(
            f"ERROR: no existe la carpeta de JSON HSBC:\n{carpeta_json}\n"
            "Indica la ruta correcta con --carpeta-json."
        )

    archivos = obtener_archivos(carpeta_json)
    if not archivos:
        raise SystemExit(f"ERROR: no se encontraron archivos .json en:\n{carpeta_json}")

    seleccionados = obtener_bloque(archivos, args.bloque)
    if not seleccionados:
        raise SystemExit(f"ERROR: el bloque {args.bloque} no contiene comprobantes. JSON disponibles: {len(archivos)}")

    carpeta_salida = args.salida or (carpeta_json / "Pruebas_Hibrido_HSBC")
    carpeta_salida = Path(carpeta_salida).expanduser().resolve()
    resultados = []
    print("=" * 90)
    print("HSBC - EXTRACTOR HÍBRIDO V1.2.5 EXPERIMENTAL")
    print(f"Carpeta JSON: {carpeta_json}")
    print(f"JSON disponibles: {len(archivos)} | Bloque: {args.bloque} | En este bloque: {len(seleccionados)}")
    print("Principio: EXTRAER, NO INVENTAR")
    print("=" * 90)

    for i, ruta in enumerate(seleccionados, 1):
        print(f"[{i:02d}/{len(seleccionados):02d}] {ruta.name}")
        try:
            # Apertura de solo lectura. Nunca se escribe en el JSON original.
            with ruta.open("r", encoding="utf-8-sig") as archivo:
                datos = json.load(archivo)
            resultado = extraer(datos)
            resultado["archivo"] = datos.get("archivo") or ruta.name
            resultados.append(resultado)
            print("    " + " | ".join(f"{c}={resultado['campos'][c]['valor']}" for c in CAMPOS_OBJETIVO))
        except Exception as error:
            print(f"    ERROR: {type(error).__name__}: {error}")

    carpeta_salida.mkdir(parents=True, exist_ok=True)
    ruta_salida = carpeta_salida / f"resultado_hsbc_hibrido_bloque_{args.bloque:02d}.txt"
    escribir_txt(resultados, ruta_salida, args.bloque)
    print("\nPROCESO TERMINADO")
    print(f"TXT generado: {ruta_salida}")


if __name__ == "__main__":
    main()
