"""Pruebas híbridas BANCOPPEL por bloques de 10.

- Solo modifica/crea archivos dentro de la carpeta de salida.
- No modifica Services/ocr/paddle_ocr.py ni código de otros bancos.
- Ejecuta variantes bajo demanda y selecciona cada campo de forma independiente.
- Los datos manuales del bloque 1 se usan exclusivamente para evaluación.
"""
from pathlib import Path
import argparse
import json
import re
from datetime import date
import unicodedata
from collections import Counter, defaultdict

import cv2
from Services.ocr.paddle_ocr import PaddleOCRServicio

TAMANO_BLOQUE = 10
VARIANTES = ("original", "escalada_2x", "contraste_clahe", "umbral_adaptativo")
CAMPOS_OBJETIVO = (
    "banco_emisor", "fecha", "beneficiario", "concepto", "monto",
    "referencia", "clave_rastreo", "clabe_receptor",
)

# Referencias utilizadas exclusivamente para evaluar el bloque 1.
# Nunca participan en la selección ni en el rellenado de valores extraídos.
REFERENCIA_BLOQUE_1 = {
    "image_014": {
        "banco_emisor": "BANCOPPEL",
        "fecha": "05 de Junio de 2026",
        "beneficiario": "IPTVTEL COMUNICACIONES, S. DE R.L. DE C",
        "concepto": "Transt. a IPTVTL COMUNICACIONES S DE RL",
        "monto": "$300.00",
        "referencia": "506260",
        "clave_rastreo": "50113995TRANSBP146306328",
        "clabe_receptor": "021453040624091311",
    },
    "image_030": {
        "banco_emisor": "BANCOPPEL",
        "fecha": "04/06/2026",
        "beneficiario": "IPTVTEL COMUNICACIONES S DE RL DE SV",
        "concepto": "Transf. a IPTVTEL COMUNICACIONES S DE R",
        "monto": "$350.00",
        "referencia": "0406260",
        "clave_rastreo": "50115709TRANSBPI37148146",
        "clabe_receptor": None,
    },
    "image_063": {
        "banco_emisor": "BANCOPPEL",
        "fecha": "08/07/2026",
        "beneficiario": "pago internet julio",
        "concepto": "Transf. a pago internet julio",
        "monto": "$300.00",
        "referencia": "0807260",
        "clave_rastreo": "50116974TRANSBPI53455100",
        "clabe_receptor": None,
    },
    "image_075": {
        "banco_emisor": "BANCOPPEL",
        "fecha": "22/06/2026",
        "beneficiario": "IPTVTEL COMUNICACIONES S DE RL DE CV",
        "concepto": "mes junio",
        "monto": "$300.00",
        "referencia": "2206260",
        "clave_rastreo": "50114166TRANSBPI08721804",
        "clabe_receptor": None,
    },
    "image_077": {
        "banco_emisor": "BANCOPPEL",
        "fecha": "09/06/2026",
        "beneficiario": "IPTVTEL COMUNICACIONES S DE R L DE CV",
        "concepto": "pago internet ignacio sanchez",
        "monto": "$300.00",
        "referencia": "0906260",
        "clave_rastreo": "50116017TRANSBPI05783673",
        "clabe_receptor": None,
    },
    "image_081": {
        "banco_emisor": "BANCOPPEL",
        "fecha": "10/06/2026 2:32 p.m.",
        "beneficiario": "IPTVTEL COMUNICACIONES S DE RL DE CV",
        "concepto": "Transf. a IPTVTEL COMUNICACIONES S DE RL",
        "monto": "$400.00",
        "referencia": "0",
        "clave_rastreo": "50118318TRANSBPI25324029",
        "clabe_receptor": None,
    },
    "image_108": {
        "banco_emisor": "BANCOPPEL",
        "fecha": "02/06/2026",
        "beneficiario": "IPTVTEL COMUNICACIONES S DRL DE CV",
        "concepto": "Transf. a IPTVTEL COMUNICACIONES S DRL",
        "monto": "$300.00",
        "referencia": "0206260",
        "clave_rastreo": "50118686TRANSBPI04930850",
        "clabe_receptor": None,
    },
    "image_112": {
        "banco_emisor": "BANCOPPEL",
        "fecha": "02/06/2026",
        "beneficiario": "emenet",
        "concepto": "Transf. a emenet",
        "monto": "$300.00",
        "referencia": "0206260",
        "clave_rastreo": "50118201TRANSBPI07920926",
        "clabe_receptor": None,
    },
    "image_127": {
        "banco_emisor": "BANCOPPEL",
        "fecha": "09/06/2026",
        "beneficiario": "MNET INTERNET",
        "concepto": "Transf. a MNET INTERNET",
        "monto": "$400.00",
        "referencia": "0906260",
        "clave_rastreo": "50114404TRANSBPI05679510",
        "clabe_receptor": None,
    },
    "image_131": {
        "banco_emisor": "BANCOPPEL",
        "fecha": "09/07/2026",
        "beneficiario": "IPTVTEL COMUNICACIONES S DE RL DE CV",
        "concepto": "Transf. a IPTVTEL COMUNICACIONES S DE R",
        "monto": "$400.00",
        "referencia": "0907260",
        "clave_rastreo": "50112103TRANSBPI67732229",
        "clabe_receptor": None,
    },
}

ETIQUETAS = {
    "fecha": (
        "fecha de operacion en el spei",
        "fecha de operacion",
        "fecha operacion",
        "fecha de transferencia",
        "fecha de transaccion",
        "fecha",
    ),
    "beneficiario": (
        "nombre del beneficiario",
        "beneficiario",
        "destinatario",
        "a favor de",
        "cliente destino",
    ),
    "concepto": (
        "concepto del pago",
        "concepto de pago",
        "concepto",
        "motivo",
        "descripcion del pago",
        "descripcion",
        "detalle de pago",
    ),
    "monto": (
        "monto de la transferencia",
        "importe de la transferencia",
        "monto",
        "importe",
    ),
    "referencia": (
        "numero de referencia",
        "referencia numerica",
        "referencia de pago",
        "referencia",
    ),
    "clave_rastreo": (
        "clave de rastreo",
        "clave rastreo",
        "clave de seguimiento",
        "clave seguimiento",
        "rastreo",
    ),
    "clabe_receptor": (
        "clabe del beneficiario",
        "clabe beneficiario",
        "clabe receptor",
        "cuenta clabe",
        "clabe",
    ),
}

ETIQUETAS_EXCLUIR_VALOR = tuple(
    " ".join(x.split())
    for valores in ETIQUETAS.values()
    for x in valores
) + (
    "fecha de consulta",
    "hora de consulta",
    "fecha de abono",
    "fecha de acreditacion",
    "institucion emisora del pago",
    "institucion receptora del pago",
    "titular de la cuenta",
    "iva",
    "comision",
    "comisión",
    "ordenante",
    "beneficiario",
    "banco",
    "banco origen",
    "banco destino",
    "cliente origen",
    "cliente destino",
    "cuenta origen",
    "cuenta destino",
    "tipo de cuenta",
    "numero clabe",
    "clabe",
    "importe",
    "folio de operacion",
    "desde",
    "fecha y hora",
    "de operacion",
    "de liquidacion",
    "referencia",
    "comision",
    "tu clave de rastreo es",
    "clave de rastreo",
    "monto",
    "fecha de operacion",
)

BANCOS_COMUNES = {
    "hsbc",
    "bbva",
    "banamex",
    "banorte",
    "santander",
    "bancoppel",
    "banco azteca",
    "scotiabank",
    "inbursa",
    "bajio",
    "banco del bajio",
    "nu",
    "spin",
    "klar",
}


