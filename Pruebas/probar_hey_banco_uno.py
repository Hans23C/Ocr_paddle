from pathlib import Path
import json
import sys

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from Services.extractores.hey_banco.hey_banco import HeyBancoExtractor

CARPETA_JSON = RAIZ_PROYECTO / "Resultados_OCR" / "HEY_BANCO"
NOMBRE_ARCHIVO = sys.argv[1] if len(sys.argv) > 1 else "image_613.json"
if not NOMBRE_ARCHIVO.endswith(".json"):
    NOMBRE_ARCHIVO += ".json"
RUTA_JSON = CARPETA_JSON / NOMBRE_ARCHIVO


def main():
    print()
    print("=" * 90)
    print(f"PRUEBA INDIVIDUAL - HEY, BANCO ({NOMBRE_ARCHIVO})")
    print("=" * 90)
    print()

    if not RUTA_JSON.exists():
        print(f"ERROR: No existe el JSON: {RUTA_JSON}")
        sys.exit(1)

    with open(RUTA_JSON, "r", encoding="utf-8") as f:
        datos = json.load(f)

    extractor = HeyBancoExtractor()
    resultado = extractor.extraer(datos)

    print("BANCO DETECTADO:", resultado.get("banco"))
    print()
    print("CAMPOS EXTRAÍDOS:")
    for k, v in resultado.get("campos", {}).items():
        print(f"  {k:<20}: {v}")
    print()


if __name__ == "__main__":
    main()
