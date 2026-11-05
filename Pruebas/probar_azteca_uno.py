from pathlib import Path
import json
import sys

from Services.extractores.azteca.azteca import (
    AztecaExtractor
)


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_JSON = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "AZTECA"
)


# ============================================================
# COMPROBANTE A PROBAR
# ============================================================

NOMBRE_ARCHIVO = "image_391.json"


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 100)
    print("PRUEBA INDIVIDUAL - AZTECA")
    print("=" * 100)

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
    # INFORMACIÓN GENERAL
    # ========================================================

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
    print(datos.get("ancho_imagen"))

    print()
    print("Alto:")
    print(datos.get("alto_imagen"))

    # ========================================================
    # DETECCIONES
    # ========================================================

    detecciones = datos.get(
        "detecciones",
        []
    )

    print()
    print(
        f"Detecciones OCR: {len(detecciones)}"
    )

    print()
    print("=" * 100)
    print("DETECCIONES OCR")
    print("=" * 100)

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

        ancho = deteccion.get(
            "ancho",
            0
        )

        alto = deteccion.get(
            "alto",
            0
        )

        print(
            f"{i:03d} | "
            f"x={float(x):.2f} "
            f"y={float(y):.2f} "
            f"ancho={float(ancho):.2f} "
            f"alto={float(alto):.2f} "
            f"conf={float(confianza):.4f} | "
            f"{texto}"
        )

    # ========================================================
    # EJECUTAR EXTRACTOR
    # ========================================================

    print()
    print("=" * 100)
    print("EJECUTANDO EXTRACTOR AZTECA")
    print("=" * 100)

    try:

        extractor = AztecaExtractor()

        resultado = extractor.extraer(
            datos
        )

    except Exception as error:

        print()
        print("ERROR EJECUTANDO EXTRACTOR:")

        print(
            type(error).__name__,
            error
        )

        sys.exit(1)

    # ========================================================
    # MOSTRAR RESULTADO
    # ========================================================

    print()
    print("=" * 100)
    print("RESULTADO DEL EXTRACTOR")
    print("=" * 100)

    print()
    print("Banco:")
    print(
        resultado.get(
            "banco"
        )
    )

    campos = resultado.get(
        "campos",
        {}
    )

    print()
    print("Campos:")

    for nombre, valor in campos.items():

        print()
        print(nombre)

        print(
            "-" * 70
        )

        print(
            f"Valor: {valor}"
        )

    # ========================================================
    # FIN
    # ========================================================

    print()
    print("=" * 100)
    print("FIN DE PRUEBA")
    print("=" * 100)
    print()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    main()