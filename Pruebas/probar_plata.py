from pathlib import Path
import json
import sys

from Services.extractores.plata.plata import (
    PlataExtractor
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_JSON = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "PLATA"
)


# ============================================================
# PROCESAMIENTO
# ============================================================

def procesar_json(ruta_json, extractor):

    print()
    print("=" * 100)
    print(f"ARCHIVO: {ruta_json.name}")
    print("=" * 100)
    print()

    # --------------------------------------------------------
    # Cargar JSON
    # --------------------------------------------------------

    try:

        with open(
            ruta_json,
            "r",
            encoding="utf-8"
        ) as archivo:

            datos = json.load(archivo)

    except Exception as error:

        print("ERROR LEYENDO JSON:")
        print(type(error).__name__)
        print(error)
        return False

    detecciones = datos.get(
        "detecciones",
        []
    )

    print(
        f"Detecciones OCR: {len(detecciones)}"
    )

    # --------------------------------------------------------
    # Ejecutar extractor
    # --------------------------------------------------------

    try:

        resultado = extractor.extraer(
            datos
        )

    except Exception as error:

        print()
        print("ERROR EJECUTANDO EXTRACTOR:")
        print(type(error).__name__)
        print(error)
        return False

    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    print()
    print("Banco:")
    print(
        resultado.get("banco")
    )

    print()
    print("Tipo:")
    print(
        resultado.get("tipo")
    )

    print()
    print("Campos:")

    campos = resultado.get(
        "campos",
        {}
    )

    if not campos:

        print(
            "No hay campos extraídos."
        )

    else:

        for nombre, datos_campo in campos.items():

            print()
            print(nombre)
            print("-" * 70)

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

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 100)
    print("PRUEBA MASIVA - PLATA")
    print("=" * 100)
    print()

    print("Carpeta de JSON:")
    print(CARPETA_JSON)
    print()

    # --------------------------------------------------------
    # Validar carpeta
    # --------------------------------------------------------

    if not CARPETA_JSON.exists():

        print(
            "ERROR: No existe la carpeta de JSON."
        )

        print()
        print(CARPETA_JSON)

        sys.exit(1)

    # --------------------------------------------------------
    # Buscar JSON
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
            "ERROR: No se encontraron archivos JSON."
        )

        sys.exit(1)

    print()

    # --------------------------------------------------------
    # Crear extractor
    # --------------------------------------------------------

    try:

        extractor = PlataExtractor()

    except Exception as error:

        print(
            "ERROR CREANDO EXTRACTOR:"
        )

        print(
            type(error).__name__
        )

        print(error)

        sys.exit(1)

    # --------------------------------------------------------
    # Procesar todos
    # --------------------------------------------------------

    exitosos = 0
    errores = 0

    for indice, ruta_json in enumerate(
        archivos_json,
        start=1
    ):

        print()
        print(
            f"[{indice}/{len(archivos_json)}] "
            f"Procesando..."
        )

        resultado = procesar_json(
            ruta_json,
            extractor
        )

        if resultado:

            exitosos += 1

        else:

            errores += 1

    # --------------------------------------------------------
    # Resumen
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print("RESUMEN FINAL")
    print("=" * 100)
    print()

    print(
        f"Total de archivos: {len(archivos_json)}"
    )

    print(
        f"Procesados correctamente: {exitosos}"
    )

    print(
        f"Con errores: {errores}"
    )

    print()

    if errores == 0:

        print(
            "RESULTADO: TODOS LOS COMPROBANTES "
            "SE PROCESARON CORRECTAMENTE."
        )

    else:

        print(
            "RESULTADO: HUBO COMPROBANTES "
            "CON ERRORES."
        )

    print()
    print("=" * 100)
    print("FIN DE PRUEBA MASIVA - PLATA")
    print("=" * 100)
    print()


if __name__ == "__main__":
    main()