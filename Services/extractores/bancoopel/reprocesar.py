
"""Ejecuta PaddleOCR sobre variantes de comprobantes BANCOPPEL.
Los resultados se guardan en una carpeta separada.
No sobrescribe JSON existentes.
"""
from pathlib import Path
import argparse
import json
import sys
import time

RAIZ = Path(__file__).resolve().parents[2]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from Services.ocr.paddle_ocr import PaddleOCRServicio
from Services.extractores.bancoopel.procesar import generar_variantes


EXTENSIONES = {
    ".jpg", ".jpeg", ".png", ".bmp",
    ".tif", ".tiff", ".webp"
}


def deteccion_a_dict(d):
    if isinstance(d, dict):
        return d

    return {
        "texto": getattr(d, "texto", ""),
        "confianza": getattr(d, "confianza", 0.0),
        "bbox": getattr(d, "bbox", []),
        "x": getattr(d, "x", 0),
        "y": getattr(d, "y", 0),
        "ancho": getattr(d, "ancho", 0),
        "alto": getattr(d, "alto", 0),
        "x_rel": getattr(d, "x_rel", 0),
        "y_rel": getattr(d, "y_rel", 0),
        "ancho_rel": getattr(d, "ancho_rel", 0),
        "alto_rel": getattr(d, "alto_rel", 0),
    }


def resultado_a_dict(
    resultado,
    archivo_origen,
    banco="BANCOPPEL",
    variante="original",
    tiempo=0.0
):
    detecciones = getattr(resultado, "detecciones", []) or []

    return {
        "archivo": Path(archivo_origen).name,
        "banco": banco,
        "variante_preprocesamiento": variante,
        "tiempo_ocr_segundos": round(tiempo, 4),
        "ancho_imagen": int(
            getattr(resultado, "ancho_imagen", 0) or 0
        ),
        "alto_imagen": int(
            getattr(resultado, "alto_imagen", 0) or 0
        ),
        "total_detecciones": len(detecciones),
        "detecciones": [
            deteccion_a_dict(d) for d in detecciones
        ],
        "lineas": list(
            getattr(resultado, "lineas", []) or []
        ),
        "texto_completo": str(
            getattr(resultado, "texto_completo", "") or ""
        ),
    }


def numero_archivo(ruta):
    import re
    coincidencia = re.search(r"(\d+)", ruta.stem)
    return int(coincidencia.group(1)) if coincidencia else 10**12


def main():
    parser = argparse.ArgumentParser(
        description="Reprocesamiento OCR aislado para BANCOPPEL."
    )

    parser.add_argument(
        "--entrada",
        type=Path,
        default=RAIZ / "Comprobantes" / "BANCOPPEL"
    )

    parser.add_argument(
        "--salida",
        type=Path,
        default=RAIZ / "Resultados_OCR" / "BANCOPPEL" / "Reprocesados"
    )

    parser.add_argument(
        "--limite",
        type=int,
        default=0,
        help="Limita el número de imágenes; 0 procesa todas."
    )

    parser.add_argument(
        "--solo-original",
        action="store_true",
        help="Ejecuta OCR solo sobre la imagen original."
    )

    args = parser.parse_args()

    entrada = args.entrada.resolve()
    salida = args.salida.resolve()

    if not entrada.is_dir():
        raise SystemExit(
            f"No existe la carpeta de entrada: {entrada}"
        )

    imagenes = sorted(
        (
            p for p in entrada.iterdir()
            if p.is_file()
            and p.suffix.lower() in EXTENSIONES
        ),
        key=numero_archivo
    )

    if args.limite > 0:
        imagenes = imagenes[:args.limite]

    if not imagenes:
        raise SystemExit(
            f"No se encontraron imágenes en: {entrada}"
        )

    print(
        f"BANCOPPEL | imágenes: {len(imagenes)} "
        f"| salida: {salida}"
    )

    servicio = PaddleOCRServicio(idioma="es")
    total = 0

    for indice, imagen in enumerate(imagenes, 1):
        print(f"[{indice}/{len(imagenes)}] {imagen.name}")

        try:
            if args.solo_original:
                variantes = {"original": imagen}
            else:
                carpeta_variantes = (
                    salida / "_imagenes_variantes" / imagen.stem
                )

                variantes = generar_variantes(
                    imagen, carpeta_variantes
                )

            for nombre, ruta_variante in variantes.items():
                inicio = time.perf_counter()

                resultado = servicio.procesar_imagen(
                    str(ruta_variante)
                )

                duracion = time.perf_counter() - inicio

                datos = resultado_a_dict(
                    resultado,
                    imagen,
                    variante=nombre,
                    tiempo=duracion
                )

                destino = (
                    salida / imagen.stem / f"{nombre}.json"
                )
                destino.parent.mkdir(
                    parents=True, exist_ok=True
                )

                # Modo "x": no sobrescribe resultados anteriores.
                with destino.open("x", encoding="utf-8") as f:
                    json.dump(
                        datos,
                        f,
                        ensure_ascii=False,
                        indent=2
                    )

                total += 1

                print(
                    f"   {nombre}: "
                    f"{datos['total_detecciones']} detecciones, "
                    f"{duracion:.2f}s -> {destino.name}"
                )

        except FileExistsError as e:
            print(
                "   OMITIDO: ya existe un resultado; "
                f"no se sobrescribió ({e.filename})"
            )

        except Exception as e:
            print(f"   ERROR {type(e).__name__}: {e}")

    print(
        f"Terminado. JSON nuevos generados: {total}. "
        f"Resultados en: {salida}"
    )


if __name__ == "__main__":
    main()
