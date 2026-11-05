from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import cv2

from Services.ocr.paddle_ocr import PaddleOCRServicio
from Services.extractores.banco_hsbc.preprocesamiento import generar_variantes


# Las coordenadas de las detecciones se normalizan a la imagen original.
FACTORES_ESCALA = {
    "original": 1.0,
    "escalada_2x": 2.0,
    "brillo_contraste": 1.0,
    "contraste_clahe": 1.0,
    "nitidez_suave": 1.0,
    "reduccion_ruido_clahe": 1.0,
    "umbral_adaptativo": 1.0,
}

ETIQUETAS_REGION = {
    "folio": re.compile(r"\b(?:folio|folid|foli0|fulid|filid|olio)\b", re.I),
    "cuenta": re.compile(r"\b(?:cuenta|cuenta de deposito|cuenta de deposit[io])\b", re.I),
    "titular": re.compile(r"\b(?:titular|nombre|nom[bp]re)\b", re.I),
    "deposito": re.compile(r"\b(?:deposito|eposito|posito)\b", re.I),
    "monto": re.compile(r"\b(?:deposito|total deposito)\s*[:;,]?", re.I),
}


def guardar_resultado_json(resultado, ruta_json: Path, nombre_imagen: str, variante: str):
    factor = FACTORES_ESCALA.get(variante, 1.0)
    detecciones = []
    for d in resultado.detecciones:
        detecciones.append({
            "texto": d.texto,
            "confianza": float(d.confianza),
            "x": float(d.x / factor),
            "y": float(d.y / factor),
            "ancho": float(d.ancho / factor),
            "alto": float(d.alto / factor),
            "bbox": [[float(p[0] / factor), float(p[1] / factor)] for p in d.bbox],
        })
    documento = {
        "archivo": nombre_imagen,
        "banco": "BANCO_HSBC",
        "variante_preprocesamiento": variante,
        "ancho_imagen": int(resultado.ancho_imagen / factor),
        "alto_imagen": int(resultado.alto_imagen / factor),
        "total_detecciones": len(detecciones),
        "detecciones": detecciones,
    }
    ruta_json.parent.mkdir(parents=True, exist_ok=True)
    with ruta_json.open("w", encoding="utf-8") as f:
        json.dump(documento, f, ensure_ascii=False, indent=2)


def _normalizar_bbox(resultado, factor):
    salida = []
    for d in resultado.detecciones:
        salida.append({
            "texto": str(d.texto or ""),
            "confianza": float(d.confianza or 0.0),
            "x": float(d.x / factor), "y": float(d.y / factor),
            "ancho": float(d.ancho / factor), "alto": float(d.alto / factor),
        })
    return salida


def generar_recortes_candidatos(ruta_original: Path, detecciones: list[dict], carpeta: Path):
    """Crea recortes alrededor de etiquetas detectadas; no supone valores ni coordenadas fijas."""
    imagen = cv2.imread(str(ruta_original), cv2.IMREAD_COLOR)
    if imagen is None:
        raise ValueError(f"No se pudo leer la imagen para recortes: {ruta_original}")
    alto, ancho = imagen.shape[:2]
    recortes = []
    usados = set()

    for d in detecciones:
        texto = d["texto"]
        for campo, patron in ETIQUETAS_REGION.items():
            if campo in usados or not patron.search(texto):
                continue
            x, y = d["x"], d["y"]
            w, h = max(d["ancho"], 1), max(d["alto"], 1)
            # Ventana relativa a la etiqueta; se limita al tamaño de la imagen.
            margen_x = max(36, int(w * 1.8))
            margen_y = max(18, int(h * 2.2))
            x1 = max(0, int(x - margen_x))
            y1 = max(0, int(y - margen_y))
            x2 = min(ancho, int(x + w + max(180, w * 3.0)))
            y2 = min(alto, int(y + h + margen_y))
            if x2 <= x1 or y2 <= y1:
                continue
            recortes.append((campo, imagen[y1:y2, x1:x2].copy(), (x1, y1)))
            usados.add(campo)
    carpeta.mkdir(parents=True, exist_ok=True)
    rutas = []
    for campo, recorte, origen in recortes:
        ruta = carpeta / f"region_{campo}.png"
        if cv2.imwrite(str(ruta), recorte):
            rutas.append({"campo": campo, "ruta": ruta, "origen_x": origen[0], "origen_y": origen[1]})
    return rutas


