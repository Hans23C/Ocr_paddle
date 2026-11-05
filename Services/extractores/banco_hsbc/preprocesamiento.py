from __future__ import annotations

from pathlib import Path
import cv2
import numpy as np


# Variantes controladas: no se modifica ni sobrescribe la imagen original.
# Se evita crear demasiadas combinaciones para limitar RAM/tiempo en lotes grandes.
NOMBRES_VARIANTES = (
    "original",
    "escalada_2x",
    "brillo_contraste",
    "contraste_clahe",
    "nitidez_suave",
    "reduccion_ruido_clahe",
    "umbral_adaptativo",
)


def _ajustar_bloque_adaptativo(gris):
    alto, ancho = gris.shape[:2]
    minimo = min(alto, ancho)
    bloque = min(31, minimo if minimo % 2 else minimo - 1)
    return bloque if bloque >= 3 else None


def generar_variantes(
    ruta_imagen: str | Path,
    carpeta_salida: str | Path,
) -> dict[str, Path]:
    """Genera un conjunto acotado de variantes experimentales para OCR HSBC."""
    ruta_imagen = Path(ruta_imagen)
    carpeta_salida = Path(carpeta_salida)

    if not ruta_imagen.is_file():
        raise FileNotFoundError(f"No existe la imagen: {ruta_imagen}")

    imagen = cv2.imread(str(ruta_imagen), cv2.IMREAD_COLOR)
    if imagen is None:
        raise ValueError(f"No se pudo leer la imagen: {ruta_imagen}")

    carpeta_salida.mkdir(parents=True, exist_ok=True)
    alto, ancho = imagen.shape[:2]
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    variantes = {"original": imagen.copy()}

    # Escalado cúbico para texto pequeño. Mantiene coordenadas recuperables
    # mediante el factor 2 configurado en reprocesar_hsbc.py.
    variantes["escalada_2x"] = cv2.resize(
        imagen, (ancho * 2, alto * 2), interpolation=cv2.INTER_CUBIC
    )

    # Brillo/contraste moderados: evita quemar el papel térmico.
    variantes["brillo_contraste"] = cv2.convertScaleAbs(
        gris, alpha=1.22, beta=8
    )

    # CLAHE local: mejora zonas de contraste desigual.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gris_clahe = clahe.apply(gris)
    variantes["contraste_clahe"] = gris_clahe

    # Nitidez moderada mediante unsharp mask, sin exagerar bordes.
    desenfoque = cv2.GaussianBlur(gris_clahe, (0, 0), 1.0)
    variantes["nitidez_suave"] = cv2.addWeighted(
        gris_clahe, 1.35, desenfoque, -0.35, 0
    )

    # Reducción de ruido seguida de CLAHE. Se mantiene separada de las otras.
    sin_ruido = cv2.fastNlMeansDenoising(
        gris, None, h=5, templateWindowSize=7, searchWindowSize=21
    )
    variantes["reduccion_ruido_clahe"] = clahe.apply(sin_ruido)

    bloque = _ajustar_bloque_adaptativo(gris_clahe)
    if bloque is not None:
        variantes["umbral_adaptativo"] = cv2.adaptiveThreshold(
            gris_clahe, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, bloque, 9
        )

    rutas = {}
    for nombre, imagen_variante in variantes.items():
        destino = carpeta_salida / f"{nombre}.png"
        if not cv2.imwrite(str(destino), imagen_variante):
            raise OSError(f"No se pudo guardar la variante: {destino}")
        rutas[nombre] = destino

    return rutas
