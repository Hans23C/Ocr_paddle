from pathlib import Path
import json
import sys

from Services.extractores.stori.stori import (
    StoriExtractor
)


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_JSON = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "STORI"
)


# ============================================================
# PROCESAR ARCHIVO
# ============================================================

def procesar_archivo(ruta_json, extractor):

    print()
    print("-" * 100)
    print(f"ARCHIVO: {ruta_json.name}")
    print("-" * 100)

    try:

        with open(
            ruta_json,
            "r",
            encoding="utf-8"
        ) as archivo:

            datos = json.load(archivo)

    except Exception as e:

        print(f"ERROR AL CARGAR JSON: {e}")
        return False

    try:

        resultado = extractor.extraer(datos)

    except Exception as e:

        print(f"ERROR EN EXTRACTOR: {e}")
        return False

    print()
    print("RESULTADO:")

    print(f"Banco: {resultado.get('banco')}")
    print(f"Tipo:  {resultado.get('tipo')}")

    print()
    print("Campos:")

    campos = resultado.get("campos", {})

    for nombre, informacion in campos.items():

        print()
        print(nombre)
        print("-" * 70)

        print(
            f"Valor:      {informacion.get('valor')}"
        )

        print(
            f"Método:     {informacion.get('metodo')}"
        )

        print(
            f"Confianza:  "
            f"{informacion.get('confianza', 0.0):.4f}"
        )

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 100)
    print("PRUEBA MASIVA - STORI")
    print("=" * 100)

    print()
    print("Carpeta:")
    print(CARPETA_JSON)

    # --------------------------------------------------------
    # VALIDAR CARPETA
    # --------------------------------------------------------

    if not CARPETA_JSON.exists():

        print()
        print("ERROR:")
        print("La carpeta de resultados OCR no existe.")

        sys.exit(1)

    # --------------------------------------------------------
    # BUSCAR JSON
    # --------------------------------------------------------

    archivos_json = sorted(
        CARPETA_JSON.glob("*.json")
    )

    print()
    print(
        f"Archivos JSON encontrados: "
        f"{len(archivos_json)}"
    )

    if not archivos_json:

        print()
        print("No se encontraron archivos JSON.")

        sys.exit(1)

    # --------------------------------------------------------
    # MOSTRAR ARCHIVOS
    # --------------------------------------------------------

    print()

    for indice, ruta in enumerate(
        archivos_json,
        start=1
    ):

        print(
            f"{indice:03d} | {ruta.name}"
        )

    # --------------------------------------------------------
    # CREAR EXTRACTOR
    # --------------------------------------------------------

    extractor = StoriExtractor()

    # --------------------------------------------------------
    # PROCESAMIENTO
    # --------------------------------------------------------

    exitosos = 0
    errores = 0

    print()
    print("=" * 100)
    print("PROCESANDO COMPROBANTES")
    print("=" * 100)

    for ruta_json in archivos_json:

        correcto = procesar_archivo(
            ruta_json,
            extractor
        )

        if correcto:
            exitosos += 1
        else:
            errores += 1

    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print("RESUMEN DE PRUEBA MASIVA")
    print("=" * 100)

    print()
    print(f"Total de archivos: {len(archivos_json)}")
    print(f"Procesados correctamente: {exitosos}")
    print(f"Con errores: {errores}")

    print()

    if errores == 0:

        print(
            "RESULTADO FINAL: "
            "TODOS LOS COMPROBANTES PROCESADOS CORRECTAMENTE"
        )

    else:

        print(
            "RESULTADO FINAL: "
            "SE DETECTARON ERRORES"
        )

    print()
    print("=" * 100)
    print("FIN DE PRUEBA MASIVA")
    print("=" * 100)


# ============================================================
# EJECUCION
# ============================================================

if __name__ == "__main__":
    main()