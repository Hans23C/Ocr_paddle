from pathlib import Path
import json
import sys

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from Services.extractores.banorte.banorte import BanorteExtractor


# ============================================================
# RUTAS
# ============================================================

CARPETA_JSON = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "BANORTE"
)

NOMBRE_ARCHIVO = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "image_020.json"
)

if not NOMBRE_ARCHIVO.endswith(".json"):
    NOMBRE_ARCHIVO += ".json"

RUTA_JSON = CARPETA_JSON / NOMBRE_ARCHIVO


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("=" * 90)
    print(f"PRUEBA INDIVIDUAL - BANORTE ({NOMBRE_ARCHIVO})")
    print("=" * 90)
    print()
    print("JSON:")
    print(RUTA_JSON)
    print()

    if not RUTA_JSON.exists():
        print("ERROR: No existe el JSON.")
        sys.exit(1)

    with open(RUTA_JSON, "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    extractor = BanorteExtractor()
    resultado = extractor.extraer(datos)

    print("BANCO DETECTADO:")
    print(resultado.get("banco"))
    print()
    print("CAMPOS EXTRAÍDOS:")
    for nombre, valor in resultado.get("campos", {}).items():
        print(f"  {nombre:<18}: {valor}")
    print()


if __name__ == "__main__":
    main()
