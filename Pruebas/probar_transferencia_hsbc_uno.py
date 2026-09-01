from pathlib import Path
import json
import sys

from Services.extractores.transferencia_hsbc.transferencia_hsbc import (
    TransferenciaHSBCExtractor
)


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_JSON = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "TRANSFERENCIA_HSBC"
)


# ============================================================
# COMPROBANTE A PROBAR
# ============================================================

NOMBRE_ARCHIVO = "image_530.json"

RUTA_JSON = CARPETA_JSON / NOMBRE_ARCHIVO


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print("=" * 90)
    print("PRUEBA INDIVIDUAL - TRANSFERENCIA HSBC")
    print("=" * 90)

    print()

    print("JSON:")

    print(
        RUTA_JSON
    )

    print()

    # --------------------------------------------------------
    # VALIDAR JSON
    # --------------------------------------------------------

    if not RUTA_JSON.exists():

        print(
            "ERROR: No existe el JSON."
        )

        print()

        print(
            RUTA_JSON
        )

        sys.exit(1)

    # --------------------------------------------------------
    # CARGAR JSON
    # --------------------------------------------------------

    print(
        "Cargando JSON..."
    )

    try:

        with open(
            RUTA_JSON,
            "r",
            encoding="utf-8"
        ) as archivo:

            datos = json.load(
                archivo
            )

    except Exception as error:

        print()

        print(
            "ERROR LEYENDO JSON:"
        )

        print(
            type(error).__name__
        )

        print(
            error
        )

        sys.exit(1)

    print(
        "JSON cargado correctamente."
    )

    # --------------------------------------------------------
    # OCR
    # --------------------------------------------------------

    detecciones = datos.get(
        "detecciones",
        []
    )

    print()

    print(
        f"Detecciones OCR: "
        f"{len(detecciones)}"
    )

    # --------------------------------------------------------
    # MOSTRAR DETECCIONES
    # --------------------------------------------------------

    print()

    print("=" * 90)
    print("DETECCIONES OCR")
    print("=" * 90)

    for indice, deteccion in enumerate(
        detecciones
    ):

        print(
            f"{indice:03d} | "
            f"x={deteccion.get('x', 0):.2f} "
            f"y={deteccion.get('y', 0):.2f} "
            f"conf={deteccion.get('confianza', 0):.4f} | "
            f"{deteccion.get('texto', '')}"
        )

    # --------------------------------------------------------
    # EXTRACTOR
    # --------------------------------------------------------

    print()

    print("=" * 90)
    print("EJECUTANDO EXTRACTOR TRANSFERENCIA HSBC")
    print("=" * 90)

    try:

        extractor = TransferenciaHSBCExtractor()

        resultado = extractor.extraer(
            datos
        )

    except Exception as error:

        print()

        print(
            "ERROR EJECUTANDO EXTRACTOR:"
        )

        print(
            type(error).__name__
        )

        print(
            error
        )

        sys.exit(1)

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    print()

    print("=" * 90)
    print("RESULTADO DEL EXTRACTOR")
    print("=" * 90)

    print()

    print(
        "Banco:"
    )

    print(
        resultado.get(
            "banco"
        )
    )

    print()

    print(
        "Tipo:"
    )

    print(
        resultado.get(
            "tipo"
        )
    )

    print()

    print(
        "Campos:"
    )

    campos = resultado.get(
        "campos",
        {}
    )

    if not campos:

        print(
            "No hay campos extraídos todavía."
        )

    else:

        for nombre, datos_campo in campos.items():

            print()

            print(
                nombre
            )

            print(
                "-" * 70
            )

            print(
                f"Valor:      "
                f"{datos_campo.get('valor')}"
            )

            print(
                f"Método:     "
                f"{datos_campo.get('metodo', 'N/A')}"
            )

            print(
                f"Confianza:  "
                f"{datos_campo.get('confianza', 0):.4f}"
            )

    print()

    print("=" * 90)
    print("FIN DE PRUEBA")
    print("=" * 90)

    print()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    main()