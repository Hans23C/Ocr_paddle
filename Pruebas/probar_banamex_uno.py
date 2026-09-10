from pathlib import Path
import json
import sys

from Services.extractores.banamex.banamex import (
    BanamexExtractor
)


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_JSON = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "BANAMEX"
)


# ============================================================
# COMPROBANTE A PROBAR
# ============================================================

NOMBRE_ARCHIVO = "image_392.json"


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 90)
    print("PRUEBA INDIVIDUAL - BANAMEX")
    print("=" * 90)

    ruta_json = CARPETA_JSON / NOMBRE_ARCHIVO

    print()
    print("JSON:")
    print(ruta_json)

    # ========================================================
    # VALIDAR ARCHIVO
    # ========================================================

    if not ruta_json.exists():

        print()
        print("ERROR: No existe el archivo JSON.")

        sys.exit(1)

    # ========================================================
    # CARGAR JSON
    # ========================================================

    print()
    print("Cargando JSON...")

    try:

        with open(
            ruta_json,
            "r",
            encoding="utf-8"
        ) as archivo:

            datos = json.load(archivo)

    except Exception as e:

        print()
        print("ERROR al cargar el JSON:")
        print(e)

        sys.exit(1)

    print("JSON cargado correctamente.")

    # ========================================================
    # DETECCIONES
    # ========================================================

    detecciones = datos.get(
        "detecciones",
        []
    )

    print()
    print(f"Detecciones OCR: {len(detecciones)}")

    # ========================================================
    # MOSTRAR DETECCIONES
    # ========================================================

    print()
    print("=" * 90)
    print("DETECCIONES OCR")
    print("=" * 90)

    for i, deteccion in enumerate(detecciones):

        texto = deteccion.get(
            "texto",
            ""
        )

        confianza = deteccion.get(
            "confianza",
            0
        )

        x = deteccion.get(
            "x",
            0
        )

        y = deteccion.get(
            "y",
            0
        )

        print(
            f"{i:03d} | "
            f"x={x:.2f} "
            f"y={y:.2f} "
            f"conf={confianza:.4f} | "
            f"{texto}"
        )

    # ========================================================
    # EJECUTAR EXTRACTOR
    # ========================================================

    print()
    print("=" * 90)
    print("EJECUTANDO EXTRACTOR BANAMEX")
    print("=" * 90)

    extractor = BanamexExtractor()

    resultado = extractor.extraer(
        datos
    )

    # ========================================================
    # MOSTRAR RESULTADO
    # ========================================================

    print()
    print("=" * 90)
    print("RESULTADO DEL EXTRACTOR")
    print("=" * 90)

    print()
    print("Banco:")
    print(resultado.get("banco"))

    campos = resultado.get(
        "campos",
        {}
    )

    print()
    print("Campos:")

    for nombre, valor in campos.items():

        print()
        print(nombre)
        print("-" * 70)
        print(f"Valor: {valor}")

    # ========================================================
    # FIN
    # ========================================================

    print()
    print("=" * 90)
    print("FIN DE PRUEBA")
    print("=" * 90)
    print()


# ============================================================
# EJECUCION
# ============================================================

if __name__ == "__main__":
    main()