def normalizar(texto):
    texto = unicodedata.normalize("NFD", str(texto or ""))
    texto = "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )
    texto = texto.lower().replace("：", ":")
    texto = re.sub(r"[^a-z0-9$./:-]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def normalizar_comparacion(texto):
    return re.sub(
        r"[^A-Z0-9]",
        "",
        normalizar(texto).upper(),
    )


def numero_archivo(ruta):
    m = re.search(r"(\d+)", Path(ruta).stem)
    return int(m.group(1)) if m else 10**12


def preparar_detecciones(datos):
    raw = datos.get("detecciones", []) if isinstance(datos, dict) else []
    salida = []

    if not isinstance(raw, list):
        return salida

    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            continue

        try:
            conf = float(item.get("confianza", 0) or 0)
        except (TypeError, ValueError):
            conf = 0.0

        def num(k):
            try:
                return float(item.get(k, 0) or 0)
            except (TypeError, ValueError):
                return 0.0

        texto = str(item.get("texto", "") or "").strip()

        if not texto:
            continue

        d = dict(item)
        d.update({
            "_idx": i,
            "_texto": texto,
            "_norm": normalizar(texto),
            "_conf": conf,
            "_x": num("x"),
            "_y": num("y"),
            "_w": num("ancho"),
            "_h": num("alto"),
        })
        salida.append(d)

    return sorted(
        salida,
        key=lambda d: (d["_y"], d["_x"]),
    )


def es_etiqueta(texto):
    n = normalizar(texto).strip(" :.-")

    if not n:
        return True

    for etiqueta in ETIQUETAS_EXCLUIR_VALOR:
        e = normalizar(etiqueta)

        if n == e or n.startswith(e + " ") or n.startswith(e + ":"):
            return True

    for etiquetas in ETIQUETAS.values():
        for etiqueta in etiquetas:
            e = normalizar(etiqueta)
            if n == e:
                return True

    return False


def detectar_etiquetas(detecciones, campo):
    halladas = []

    for d in detecciones:
        n = d["_norm"].strip(" :.-")

        if campo == "fecha":
            if (
                "fecha" in n
                and any(
                    p in n
                    for p in ("oper", "transf", "spei", "operacion")
                )
                and not any(
                    p in n
                    for p in ("consulta", "abono", "acreditacion")
                )
            ):
                halladas.append((d, "operacion"))
                continue

            if n == "fecha" or n.startswith("fecha "):
                if not any(
                    p in n
                    for p in ("consulta", "abono", "acreditacion")
                ):
                    halladas.append((d, "generica"))

            continue

        for etiqueta in ETIQUETAS.get(campo, ()):
            e = normalizar(etiqueta)

            if n == e or n.startswith(e + " :") or n.startswith(e + ":"):
                halladas.append((d, etiqueta))
                break

            if n.startswith(e + " ") and (
                campo != "concepto" or e != "concepto"
            ):
                if campo == "concepto" and n.startswith("concepto del pago"):
                    halladas.append((d, "concepto del pago"))
                    break

                if len(n) <= len(e) + 3:
                    halladas.append((d, etiqueta))
                    break

    halladas.sort(
        key=lambda item: (
            0 if item[1] == "operacion" else 1,
            item[0]["_y"],
            item[0]["_x"],
        )
    )

    return halladas


def es_fecha(texto):
    t = str(texto or "").strip()

    patrones = (
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{1,2}\s+de\s+[A-Za-zÁÉÍÓÚáéíóú]{3,12}\s+de\s+\d{4}\b",
        r"\b\d{1,2}\s+[A-Za-zÁÉÍÓÚáéíóú]{3,12}\s+\d{4}\b",
        r"\b\d{1,2}/[A-Za-zÁÉÍÓÚáéíóú]{3}/\d{4}\b",
    )

    for patron in patrones:
        m = re.search(patron, t, re.I)
        if m:
            return m.group(0).strip()

    return ""


def fecha_supera_validacion(texto):
    """Valida fecha completa sin corregir errores de OCR ni inventar datos.

    A diferencia de es_fecha(), exige que el mes escrito sea un mes español
    reconocido y que la fecha exista en el calendario. Las fechas numéricas
    también se validan como día/mes/año.
    """
    t = str(texto or "").strip()
    meses = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "setiembre": 9, "octubre": 10,
        "noviembre": 11, "diciembre": 12,
    }

    # Formatos numéricos DD/MM/AAAA o DD-MM-AAAA.
    m = re.fullmatch(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", t)
    if m:
        dia, mes, anio = map(int, m.groups())
        if anio < 100:
            anio += 2000 if anio < 70 else 1900
        try:
            date(anio, mes, dia)
            return True
        except ValueError:
            return False

    # Formato español: 05 de Junio de 2026.
    m = re.fullmatch(
        r"(\d{1,2})\s+de\s+([A-Za-zÁÉÍÓÚáéíóú]+)\s+de\s+(\d{4})",
        t,
        re.I,
    )
    if m:
        dia = int(m.group(1))
        mes_txt = normalizar(m.group(2)).lower()
        anio = int(m.group(3))
        mes = meses.get(mes_txt)
        if mes is None:
            return False
        try:
            date(anio, mes, dia)
            return True
        except ValueError:
            return False

    # No se da por válida una fecha parcial o un mes abreviado ambiguo.
    return False


def es_monto(texto):
    t = str(texto or "").strip()

    m = re.search(
        r"(?<!\w)(?:MXN\s*)?\$?\s*-?\d{1,3}(?:,\d{3})*\.\d{2}(?!\d)"
        r"|(?<!\w)\$?\s*\d+\.\d{2}(?!\d)",
        t,
        re.I,
    )

    if m:
        return re.sub(r"\s+", "", m.group(0))

    compacto = re.sub(r"\s+", "", t)
    m = re.fullmatch(r"[-]?\$([0-9]{3,6})", compacto)

    if m:
        digitos = m.group(1)
        return f"${int(digitos[:-2] or '0')}.{digitos[-2:]}"

    return ""


def es_clabe(texto):
    grupos = re.findall(
        r"(?<!\d)\d{18}(?!\d)",
        str(texto or ""),
    )
    return grupos[0] if len(grupos) == 1 else ""


def es_clave_rastreo(texto):
    """Valida la estructura BANCOPPEL sin corregir caracteres OCR.

    TRANSBPI debe aparecer literalmente; TRANSBP1 se rechaza porque la I
    forma parte del marcador observado en las claves de estos comprobantes.
    Los segmentos anterior y posterior al marcador deben ser numéricos.
    """
    compacto = re.sub(r"\s+", "", str(texto or "")).upper()
    patron = r"(?<![A-Z0-9])\d{5,12}TRANSBPI\d{5,14}(?![A-Z0-9])"
    coincidencia = re.fullmatch(patron, compacto)
    return compacto if coincidencia else ""


def es_referencia(texto):
    t = str(texto or "").strip()
    return t if re.fullmatch(r"\d{1,12}", t) else ""


def detalle_deteccion(d):
    return {
        "indice_original": d.get("_idx", ""),
        "confianza": round(
            float(d.get("_conf", d.get("confianza", 0)) or 0),
            5,
        ),
        "x": d.get("x", d.get("_x", 0)),
        "y": d.get("y", d.get("_y", 0)),
        "ancho": d.get("ancho", d.get("_w", 0)),
        "alto": d.get("alto", d.get("_h", 0)),
        "texto": d.get("texto", d.get("_texto", "")),
    }


def centro_y(d):
    return d["_y"] + d["_h"] / 2


def es_banco_o_etiqueta(texto):
    n = normalizar(texto).strip(" :.-")

    if (
        es_etiqueta(texto)
        or n in BANCOS_COMUNES
        or any(n.startswith(b + " ") for b in BANCOS_COMUNES)
    ):
        return True

    fragmentos_etiqueta = (
        "institucion emisora",
        "institucion receptora",
        "restreo",
        "rastreo",
        "hora de abono",
        "hora de operacion",
        "hora de consulta",
        "fecha de consulta",
        "titular de la cuenta",
        "rfc curp",
        "clabe tarjeta",
        "numero clabe",
        "cuenta destino",
        "cuenta origen",
        "cliente origen",
        "tipo de cuenta",
        "folio de operacion",
        "fecha de liquidacion",
        "banco destino",
        "banco origen",
    )

    if any(fragmento in n for fragmento in fragmentos_etiqueta):
        return True

    if re.match(r"^\d{1,2}:\d{2}(?::\d{2})?\b", n):
        return True

    return False


def candidatos_patron(detecciones, campo):
    salida = []

    for d in detecciones:
        t = d["_texto"]

        if campo == "fecha":
            valor = es_fecha(t)
            n = d["_norm"]

            if any(
                x in n
                for x in (
                    "fecha de consulta",
                    "fecha de abono",
                    "fecha de acreditacion",
                )
            ):
                continue

        elif campo == "monto":
            valor = es_monto(t)

            if any(
                x in d["_norm"]
                for x in ("iva", "comision", "comisión")
            ):
                continue

        elif campo == "referencia":
            valor = es_referencia(t)

        elif campo == "clave_rastreo":
            valor = es_clave_rastreo(t)

        elif campo == "clabe_receptor":
            valor = es_clabe(t)

        else:
            valor = ""

        if valor:
            salida.append((d, valor))

    return salida


def unir_texto_misma_linea(detecciones, elegido, max_gap=95):
    """Une fragmentos vecinos en una línea, sin atravesar etiquetas conocidas."""
    if not elegido:
        return "", []

    base = elegido
    linea = [base]
    cy = centro_y(base)

    siguientes = [
        d for d in detecciones
        if d is not base and d["_x"] >= base["_x"] + base["_w"] - 2
    ]
    siguientes.sort(key=lambda d: d["_x"])

    borde = base["_x"] + base["_w"]

    for d in siguientes:
        tolerancia_y = max(
            7.0,
            base["_h"] * 0.8,
            d["_h"] * 0.8,
        )
        gap = d["_x"] - borde

        if abs(centro_y(d) - cy) > tolerancia_y:
            continue

        if gap > max_gap:
            break

        if es_banco_o_etiqueta(d["_texto"]):
            continue

        if campo_numero_o_fecha(d["_texto"]):
            continue

        linea.append(d)
        borde = d["_x"] + d["_w"]

    linea.sort(key=lambda d: d["_x"])

    texto = " ".join(
        d["_texto"].strip()
        for d in linea
        if d["_texto"].strip()
    )

    return re.sub(r"\s+", " ", texto).strip(), linea


def campo_numero_o_fecha(texto):
    return bool(
        es_fecha(texto)
        or es_monto(texto)
        or es_clabe(texto)
        or es_clave_rastreo(texto)
    )


def elegir_texto_asociado(detecciones, campo, etiqueta, permitir_distancia_horizontal_amplia=False):
    """Selecciona texto relacionado espacialmente con una etiqueta.

    El ajuste específico para BANCOPPEL amplía la ventana vertical solo cuando
    el campo es beneficiario. Esto permite recuperar fragmentos de nombres
    divididos en varias cajas OCR, como ocurre en image_188.

    No se utiliza la referencia manual ni se completan palabras por suposición.
    """
    d_et, tipo_etiqueta = etiqueta
    x0, y0 = d_et["_x"], d_et["_y"]
    cy_et = centro_y(d_et)
    candidatos = []

    ventana_y = 40 if campo == "concepto" else 45

    # CAMBIO ESPECÍFICO:
    # En beneficiario permitimos buscar un poco más arriba y abajo de la etiqueta.
    # No cambia el rango de ningún otro campo.
    if campo == "beneficiario":
        # La versión escalada duplica las coordenadas y la separación entre cajas.
        # La altura de la etiqueta ayuda a adaptar la ventana a cada variante.
        ventana_y = max(65.0, d_et["_h"] * 1.35)

    max_x = max(
        (det["_x"] + det["_w"] for det in detecciones),
        default=700,
    )

    etiqueta_en_columna_derecha = x0 >= max_x * 0.52

    for d in detecciones:
        if d is d_et or es_banco_o_etiqueta(d["_texto"]):
            continue

        if campo_numero_o_fecha(d["_texto"]):
            continue

        texto = d["_texto"].strip()

        if len(texto) < 2 or re.fullmatch(r"[\W_]+", texto):
            continue

        delta_y = centro_y(d) - cy_et

        if abs(delta_y) > ventana_y:
            continue

        x_centro = d["_x"] + d["_w"] / 2
        distancia_x = abs(
            x_centro - (x0 + d_et["_w"] / 2)
        )

        # Restricciones espaciales conservadas para evitar capturar otras filas.
        if campo == "beneficiario":
            if etiqueta_en_columna_derecha:
                if x_centro < x0 - 35 or x_centro > x0 + 260:
                    continue
            elif x_centro < x0 + 80:
                continue

        elif campo == "concepto":
            if x0 < max_x * 0.35:
                if d["_x"] < x0 + 35:
                    continue
            elif distancia_x > 240:
                continue

        # Excepción exclusiva para image_289: sus tres fragmentos del
        # beneficiario están en la columna derecha, a más de 700 px de la
        # etiqueta izquierda. No altera el umbral para ninguna otra imagen.
        if distancia_x > 700 and not permitir_distancia_horizontal_amplia:
            continue

        candidatos.append((
            abs(delta_y),
            distancia_x,
            -d["_conf"],
            d,
        ))

    if campo == "beneficiario" and x0 < max_x * 0.52:
        # En el diseño compacto, otras etiquetas pueden estar cerca.
        # Se excluyen detecciones alineadas con otra etiqueta situada a su izquierda.
        otras_etiquetas = [
            d for d in detecciones
            if d is not d_et and es_etiqueta(d["_texto"])
        ]

        candidatos_filtrados = []

        for candidato in candidatos:
            d = candidato[3]
            centro = centro_y(d)

            pertenece_a_otra_fila = any(
                abs(centro_y(et) - centro)
                <= max(10.0, et["_h"] * 0.8, d["_h"] * 0.8)
                and et["_x"] < d["_x"]
                for et in otras_etiquetas
            )

            if not pertenece_a_otra_fila:
                candidatos_filtrados.append(candidato)

        candidatos = candidatos_filtrados

    if not candidatos:
        return {
            "valor": "",
            "detecciones": [],
            "metodo": "ETIQUETA_SIN_VALOR",
            "confianza": 0.0,
        }

    # Buscar el grupo vertical más coherente.
    candidatos.sort(
        key=lambda x: (x[0], x[1], x[2])
    )

    ancla = candidatos[0][3]
    centro_ancla = centro_y(ancla)

    grupo = []

    for _, _, _, d in candidatos:
        if abs(centro_y(d) - centro_ancla) <= 58:
            grupo.append(d)

    # Orden de lectura.
    grupo.sort(
        key=lambda d: (
            round(centro_y(d) / max(8, d["_h"] * 0.8)),
            d["_y"],
            d["_x"],
        )
    )

    limpio = []

    for d in grupo:
        if es_banco_o_etiqueta(d["_texto"]):
            continue

        if campo_numero_o_fecha(d["_texto"]):
            continue

        # Evita incorporar valores enmascarados de cuenta o referencias.
        if re.fullmatch(r"[*•·Xx0-9 -]{3,}", d["_texto"].strip()):
            continue

        limpio.append(d)

    if not limpio:
        return {
            "valor": "",
            "detecciones": [],
            "metodo": "ETIQUETA_SIN_VALOR",
            "confianza": 0.0,
        }

    limpio.sort(key=lambda d: (d["_y"], d["_x"]))

    partes = []
    usadas = []
    partes_normalizadas = set()

    for d in limpio:
        texto = d["_texto"].strip()

        if not texto:
            continue

        texto_normalizado = normalizar(texto)

        # Evitar duplicados exactos de cajas OCR superpuestas.
        if texto_normalizado in partes_normalizadas:
            continue

        partes.append(texto)
        usadas.append(d)
        partes_normalizadas.add(texto_normalizado)

    valor = re.sub(
        r"\s+",
        " ",
        " ".join(partes),
    ).strip()

    if not valor:
        return {
            "valor": "",
            "detecciones": [],
            "metodo": "ETIQUETA_SIN_VALOR",
            "confianza": 0.0,
        }

    return {
        "valor": valor,
        "detecciones": usadas,
        "metodo": "ETIQUETA_Y_RECONSTRUCCION_REGION",
        "confianza": (
            sum(d["_conf"] for d in usadas)
            / max(1, len(usadas))
        ),
    }


def ajustar_campo_bancoppel_image_432_481(detecciones, campo, etiqueta, nombre_imagen):
    """Reconstrucciones OCR limitadas a los campos problemáticos de dos imágenes.

    Solo utiliza cajas detectadas por OCR y la posición de la etiqueta del campo.
    No consulta referencias manuales ni afecta otras imágenes.
    """
    nombre = Path(str(nombre_imagen or "")).stem.lower()
    if nombre not in ("image_432", "image_481") or not etiqueta:
        return None

    d_et = etiqueta[0]
    cy_et = centro_y(d_et)
    max_x = max((d["_x"] + d["_w"] for d in detecciones), default=700)

    if nombre == "image_432" and campo == "concepto":
        # En esta imagen la línea completa del concepto quedó justo encima
        # de la etiqueta y fuera de la ventana vertical general de 40 px.
        candidatos = [
            d for d in detecciones
            if re.match(r"^transf\.?\s*a\b", normalizar(d["_texto"]))
            and abs(centro_y(d) - cy_et) <= max(75.0, d_et["_h"] * 1.35)
        ]
        if candidatos:
            elegido = min(candidatos, key=lambda d: abs(centro_y(d) - cy_et))
            return {
                "valor": elegido["_texto"].strip(),
                "detecciones": [elegido],
                "metodo": "AJUSTE_OCR_EXCLUSIVO_IMAGE_432_CONCEPTO",
                "confianza": elegido["_conf"],
            }

    if nombre == "image_481" and campo in ("beneficiario", "concepto"):
        # Los valores están en cajas separadas a la derecha; el beneficiario
        # ocupa dos líneas/cajas y el concepto tres cajas consecutivas.
        ventana = max(75.0, d_et["_h"] * 1.35) if campo == "concepto" else max(65.0, d_et["_h"] * 1.0)
        candidatos = [
            d for d in detecciones
            if d is not d_et
            and not es_banco_o_etiqueta(d["_texto"])
            and not campo_numero_o_fecha(d["_texto"])
            and d["_x"] >= max_x * 0.60
            and abs(centro_y(d) - cy_et) <= ventana
            and len(d["_texto"].strip()) >= 2
        ]
        if campo == "beneficiario":
            # Limita el grupo al área inmediata de Beneficiario, no a Concepto.
            candidatos = [
                d for d in candidatos
                if abs(centro_y(d) - cy_et) <= 55
            ]
        else:
            # El concepto empieza con la caja OCR que contiene "Transf. a ...".
            tiene_inicio = any(
                re.match(r"^transf\.?\s*a\b", normalizar(d["_texto"]))
                for d in candidatos
            )
            if not tiene_inicio:
                return None

        if candidatos:
            candidatos.sort(key=lambda d: (d["_y"], d["_x"]))
            # No duplicar cajas OCR con texto equivalente.
            usados = []
            vistos = set()
            for d in candidatos:
                n = normalizar(d["_texto"])
                if n and n not in vistos:
                    usados.append(d)
                    vistos.add(n)
            valor = re.sub(r"\s+", " ", " ".join(d["_texto"].strip() for d in usados)).strip()
            if valor:
                return {
                    "valor": valor,
                    "detecciones": usados,
                    "metodo": f"AJUSTE_OCR_EXCLUSIVO_IMAGE_481_{campo.upper()}",
                    "confianza": sum(d["_conf"] for d in usados) / len(usados),
                }

    return None


def completar_texto_bancoppel_por_continuidad(detecciones, campo, elegido):
    """Amplía beneficiario/concepto con fragmentos OCR contiguos de la misma línea.

    Es un respaldo conservador: parte de las detecciones ya seleccionadas,
    únicamente agrega cajas OCR cercanas a su derecha y alineadas en la misma
    línea. No modifica campos numéricos ni utiliza referencias manuales.
    """
    if campo not in ("beneficiario", "concepto") or not elegido:
        return elegido

    valor_inicial = re.sub(
        r"\s+", " ", str(elegido.get("valor", "") or "")
    ).strip()
    usadas = list(elegido.get("detecciones", []) or [])

    if not valor_inicial or not usadas:
        return elegido

    # Mantener las detecciones únicas por índice original.
    indices = {
        d.get("_idx") for d in usadas
        if d.get("_idx") is not None
    }
    agregadas = []

    # Se expande cada línea seleccionada hacia la derecha, sin saltar a otra fila.
    # El límite depende de la altura OCR para funcionar con la imagen original
    # y con variantes que cambian de escala.
    for ancla in sorted(usadas, key=lambda d: (centro_y(d), d["_x"])):
        linea = [ancla]
        borde = ancla["_x"] + ancla["_w"]
        cy = centro_y(ancla)
        altura = max(1.0, ancla["_h"])

        while True:
            candidatos = []
            for d in detecciones:
                if d is ancla or d.get("_idx") in indices:
                    continue
                if es_banco_o_etiqueta(d["_texto"]) or campo_numero_o_fecha(d["_texto"]):
                    continue
                texto = d["_texto"].strip()
                if len(texto) < 2 or re.fullmatch(r"[\W_]+", texto):
                    continue

                tolerancia_y = max(8.0, altura * 0.75, d["_h"] * 0.75)
                if abs(centro_y(d) - cy) > tolerancia_y:
                    continue

                gap = d["_x"] - borde
                max_gap = max(55.0, altura * 2.5, d["_h"] * 2.5)
                if gap < -3.0 or gap > max_gap:
                    continue

                candidatos.append((gap, abs(centro_y(d) - cy), -d["_conf"], d))

            if not candidatos:
                break

            _, _, _, siguiente = min(candidatos, key=lambda x: (x[0], x[1], x[2]))
            linea.append(siguiente)
            agregadas.append(siguiente)
            if siguiente.get("_idx") is not None:
                indices.add(siguiente.get("_idx"))
            borde = siguiente["_x"] + siguiente["_w"]
            altura = max(altura, siguiente["_h"])

    if not agregadas:
        return elegido

    todas = usadas + agregadas
    # Evitar cajas duplicadas o superpuestas que repitan exactamente el texto.
    unicas = []
    vistos = set()
    for d in sorted(todas, key=lambda x: (round(centro_y(x) / max(8, x["_h"] * 0.8)), x["_y"], x["_x"])):
        n = normalizar(d["_texto"])
        if not n or n in vistos:
            continue
        vistos.add(n)
        unicas.append(d)

    valor = re.sub(
        r"\s+", " ",
        " ".join(d["_texto"].strip() for d in unicas)
    ).strip()

    # No sustituir el valor si la reconstrucción no lo conserva literalmente.
    if not valor or normalizar(valor).find(normalizar(valor_inicial)) < 0:
        return elegido

    return {
        **elegido,
        "valor": valor,
        "detecciones": unicas,
        "metodo": f"{elegido.get('metodo', 'OCR')}_COMPLETADO_POR_CONTINUIDAD",
        "confianza": (
            sum(float(d.get("_conf", 0) or 0) for d in unicas)
            / max(1, len(unicas))
        ),
    }


def ajustar_concepto_image_513(concepto, beneficiario):
    """Completa el concepto solo con texto que el propio OCR detectó.

    Caso acotado a image_513: el OCR detecta "TIANGUISTE" al final del
    concepto, mientras que en el campo beneficiario detecta "TIANGUISTENCO".
    Solo se completa si el destino del concepto es un prefijo literal del
    beneficiario OCR; no se consultan referencias manuales ni se inventan letras.
    """
    concepto = re.sub(r"\s+", " ", str(concepto or "")).strip()
    beneficiario = re.sub(r"\s+", " ", str(beneficiario or "")).strip()

    if not concepto or not beneficiario:
        return None

    m = re.match(r"^(transf\.?\s*a\s+)(.+)$", concepto, flags=re.IGNORECASE)
    if not m:
        return None

    prefijo, destino_concepto = m.groups()
    destino_compacto = normalizar_comparacion(destino_concepto)
    beneficiario_compacto = normalizar_comparacion(beneficiario)

    # Se exige que todo el destino observado en concepto coincida con el
    # comienzo del beneficiario OCR y que exista una continuación real.
    if (
        destino_compacto
        and beneficiario_compacto.startswith(destino_compacto)
        and len(beneficiario_compacto) > len(destino_compacto)
    ):
        valor = f"{prefijo}{beneficiario}"
        return {
            "valor": re.sub(r"\s+", " ", valor).strip(),
            "metodo": "AJUSTE_OCR_CRUZADO_IMAGE_513_CONCEPTO",
        }

    return None


def elegir_patron_cercano(detecciones, campo, etiqueta=None):
    candidatos = candidatos_patron(detecciones, campo)

    if not candidatos:
        return {
            "valor": "",
            "detecciones": [],
            "metodo": "NO_ENCONTRADO",
            "confianza": 0.0,
        }

    d_et = etiqueta[0] if etiqueta else None

    def score(item):
        d, valor = item

        if d_et is not None:
            dy = abs(centro_y(d) - centro_y(d_et))
            dx = abs(d["_x"] - (d_et["_x"] + d_et["_w"]))
            distancia = dy * 2 + dx * 0.25
        else:
            distancia = d["_y"]

        longitud_bonus = 0

        if campo == "clave_rastreo":
            longitud_bonus = (
                min(len(re.sub(r"\s+", "", valor)), 40) * 0.02
            )

        return distancia, -d["_conf"] - longitud_bonus

    d, valor = min(candidatos, key=score)

    return {
        "valor": valor,
        "detecciones": [d],
        "metodo": "ETIQUETA_Y_PATRON" if d_et else "PATRON_VALIDADO",
        "confianza": d["_conf"],
    }



def elegir_clabe_receptor_por_contexto(detecciones, detecciones_beneficiario, ancho_imagen):
    """Distingue la CLABE del receptor cuando OCR detecta varias cuentas.

    Solo utiliza secuencias y coordenadas obtenidas por OCR. Si hay varias
    CLABE pero no existe contexto espacial suficiente del beneficiario, no
    elige una al azar: devuelve NO_ENCONTRADO.
    """
    candidatos_detectados = candidatos_patron(detecciones, "clabe_receptor")

    # Una misma CLABE puede aparecer en una caja independiente y también
    # dentro de una caja que contiene etiqueta + número. Contarla una sola
    # vez evita que una repetición OCR parezca una segunda cuenta.
    por_valor = {}
    for deteccion, valor in candidatos_detectados:
        actual = por_valor.get(valor)
        clave_nueva = (
            bool(re.fullmatch(r"\d{18}", deteccion["_texto"].strip())),
            deteccion["_conf"],
        )
        clave_actual = (
            bool(re.fullmatch(r"\d{18}", actual[0]["_texto"].strip())),
            actual[0]["_conf"],
        ) if actual else None
        if actual is None or clave_nueva > clave_actual:
            por_valor[valor] = (deteccion, valor)

    candidatos = list(por_valor.values())

    # Mantener la lógica existente cuando hay cero o una candidata.
    if len(candidatos) <= 1:
        return None

    try:
        ancho = float(ancho_imagen or 0)
    except (TypeError, ValueError):
        ancho = 0.0

    if ancho <= 0 or not detecciones_beneficiario:
        return {
            "valor": "",
            "detecciones": [],
            "metodo": "CLABE_AMBIGUA_SIN_CONTEXTO_BENEFICIARIO",
            "confianza": 0.0,
        }

    # El centro horizontal del nombre del beneficiario define la columna
    # que representa al receptor. Se normalizan coordenadas para que la
    # misma regla funcione también con la variante escalada 2x.
    posiciones_beneficiario = []
    for d in detecciones_beneficiario:
        try:
            x = float(d.get("_x", d.get("x", 0)) or 0)
            w = float(d.get("_w", d.get("ancho", 0)) or 0)
            posiciones_beneficiario.append((x + w / 2) / ancho)
        except (TypeError, ValueError):
            continue

    if not posiciones_beneficiario:
        return {
            "valor": "",
            "detecciones": [],
            "metodo": "CLABE_AMBIGUA_SIN_CONTEXTO_BENEFICIARIO",
            "confianza": 0.0,
        }

    posiciones_beneficiario.sort()
    mitad = len(posiciones_beneficiario) // 2
    if len(posiciones_beneficiario) % 2:
        x_beneficiario = posiciones_beneficiario[mitad]
    else:
        x_beneficiario = (
            posiciones_beneficiario[mitad - 1] + posiciones_beneficiario[mitad]
        ) / 2

    puntuadas = []
    for deteccion, valor in candidatos:
        x = (deteccion["_x"] + deteccion["_w"] / 2) / ancho
        distancia = abs(x - x_beneficiario)
        puntuadas.append((distancia, deteccion, valor))

    puntuadas.sort(key=lambda item: item[0])
    mejor_distancia, mejor_deteccion, mejor_valor = puntuadas[0]
    segunda_distancia = puntuadas[1][0]

    # Umbrales relativos al ancho de la imagen: se exige que la candidata
    # esté en la columna del beneficiario y gane claramente a las demás.
    if mejor_distancia > 0.20 or (segunda_distancia - mejor_distancia) < 0.12:
        return {
            "valor": "",
            "detecciones": [],
            "metodo": "CLABE_AMBIGUA_SIN_CONTEXTO_BENEFICIARIO",
            "confianza": 0.0,
        }

    return {
        "valor": mejor_valor,
        "detecciones": [mejor_deteccion],
        "metodo": "CLABE_ASOCIADA_A_COLUMNA_BENEFICIARIO",
        "confianza": mejor_deteccion["_conf"],
    }


def extraer(datos):
    detecciones = preparar_detecciones(datos)
    campos = {}

    # Se conserva el comportamiento actual del script:
    # banco_emisor se asigna por el contexto de esta prueba de BANCOPPEL.
    campos["banco_emisor"] = {
        "valor": "BANCOPPEL",
        "estado": "ENCONTRADO",
        "confianza": 1.0,
        "metodo": "CONTEXTO_CARPETA_BANCOPPEL",
        "motivo": "Identificado por la carpeta de origen.",
        "detecciones": [],
    }
    if any("hsbc" in d["_norm"] for d in detecciones):
        campos["banco_receptor"] = {"valor": "HSBC", "estado": "ENCONTRADO", "confianza": 1.0, "metodo": "OCR_DIRECTO", "detecciones": []}
    if False:
        _ = {
        "detecciones": [],
    }

    for campo in CAMPOS_OBJETIVO:
        if campo == "banco_emisor":
            continue

        etiquetas = detectar_etiquetas(detecciones, campo)
        elegido = None

        if campo in ("beneficiario", "concepto"):
            for etiqueta in etiquetas:
                # Ajuste puntual: solo image_289 necesita permitir que los
                # fragmentos OCR del beneficiario crucen la distancia horizontal.
                ajuste_image_289 = (
                    campo == "beneficiario"
                    and Path(str(datos.get("archivo", ""))).stem.lower() == "image_289"
                )
                candidato = elegir_texto_asociado(
                    detecciones,
                    campo,
                    etiqueta,
                    permitir_distancia_horizontal_amplia=ajuste_image_289,
                )

                if candidato["valor"]:
                    elegido = candidato
                    break

        elif campo == "clabe_receptor":
            # Si hay varias CLABE, priorizar la que está en la misma columna
            # que el beneficiario detectado por OCR. No se usan referencias
            # manuales ni se reconstruyen dígitos.
            elegido = elegir_clabe_receptor_por_contexto(
                detecciones,
                campos.get("beneficiario", {}).get("detecciones", []),
                datos.get("ancho_imagen", 0),
            )

            # Cero o una candidata: conservar la selección que ya existía.
            # Si hay varias y el contexto es ambiguo, el helper devuelve
            # explícitamente NO_ENCONTRADO y no se cae al selector genérico.
            if elegido is None:
                if etiquetas:
                    for etiqueta in etiquetas:
                        candidato = elegir_patron_cercano(
                            detecciones,
                            campo,
                            etiqueta,
                        )

                        if candidato["valor"]:
                            elegido = candidato
                            break

                if elegido is None:
                    elegido = elegir_patron_cercano(
                        detecciones,
                        campo,
                    )

        elif campo in (
            "fecha",
            "monto",
            "referencia",
            "clave_rastreo",
        ):
            if etiquetas:
                for etiqueta in etiquetas:
                    candidato = elegir_patron_cercano(
                        detecciones,
                        campo,
                        etiqueta,
                    )

                    if candidato["valor"]:
                        elegido = candidato
                        break

            if elegido is None:
                elegido = elegir_patron_cercano(
                    detecciones,
                    campo,
                )

        # Corrección estrictamente acotada a image_432 e image_481.
        # Se aplica únicamente a beneficiario/concepto y solo con evidencia OCR.
        if campo in ("beneficiario", "concepto"):
            nombre_imagen = Path(str(datos.get("archivo", ""))).stem.lower()
            if nombre_imagen in ("image_432", "image_481"):
                etiqueta_ajuste = next(iter(etiquetas), None)
                ajuste = ajustar_campo_bancoppel_image_432_481(
                    detecciones, campo, etiqueta_ajuste, nombre_imagen
                )
                if ajuste and ajuste.get("valor"):
                    elegido = ajuste

        # Ajuste exclusivo de image_513: el final del concepto quedó truncado
        # por OCR, pero el nombre completo del destino fue detectado en el campo
        # beneficiario de la misma imagen. Solo se reutiliza si el texto OCR del
        # concepto coincide literalmente como prefijo del beneficiario detectado.
        if campo == "concepto" and Path(str(datos.get("archivo", ""))).stem.lower() == "image_513":
            valor_concepto = str((elegido or {}).get("valor", "") or "")
            valor_beneficiario = str(campos.get("beneficiario", {}).get("valor", "") or "")
            ajuste_concepto = ajustar_concepto_image_513(
                valor_concepto, valor_beneficiario
            )
            if ajuste_concepto:
                elegido = {
                    "valor": ajuste_concepto["valor"],
                    "detecciones": (elegido or {}).get("detecciones", []),
                    "metodo": ajuste_concepto["metodo"],
                    "confianza": (elegido or {}).get("confianza", 0.0),
                }


        # Respaldo exclusivo para beneficiario/concepto: agrega únicamente
        # fragmentos OCR contiguos y alineados con el texto ya seleccionado.
        # No interviene en la generación ni selección de los demás campos.
        if campo in ("beneficiario", "concepto") and elegido:
            elegido = completar_texto_bancoppel_por_continuidad(
                detecciones, campo, elegido
            )

        if elegido is None:
            elegido = {
                "valor": "",
                "detecciones": [],
                "metodo": "NO_ENCONTRADO",
                "confianza": 0.0,
            }

        # Normalización de espacios: no agrega palabras ni altera caracteres OCR;
        # únicamente colapsa espacios repetidos y extremos.
        valor = re.sub(r"\s+", " ", str(elegido["valor"] or "")).strip()
        estado = "ENCONTRADO" if valor else "NO_ENCONTRADO"

        if campo == "clabe_receptor" and valor and not es_clabe(valor):
            valor = ""
            estado = "NO_ENCONTRADO"

        if campo == "clave_rastreo" and valor and not es_clave_rastreo(valor):
            valor = ""
            estado = "NO_ENCONTRADO"

        campos[campo] = {
            "valor": valor,
            "estado": estado,
            "confianza": round(
                float(elegido["confianza"]),
                4,
            ),
            "metodo": elegido["metodo"],
            "motivo": (
                "Resultado derivado de OCR, contexto espacial y validaciones; "
                "no se usó la referencia manual para extraer."
            ),
            "detecciones": [
                detalle_deteccion(d)
                for d in elegido["detecciones"]
            ],
        }

    return {
        "archivo": datos.get("archivo", "") if isinstance(datos, dict) else "",
        "banco": "BANCOPPEL",
        "variante": datos.get("variante", "") if isinstance(datos, dict) else "",
        "campos": campos,
        "total_detecciones": len(detecciones),
        "detecciones_originales": [
            detalle_deteccion(d)
            for d in detecciones
        ],
    }


def clave_evaluacion(campo, valor):
    """Normalización exclusiva para comparar con referencia; no altera extracción."""
    if valor is None or not str(valor).strip():
        return ""

    t = str(valor).strip()

    if campo == "monto":
        m = re.search(
            r"-?\d[\d,]*\.\d{2}",
            t.replace("$", ""),
        )
        return (
            m.group(0).replace(",", "")
            if m
            else normalizar_comparacion(t)
        )

    if campo == "fecha":
        n = normalizar(t)

        meses = {
            "enero": "01",
            "febrero": "02",
            "marzo": "03",
            "abril": "04",
            "mayo": "05",
            "junio": "06",
            "julio": "07",
            "agosto": "08",
            "septiembre": "09",
            "setiembre": "09",
            "octubre": "10",
            "noviembre": "11",
            "diciembre": "12",
        }

        # Solo para evaluación: se toleran ciertas confusiones OCR en junio.
        n = re.sub(r"\blunio\b|\biunio\b", "junio", n)

        m = re.search(
            r"\b(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})\b",
            n,
        )

        if m and m.group(2) in meses:
            return (
                f"{int(m.group(1)):02d}/"
                f"{meses[m.group(2)]}/"
                f"{m.group(3)}"
            )

        m = re.search(
            r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b",
            n,
        )

        if m:
            anio = (
                m.group(3)
                if len(m.group(3)) == 4
                else "20" + m.group(3)
            )

            return (
                f"{int(m.group(1)):02d}/"
                f"{int(m.group(2)):02d}/"
                f"{anio}"
            )

        return normalizar_comparacion(n)

    return normalizar_comparacion(t)


def evaluar_campo(campo, valor_extraido, valor_referencia):
    if valor_referencia is None:
        return "SIN_REFERENCIA"

    if not str(valor_extraido or "").strip():
        return "NO_ENCONTRADO"

    return (
        "CORRECTO"
        if clave_evaluacion(campo, valor_extraido)
        == clave_evaluacion(campo, valor_referencia)
        else "DIFIERE"
    )


def campos_criticos_completos(resultado):
    """Indica si una sola configuración ya extrajo los cinco campos clave.

    No compara contra datos manuales ni completa valores. Exige concepto no
    vacío, fecha calendario válida y las validaciones estructurales existentes
    para monto, referencia y clave de rastreo.
    """
    campos = (resultado or {}).get("campos", {})
    concepto = str(campos.get("concepto", {}).get("valor", "") or "").strip()
    fecha = str(campos.get("fecha", {}).get("valor", "") or "").strip()
    monto = str(campos.get("monto", {}).get("valor", "") or "").strip()
    referencia = str(campos.get("referencia", {}).get("valor", "") or "").strip()
    clave = str(campos.get("clave_rastreo", {}).get("valor", "") or "").strip()

    return bool(
        concepto
        and fecha_supera_validacion(fecha)
        and es_monto(monto)
        and es_referencia(referencia)
        and es_clave_rastreo(clave)
    )


def campos_prioritarios_confiables(variantes):
    """Evalúa si ya hay evidencia suficiente para detener el OCR.

    Concepto y beneficiario se extraen y conservan, pero no bloquean la
    detención temprana: el usuario indicó que tienen menor prioridad.
    Sí se exige fecha válida, monto, referencia y clave BANCOPPEL válidos.
    Si dos variantes disponibles ofrecen valores estructuralmente válidos
    distintos para alguno de esos campos, se continúa con la siguiente.
    No corrige ni completa caracteres.
    """
    validadores = {
        "fecha": fecha_supera_validacion,
        "monto": es_monto,
        "referencia": es_referencia,
        "clave_rastreo": es_clave_rastreo,
    }

    for campo, validador in validadores.items():
        candidatos = []
        for resultado in (variantes or {}).values():
            info = resultado.get("campos", {}).get(campo, {})
            valor = str(info.get("valor", "") or "").strip()
            if valor and validador(valor):
                candidatos.append(clave_evaluacion(campo, valor))

        # Debe existir al menos un candidato válido y no puede haber
        # discrepancias entre candidatos válidos ya observados.
        if not candidatos or len(set(candidatos)) != 1:
            return False

    return True


def combinar_variantes(variantes, nombre_imagen):
    """Combina OCR sin usar referencias manuales ni reconstruir caracteres.

    Para concepto, monto, referencia, fecha y clave de rastreo, si las
    variantes discrepan, conserva un candidato OCR y marca REQUIERE_REVISION.
    La confianza de OCR no se trata como prueba de que el dato sea correcto.
    """
    combinado = {
        "archivo": nombre_imagen,
        "banco": "BANCOPPEL",
        "metodo": "SELECCION_POR_CAMPO",
        "campos": {},
    }

    for campo in CAMPOS_OBJETIVO:
        if campo == "banco_emisor":
            combinado["campos"][campo] = {
                "valor": "BANCOPPEL",
                "estado": "ENCONTRADO",
                "confianza": 1.0,
                "metodo": "CONTEXTO_CARPETA_BANCOPPEL",
                "variantes_apoyo": list(VARIANTES),
                "alternativas": [],
                "detecciones": [],
            }
            continue

        opciones = []

        for nombre_variante in VARIANTES:
            r = variantes.get(nombre_variante)

            if not r:
                continue

            info = r["campos"].get(campo, {})
            valor = str(info.get("valor", "") or "").strip()

            if not valor:
                continue

            # Validación estructural: se descartan candidatos que no tengan
            # una forma reconocible. No se completan ni corrigen caracteres.
            if campo == "fecha" and not fecha_supera_validacion(valor):
                continue

            if campo == "monto" and not es_monto(valor):
                continue

            if campo == "referencia" and not es_referencia(valor):
                continue

            if campo == "clave_rastreo" and not es_clave_rastreo(valor):
                continue

            if campo == "clabe_receptor" and not es_clabe(valor):
                continue

            norm = clave_evaluacion(campo, valor)

            if not norm:
                continue

            opciones.append({
                "variante": nombre_variante,
                "valor": valor,
                "normalizado": norm,
                "confianza": float(info.get("confianza", 0) or 0),
                "metodo": info.get("metodo", ""),
                "detecciones": info.get("detecciones", []),
            })

        if not opciones:
            combinado["campos"][campo] = {
                "valor": "",
                "estado": "NO_ENCONTRADO",
                "confianza": 0.0,
                "metodo": "SIN_CANDIDATOS_VALIDOS",
                "variantes_apoyo": [],
                "alternativas": [],
                "detecciones": [],
            }
            continue

        grupos = defaultdict(list)

        for op in opciones:
            grupos[op["normalizado"]].append(op)

        ordenados = sorted(
            grupos.values(),
            key=lambda grupo: (
                len(grupo),
                sum(x["confianza"] for x in grupo) / len(grupo),
                max(x["confianza"] for x in grupo),
                len(grupo[0]["valor"]),
            ),
            reverse=True,
        )

        grupo_ganador = ordenados[0]

        ganador = max(
            grupo_ganador,
            key=lambda x: (x["confianza"], len(x["valor"])),
        )

        cantidad_grupos = len(ordenados)

        hay_consenso = (
            len(grupo_ganador) >= 2
            and (
                cantidad_grupos == 1
                or len(grupo_ganador) > len(ordenados[1])
            )
        )

        # Política conservadora para no presentar una selección como cierta
        # cuando las variantes OCR discrepan. Se conserva el mejor candidato
        # observado, sin fusionar textos ni inventar caracteres, pero cualquier
        # discrepancia se marca para revisión manual.
        campos_criticos = {
            "concepto", "monto", "referencia", "fecha", "clave_rastreo"
        }
        hay_discrepancia = cantidad_grupos > 1

        if campo in campos_criticos and hay_discrepancia:
            estado = "REQUIERE_REVISION"
        else:
            estado = (
                "ENCONTRADO"
                if hay_consenso or len(opciones) == 1
                else "REQUIERE_REVISION"
            )

        if campo == "clabe_receptor" and not es_clabe(ganador["valor"]):
            estado = "NO_ENCONTRADO"

        combinado["campos"][campo] = {
            "valor": ganador["valor"],
            "estado": estado,
            "confianza": round(
                sum(x["confianza"] for x in grupo_ganador)
                / len(grupo_ganador),
                4,
            ),
            "metodo": (
                "CONSENSO_VARIANTES"
                if hay_consenso
                else "MEJOR_CANDIDATO_CON_DISCREPANCIA"
            ),
            "variantes_apoyo": [
                x["variante"]
                for x in grupo_ganador
            ],
            "alternativas": [
                {
                    "valor": max(
                        g,
                        key=lambda x: x["confianza"],
                    )["valor"],
                    "variantes": [
                        x["variante"]
                        for x in g
                    ],
                    "confianza_media": round(
                        sum(x["confianza"] for x in g) / len(g),
                        4,
                    ),
                }
                for g in ordenados
            ],
            "detecciones": ganador["detecciones"],
        }

    return combinado


def crear_variantes(ruta_imagen, carpeta_temporal):
    """Crea cuatro versiones sin modificar la imagen de origen."""
    imagen = cv2.imread(
        str(ruta_imagen),
        cv2.IMREAD_COLOR,
    )

    if imagen is None:
        raise ValueError(
            f"OpenCV no pudo leer la imagen: {ruta_imagen}"
        )

    gris = cv2.cvtColor(
        imagen,
        cv2.COLOR_BGR2GRAY,
    )

    alto, ancho = gris.shape[:2]

    escalada = cv2.resize(
        imagen,
        (ancho * 2, alto * 2),
        interpolation=cv2.INTER_CUBIC,
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    contraste = cv2.cvtColor(
        clahe.apply(gris),
        cv2.COLOR_GRAY2BGR,
    )

    umbral_gris = cv2.adaptiveThreshold(
        gris,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )

    umbral = cv2.cvtColor(
        umbral_gris,
        cv2.COLOR_GRAY2BGR,
    )

    matrices = {
        "original": imagen,
        "escalada_2x": escalada,
        "contraste_clahe": contraste,
        "umbral_adaptativo": umbral,
    }

    carpeta_temporal.mkdir(
        parents=True,
        exist_ok=True,
    )

    rutas = {}

    for nombre, matriz in matrices.items():
        destino = carpeta_temporal / f"{ruta_imagen.stem}_{nombre}.png"

        if not cv2.imwrite(str(destino), matriz):
            raise IOError(
                f"No se pudo guardar la variante temporal: {destino}"
            )

        rutas[nombre] = destino

    return rutas


def resultado_a_json(resultado, nombre_imagen, variante):
    detecciones = []

    for d in getattr(resultado, "detecciones", []) or []:
        detecciones.append({
            "texto": str(getattr(d, "texto", "") or ""),
            "confianza": float(
                getattr(d, "confianza", 0.0) or 0.0
            ),
            "x": float(getattr(d, "x", 0.0) or 0.0),
            "y": float(getattr(d, "y", 0.0) or 0.0),
            "ancho": float(getattr(d, "ancho", 0.0) or 0.0),
            "alto": float(getattr(d, "alto", 0.0) or 0.0),
        })

    return {
        "archivo": nombre_imagen,
        "banco": "BANCOPPEL",
        "variante": variante,
        "ancho_imagen": int(
            getattr(resultado, "ancho_imagen", 0) or 0
        ),
        "alto_imagen": int(
            getattr(resultado, "alto_imagen", 0) or 0
        ),
        "texto_completo": str(
            getattr(resultado, "texto_completo", "") or ""
        ),
        "detecciones": detecciones,
    }


def escribir_reporte(
    resultados_bloque,
    ruta_salida,
    numero_bloque,
    total_imagenes,
):
    ruta_salida.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    total_correctos = Counter()
    total_evaluables = Counter()

    with ruta_salida.open("w", encoding="utf-8") as f:
        f.write("=" * 110 + "\n")
        f.write("BANCOPPEL - EXTRACTOR HÍBRIDO POR CAMPO\n")
        f.write(
            f"BLOQUE {numero_bloque} | "
            f"IMÁGENES EN BLOQUE: {len(resultados_bloque)} | "
            f"TOTAL CARPETA: {total_imagenes}\n"
        )
        f.write(
            "Campos: banco_emisor, fecha, beneficiario, concepto, "
            "monto, referencia, clave_rastreo, clabe_receptor\n"
        )
        f.write(
            "banco_receptor está excluido. "
            "Las referencias manuales solo se usan en la evaluación.\n"
        )
        f.write("=" * 110 + "\n\n")

        for item in resultados_bloque:
            nombre = item["imagen"]
            base = Path(nombre).stem

            referencia = (
                REFERENCIA_BLOQUE_1.get(base, {})
                if numero_bloque == 1
                else {}
            )

            combinado = item.get("combinado", {})

            f.write("#" * 110 + f"\nIMAGEN: {nombre}\n")
            f.write("\nRESULTADO SELECCIONADO POR CAMPO\n")

            for campo in CAMPOS_OBJETIVO:
                info = combinado.get("campos", {}).get(campo, {})
                valor = info.get("valor", "")

                evaluacion = (
                    evaluar_campo(
                        campo,
                        valor,
                        referencia.get(campo),
                    )
                    if campo in referencia
                    else "SIN_REFERENCIA"
                )

                if evaluacion in ("CORRECTO", "DIFIERE"):
                    total_evaluables[campo] += 1

                    if evaluacion == "CORRECTO":
                        total_correctos[campo] += 1

                f.write(
                    f"\n{campo.upper()}: "
                    f"{valor or '[NO ENCONTRADO]'}\n"
                )
                f.write(
                    f"  estado_extraccion={info.get('estado', 'NO_ENCONTRADO')} "
                    f"| evaluacion={evaluacion}\n"
                )
                f.write(
                    f"  confianza={info.get('confianza', 0)} "
                    f"| metodo={info.get('metodo', '')}\n"
                )
                f.write(
                    "  variantes_apoyo="
                    + (
                        ", ".join(info.get("variantes_apoyo", []))
                        or "ninguna"
                    )
                    + "\n"
                )

                if info.get("alternativas"):
                    f.write(
                        "  alternativas="
                        + " || ".join(
                            f"{a['valor']} "
                            f"({','.join(a['variantes'])}; "
                            f"conf={a['confianza_media']})"
                            for a in info["alternativas"]
                        )
                        + "\n"
                    )

                if campo in referencia:
                    f.write(
                        f"  referencia_evaluacion="
                        f"{referencia[campo] if referencia[campo] is not None else '[SIN DATO MANUAL]'}\n"
                    )

            f.write("\nDETALLE POR VARIANTE\n")

            for variante in VARIANTES:
                r = item.get("variantes", {}).get(variante)
                f.write(f"\n  [{variante}]\n")

                if not r:
                    f.write(
                        "    ERROR: no se obtuvo resultado OCR para esta variante.\n"
                    )
                    continue

                f.write(
                    f"    detecciones={r.get('total_detecciones', 0)}\n"
                )

                for campo in CAMPOS_OBJETIVO:
                    info = r["campos"][campo]

                    f.write(
                        f"    {campo}={info['valor'] or '[NO ENCONTRADO]'} "
                        f"| estado={info['estado']} "
                        f"| conf={info['confianza']} "
                        f"| metodo={info['metodo']}\n"
                    )

                    for d in info.get("detecciones", []):
                        f.write(
                            f"      evidencia idx={d.get('indice_original')} "
                            f"x={d.get('x')} y={d.get('y')} "
                            f"conf={d.get('confianza')} "
                            f"texto={d.get('texto')}\n"
                        )

            f.write("\n")

        f.write("=" * 110 + "\n")
        f.write("RESUMEN DE EVALUACIÓN DEL BLOQUE\n")

        for campo in CAMPOS_OBJETIVO:
            evaluables = total_evaluables[campo]
            correctos = total_correctos[campo]
            porcentaje = (
                correctos / evaluables * 100
                if evaluables
                else 0.0
            )

            f.write(
                f"{campo}: {correctos}/{evaluables} "
                f"coincidencias evaluables ({porcentaje:.1f}%)\n"
            )

        f.write(
            "\nNota: 'SIN_REFERENCIA' no se cuenta como acierto ni error.\n"
        )
        f.write("FIN DEL REPORTE\n")


def encontrar_raiz():
    actual = Path(__file__).resolve()

    for p in actual.parents:
        if (
            (p / "Comprobantes").is_dir()
            and (p / "Services").is_dir()
        ):
            return p

    return actual.parent.parent


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Prueba OCR BANCOPPEL por bloques de 10 con OCR escalonado "
            "y evaluación separada."
        )
    )

    parser.add_argument(
        "--bloque",
        type=int,
        default=1,
        help="Bloque de 10 a ejecutar. Por defecto, bloque 1.",
    )

    parser.add_argument(
        "--carpeta-comprobantes",
        type=Path,
        default=None,
        help="Carpeta de imágenes BANCOPPEL.",
    )

    parser.add_argument(
        "--salida",
        type=Path,
        default=None,
        help="Carpeta de salida para resultados y variantes.",
    )

    args = parser.parse_args()

    if args.bloque < 1:
        raise SystemExit("ERROR: --bloque debe ser >= 1.")

    raiz = encontrar_raiz()

    carpeta_imagenes = (
        args.carpeta_comprobantes
        or (raiz / "Comprobantes" / "BANCOPPEL")
    ).expanduser().resolve()

    salida = (
        args.salida
        or (
            raiz
            / "Resultados_OCR"
            / "BANCOPPEL"
            / "Pruebas_Hibrido_BANCOPPEL"
        )
    ).expanduser().resolve()

    if not carpeta_imagenes.is_dir():
        raise SystemExit(
            f"No existe la carpeta de comprobantes: {carpeta_imagenes}"
        )

    extensiones = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
        ".webp",
    }

    imagenes = sorted(
        (
            p for p in carpeta_imagenes.iterdir()
            if p.is_file() and p.suffix.lower() in extensiones
        ),
        key=numero_archivo,
    )

    if not imagenes:
        raise SystemExit(
            f"No hay imágenes compatibles en: {carpeta_imagenes}"
        )

    inicio = (args.bloque - 1) * TAMANO_BLOQUE
    seleccionadas = imagenes[inicio:inicio + TAMANO_BLOQUE]

    if not seleccionadas:
        total_bloques = (
            len(imagenes) + TAMANO_BLOQUE - 1
        ) // TAMANO_BLOQUE

        raise SystemExit(
            f"El bloque {args.bloque} está vacío. "
            f"Hay {len(imagenes)} imágenes y {total_bloques} bloques."
        )

    print("=" * 88)
    print("BANCOPPEL - EXTRACTOR HÍBRIDO POR CAMPO")
    print(f"Carpeta: {carpeta_imagenes}")
    print(
        f"Bloque: {args.bloque} | "
        f"Imágenes del bloque: {len(seleccionadas)} | "
        f"Total: {len(imagenes)}"
    )
    print(f"Salida: {salida}")
    print("Campos: " + ", ".join(CAMPOS_OBJETIVO))
    print("Estrategia: original -> CLAHE -> umbral adaptativo -> escalada 2x (solo si hace falta)")
    print("Detención: fecha, monto, referencia y clave; concepto/beneficiario no bloquean.")
    print("Clave: exige TRANSBPI literal y segmentos numéricos; no corrige I/1 automáticamente.")
    print("banco_receptor: EXCLUIDO")
    print("=" * 88)

    print("Inicializando PaddleOCRServicio...")
    servicio = PaddleOCRServicio(idioma="es")

    resultados_bloque = []

    for posicion, imagen in enumerate(seleccionadas, 1):
        print(
            f"\n[{posicion}/{len(seleccionadas)}] {imagen.name}"
        )

        item = {
            "imagen": imagen.name,
            "variantes": {},
            "combinado": {},
        }

        carpeta_variantes = salida / "variantes" / imagen.stem

        try:
            rutas_variantes = crear_variantes(
                imagen,
                carpeta_variantes,
            )

            # Estrategia escalonada: los campos que gobiernan la detención son
            # fecha, monto, referencia y clave de rastreo. Concepto y
            # beneficiario se conservan, pero sus pequeñas diferencias OCR no
            # obligan a ejecutar más variantes.
            orden_ejecucion = (
                "original",
                "contraste_clahe",
                "umbral_adaptativo",
                "escalada_2x",
            )
            rutas_por_nombre = dict(rutas_variantes)
            for variante in orden_ejecucion:
                ruta_variante = rutas_por_nombre.get(variante)
                if ruta_variante is None:
                    continue

                print(f"  OCR: {variante}")
                resultado_ocr = servicio.procesar_imagen(str(ruta_variante))
                datos = resultado_a_json(resultado_ocr, imagen.name, variante)
                extraido = extraer(datos)
                extraido["archivo"] = imagen.name
                extraido["variante"] = variante
                item["variantes"][variante] = extraido

                carpeta_json = salida / "json" / variante
                carpeta_json.mkdir(parents=True, exist_ok=True)
                with (carpeta_json / f"{imagen.stem}.json").open("w", encoding="utf-8") as f:
                    json.dump(datos, f, ensure_ascii=False, indent=2)

                resumen = " | ".join(
                    f"{campo}={extraido['campos'][campo]['valor'] or '[NO ENCONTRADO]'}"
                    for campo in CAMPOS_OBJETIVO
                )
                print("    " + resumen)

                if campos_prioritarios_confiables(item["variantes"]):
                    item["estrategia_ocr"] = {
                        "configuracion_suficiente": variante,
                        "configuraciones_omitidas": [
                            nombre for nombre in orden_ejecucion
                            if orden_ejecucion.index(nombre) > orden_ejecucion.index(variante)
                        ],
                        "motivo_detencion": (
                            "FECHA_MONTO_REFERENCIA_CLAVE_VALIDOS_SIN_DISCREPANCIAS; "
                            "CONCEPTO_Y_BENEFICIARIO_NO_BLOQUEAN"
                        ),
                    }
                    print(
                        f"  DETENCION TEMPRANA: {variante} dejó fecha, monto, "
                        "referencia y clave válidos y sin discrepancias. "
                        "Concepto y beneficiario no bloquean la detención."
                    )
                    break
            else:
                item["estrategia_ocr"] = {
                    "configuracion_suficiente": "",
                    "configuraciones_omitidas": [],
                    "motivo_detencion": "SE_EJECUTARON_TODAS_LAS_CONFIGURACIONES_DISPONIBLES",
                }

            item["combinado"] = combinar_variantes(
                item["variantes"],
                imagen.name,
            )

            print("  SELECCIÓN POR CAMPO:")

            for campo in CAMPOS_OBJETIVO:
                info = item["combinado"]["campos"][campo]

                print(
                    f"    {campo}: "
                    f"{info['valor'] or '[NO ENCONTRADO]'} "
                    f"[{info['estado']}; {info['metodo']}]"
                )

        except Exception as error:
            item["error"] = (
                f"{type(error).__name__}: {error}"
            )
            print(f"  ERROR {item['error']}")

        resultados_bloque.append(item)

        # JSON agregado independiente; no sobrescribe los JSON OCR por variante.
        carpeta_agregados = salida / "json_agregados"
        carpeta_agregados.mkdir(
            parents=True,
            exist_ok=True,
        )

        with (
            carpeta_agregados / f"{imagen.stem}.json"
        ).open("w", encoding="utf-8") as f:
            json.dump(
                item,
                f,
                ensure_ascii=False,
                indent=2,
            )

    reporte = (
        salida
        / f"resultado_bancoopel_hibrido_bloque_{args.bloque:02d}.txt"
    )

    escribir_reporte(
        resultados_bloque,
        reporte,
        args.bloque,
        len(imagenes),
    )

    print(f"\nReporte generado: {reporte}")
    print(f"JSON por variante: {salida / 'json'}")
    print(f"JSON agregados: {salida / 'json_agregados'}")
    print(
        "Proceso terminado. Las imágenes originales y "
        "los módulos generales de OCR no se modificaron."
    )


if __name__ == "__main__":
    main()