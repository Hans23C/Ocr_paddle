
"""Preprocesamiento de imágenes exclusivo para comprobantes BANCOPPEL.
No modifica imágenes originales ni configura el OCR general del proyecto.
"""
from pathlib import Path
import argparse
import cv2
import numpy as np


def _guardar(ruta: Path, imagen) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(ruta), imagen):
        raise OSError(f"No se pudo guardar la imagen: {ruta}")
    return ruta


def _limitar(imagen, max_lado=2400):
    h, w = imagen.shape[:2]
    mayor = max(h, w)
    if mayor <= max_lado:
        return imagen.copy()
    factor = max_lado / mayor
    return cv2.resize(imagen, (max(1, int(w*factor)), max(1, int(h*factor))), interpolation=cv2.INTER_AREA)


def generar_variantes(ruta_imagen, carpeta_salida):
    ruta_imagen = Path(ruta_imagen)
    carpeta_salida = Path(carpeta_salida)
    imagen = cv2.imread(str(ruta_imagen), cv2.IMREAD_COLOR)
    if imagen is None:
        raise ValueError(f"No se pudo leer la imagen: {ruta_imagen}")
    base = _limitar(imagen)
    gris = cv2.cvtColor(base, cv2.COLOR_BGR2GRAY)
    variantes = {"original": base}
    variantes["escalada_2x"] = cv2.resize(base, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    variantes["brillo_contraste"] = cv2.convertScaleAbs(base, alpha=1.18, beta=10)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gris)
    variantes["contraste_clahe"] = cv2.cvtColor(clahe, cv2.COLOR_GRAY2BGR)
    suave = cv2.GaussianBlur(base, (0, 0), 1.2)
    variantes["nitidez_suave"] = cv2.addWeighted(base, 1.45, suave, -0.45, 0)
    denoise = cv2.fastNlMeansDenoisingColored(base, None, 5, 5, 7, 21)
    denoise_gray = cv2.cvtColor(denoise, cv2.COLOR_BGR2GRAY)
    denoise_clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(denoise_gray)
    variantes["reduccion_ruido_clahe"] = cv2.cvtColor(denoise_clahe, cv2.COLOR_GRAY2BGR)
    adapt = cv2.adaptiveThreshold(clahe, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11)
    variantes["umbral_adaptativo"] = cv2.cvtColor(adapt, cv2.COLOR_GRAY2BGR)
    rutas = {}
    for nombre, img in variantes.items():
        rutas[nombre] = _guardar(carpeta_salida / f"{ruta_imagen.stem}_{nombre}.png", img)
    return rutas


def main():
    parser = argparse.ArgumentParser(description="Genera variantes de preprocesamiento solo para BANCOPPEL.")
    parser.add_argument("imagen", type=Path, help="Imagen de comprobante BANCOPPEL")
    parser.add_argument("--salida", type=Path, default=None, help="Carpeta destino de variantes")
    args = parser.parse_args()
    destino = args.salida or (args.imagen.parent / "_variantes_bancoopel" / args.imagen.stem)
    for nombre, ruta in generar_variantes(args.imagen, destino).items():
        print(f"{nombre}: {ruta}")

if __name__ == "__main__":
    main()
