from pathlib import Path
import json
import sys

from Services.extractores.banbajio.banbajio import (
    BanBajioExtractor
)


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_JSON = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "BANBAJIO"
)

NOMBRE_ARCHIVO = "image_680.json"


def main():
    print()
    print("=" * 100)
    print("PRUEBA INDIVIDUAL - BANBAJIO")
    print("=" * 100)

    ruta_json = CARPETA_JSON / NOMBRE_ARCHIVO

    print()
    print("JSON:")
    print(ruta_json)

    if not ruta_json.exists():
        print()
        print("ERROR: No existe el archivo JSON.")
        print(ruta_json)
        return

    print()
    print("Cargando JSON...")

    try:
        with open(
            ruta_json,
            "r",
            encoding="utf-8"
        ) as archivo:
            datos = json.load(archivo)

        print("JSON cargado correctamente.")

    except Exception as e:
        print()
        print("ERROR AL CARGAR JSON:")
        print(e)
        return

    print()
    print("=" * 100)
    print("INFORMACIÓN DEL COMPROBANTE")
    print("=" * 100)

    print()
    print("Archivo:")
    print(datos.get("archivo"))

    print()
    print("Banco:")
    print(datos.get("banco"))

    print()
    print("Ancho:")
    print(datos.get("ancho"))

    print()
    print("Alto:")
    print(datos.get("alto"))

    detecciones = datos.get("detecciones", [])

    print()
    print(f"Detecciones OCR: {len(detecciones)}")

    print()
    print("=" * 100)
    print("DETECCIONES OCR")
    print("=" * 100)

    for i, deteccion in enumerate(detecciones):

        texto = deteccion.get("texto", "")

        confianza = deteccion.get(
            "confianza",
            0
        )

        x = deteccion.get("x", 0)
        y = deteccion.get("y", 0)
        ancho = deteccion.get("ancho", 0)
        alto = deteccion.get("alto", 0)

        print(
            f"{i:03d} | "
            f"x={x:7.2f} "
            f"y={y:7.2f} "
            f"ancho={ancho:7.2f} "
            f"alto={alto:7.2f} "
            f"conf={confianza:.4f} | "
            f"{texto}"
        )

    print()
    print("=" * 100)
    print("EJECUTANDO EXTRACTOR BANBAJIO")
    print("=" * 100)

    extractor = BanBajioExtractor()

    resultado = extractor.extraer(datos)

    print()
    print("=" * 100)
    print("RESULTADO DEL EXTRACTOR")
    print("=" * 100)

    print()
    print("Banco:")
    print(resultado.get("banco"))

    print()
    print("Campos:")

    campos = resultado.get(
        "campos",
        {}
    )

    for nombre, valor in campos.items():

        print()
        print(nombre)
        print("-" * 70)
        print(f"Valor: {valor}")

    print()
    print("=" * 100)
    print("FIN DE LA PRUEBA")
    print("=" * 100)


if __name__ == "__main__":
    main()