def ejecutar():
    parser = argparse.ArgumentParser(description="Reprocesamiento experimental de comprobantes HSBC.")
    parser.add_argument("--imagen", required=True, help="Ruta de la imagen original.")
    parser.add_argument("--salida", default="Pruebas_HSBC_Reprocesamiento", help="Directorio de salida.")
    parser.add_argument("--idioma", default="es", help="Idioma configurado en PaddleOCRServicio.")
    parser.add_argument("--recortes", action="store_true", help="Ejecuta OCR adicional en recortes guiados por etiquetas.")
    args = parser.parse_args()

    ruta_imagen = Path(args.imagen).expanduser().resolve()
    carpeta_salida = Path(args.salida).expanduser().resolve()
    if not ruta_imagen.is_file():
        raise SystemExit(f"ERROR: no existe la imagen: {ruta_imagen}")

    nombre = ruta_imagen.stem
    carpeta = carpeta_salida / nombre
    carpeta_variantes = carpeta / "imagenes"
    carpeta_json = carpeta / "json"
    variantes = generar_variantes(ruta_imagen, carpeta_variantes)

    # Inicializar PaddleOCR una sola vez por comprobante/ejecución.
    servicio = PaddleOCRServicio(idioma=args.idioma)
    resumen = []
    detecciones_originales = []

    for variante, ruta_variante in variantes.items():
        print(f"[HSBC] OCR variante: {variante}")
        try:
            resultado = servicio.procesar_imagen(str(ruta_variante))
            ruta_json = carpeta_json / variante / f"{nombre}.json"
            guardar_resultado_json(resultado, ruta_json, ruta_imagen.name, variante)
            if variante == "original":
                detecciones_originales = _normalizar_bbox(resultado, 1.0)
            resumen.append({"variante": variante, "estado": "OK",
                            "detecciones": len(resultado.detecciones), "json": str(ruta_json)})
        except Exception as exc:
            resumen.append({"variante": variante, "estado": "ERROR",
                            "error": f"{type(exc).__name__}: {exc}"})
            print(f"  ERROR: {type(exc).__name__}: {exc}")

    # Los recortes son opcionales porque aumentan el coste de inferencia.
    # Se crean a partir de etiquetas realmente detectadas, no de coordenadas fijas.
    if args.recortes and detecciones_originales:
        carpeta_recortes = carpeta / "recortes"
        recortes = generar_recortes_candidatos(ruta_imagen, detecciones_originales, carpeta_recortes)
        for item in recortes:
            try:
                resultado = servicio.procesar_imagen(str(item["ruta"]))
                salida_json = carpeta_json / "recortes" / f"{item['campo']}.json"
                guardar_resultado_json(resultado, salida_json, ruta_imagen.name, f"recorte_{item['campo']}")
                resumen.append({"variante": f"recorte_{item['campo']}", "estado": "OK",
                                "detecciones": len(resultado.detecciones), "json": str(salida_json),
                                "origen_x": item["origen_x"], "origen_y": item["origen_y"]})
            except Exception as exc:
                resumen.append({"variante": f"recorte_{item['campo']}", "estado": "ERROR",
                                "error": f"{type(exc).__name__}: {exc}"})

    ruta_resumen = carpeta / "resumen.json"
    ruta_resumen.parent.mkdir(parents=True, exist_ok=True)
    ruta_resumen.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Prueba terminada. Resumen: {ruta_resumen}")


if __name__ == "__main__":
    ejecutar()
