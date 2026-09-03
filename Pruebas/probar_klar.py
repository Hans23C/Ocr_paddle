from pathlib import Path
import json
import sys

from Services.extractores.klar.klar import (
    KlarExtractor
)


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_JSON = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "KLAR"
)


# ============================================================
# PROCESAR COMPROBANTE
# ============================================================

def procesar_comprobante(ruta_json):

    print()
    print("=" * 90)
    print(
        f"ARCHIVO: {ruta_json.name}"
    )
    print("=" * 90)

    print()

    print("JSON:")

    print(
        ruta_json
    )

    print()

    # --------------------------------------------------------
    # CARGAR JSON
    # --------------------------------------------------------

    print(
        "Cargando JSON..."
    )

    try:

        with open(
            ruta_json,
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

        return False

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
    print("EJECUTANDO EXTRACTOR KLAR")
    print("=" * 90)

    try:

        extractor = KlarExtractor()

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

        return False

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
    print("FIN DE COMPROBANTE")
    print("=" * 90)

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print("=" * 90)
    print("PRUEBA MASIVA - KLAR")
    print("=" * 90)

    print()

    print("Carpeta:")

    print(
        CARPETA_JSON
    )

    print()

    # --------------------------------------------------------
    # VALIDAR CARPETA
    # --------------------------------------------------------

    if not CARPETA_JSON.exists():

        print()

        print(
            "ERROR: No existe la carpeta."
        )

        print()

        print(
            CARPETA_JSON
        )

        sys.exit(1)

    # --------------------------------------------------------
    # BUSCAR JSON
    # --------------------------------------------------------

    archivos_json = sorted(
        CARPETA_JSON.glob("*.json")
    )

    print(
        f"Archivos JSON encontrados: "
        f"{len(archivos_json)}"
    )

    if not archivos_json:

        print()

        print(
            "No se encontraron archivos JSON."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # CONTADORES
    # --------------------------------------------------------

    total = len(
        archivos_json
    )

    exitosos = 0
    errores = 0

    # --------------------------------------------------------
    # PROCESAR TODOS
    # --------------------------------------------------------

    for ruta_json in archivos_json:

        resultado = procesar_comprobante(
            ruta_json
        )

        if resultado:

            exitosos += 1

        else:

            errores += 1

    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------

    print()

    print("=" * 90)
    print("RESUMEN DE LA PRUEBA MASIVA")
    print("=" * 90)

    print()

    print(
        f"Total de archivos : {total}"
    )

    print(
        f"Exitosos          : {exitosos}"
    )

    print(
        f"Con errores       : {errores}"
    )

    print()

    if errores == 0:

        print(
            "RESULTADO FINAL: "
            "TODOS LOS COMPROBANTES FUERON PROCESADOS CORRECTAMENTE."
        )

    else:

        print(
            "RESULTADO FINAL: "
            "SE ENCONTRARON ERRORES EN ALGUNOS COMPROBANTES."
        )

    print()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    main()