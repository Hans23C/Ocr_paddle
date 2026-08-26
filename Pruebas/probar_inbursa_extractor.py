from pathlib import Path
import json

from Services.extractores.inbursa.inbursa import (
    extraer
)


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

CARPETA_RESULTADOS = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "INBURSA"
)


# ============================================================
# OBTENER JSON
# ============================================================

def obtener_archivos():

    return sorted(
        archivo
        for archivo in CARPETA_RESULTADOS.iterdir()
        if (
            archivo.suffix.lower() == ".json"
            and archivo.name.startswith("image_")
        )
    )


# ============================================================
# MOSTRAR CAMPO
# ============================================================

def mostrar_campo(
    nombre,
    datos
):

    valor = datos.get(
        "valor"
    )

    metodo = datos.get(
        "metodo",
        "NO ENCONTRADO"
    )

    confianza = datos.get(
        "confianza",
        0.0
    )

    if valor is None:
        valor = "NO ENCONTRADO"

    print(
        f"{nombre:<30} → "
        f"{valor}"
    )

    if metodo != "NO ENCONTRADO":

        print(
            f"{'':30}   "
            f"método={metodo} "
            f"conf={confianza:.2f}"
        )

        bbox = datos.get(
            "bbox"
        )

        if bbox:

            print(
                f"{'':30}   "
                f"BBox: "
                f"x={bbox.get('x', 0):.6f} "
                f"y={bbox.get('y', 0):.6f} "
                f"w={bbox.get('w', 0):.6f} "
                f"h={bbox.get('h', 0):.6f}"
            )


# ============================================================
# PROBAR ARCHIVO
# ============================================================

def probar_archivo(
    ruta
):

    print()
    print(
        "#" * 100
    )

    print(
        f"ARCHIVO: {ruta.name}"
    )

    print(
        "#" * 100
    )

    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as archivo:

        datos_json = json.load(
            archivo
        )

    resultado = extraer(
        datos_json
    )

    print()
    print(
        "=" * 100
    )

    print(
        "RESULTADO DEL EXTRACTOR"
    )

    print(
        "=" * 100
    )

    print()

    print(
        f"Banco: "
        f"{resultado.get('banco', 'INBURSA')}"
    )

    print(
        f"Tipo: "
        f"{resultado.get('tipo', 'DESCONOCIDO')}"
    )

    print()

    print(
        "CAMPOS:"
    )

    print(
        "-" * 100
    )

    campos = resultado.get(
        "campos",
        {}
    )

    encontrados = 0
    total = len(campos)

    for nombre, datos in campos.items():

        valor = datos.get(
            "valor"
        )

        if valor:

            encontrados += 1

        mostrar_campo(
            nombre,
            datos
        )

    print()

    print(
        f"Campos encontrados: "
        f"{encontrados}/{total}"
    )

    print()


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "=" * 100
    )

    print(
        "PRUEBA EXTRACTOR - INBURSA"
    )

    print(
        "=" * 100
    )

    print()

    print(
        "Carpeta de resultados:"
    )

    print(
        CARPETA_RESULTADOS
    )

    print()

    if not CARPETA_RESULTADOS.exists():

        print(
            "ERROR: No existe la carpeta:"
        )

        print(
            CARPETA_RESULTADOS
        )

        return

    archivos = obtener_archivos()

    print(
        f"Archivos a probar: "
        f"{len(archivos)}"
    )

    if not archivos:

        print()
        print(
            "ERROR: No se encontraron "
            "archivos JSON."
        )

        return

    for ruta in archivos:

        probar_archivo(
            ruta
        )

    print()
    print(
        "=" * 100
    )

    print(
        "PRUEBA TERMINADA"
    )

    print(
        "=" * 100
    )

    print()

    print(
        f"Archivos procesados: "
        f"{len(archivos)}"
    )

    print()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    main()