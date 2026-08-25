from pathlib import Path
import json

from Services.extractores.banamex.cep import extraer


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
    / "BANAMEX"
)


# ============================================================
# CEP A PROBAR
# ============================================================

ARCHIVOS = [
    "image_070.json",
    "image_203.json",
    "image_469.json",
]


# ============================================================
# CARGAR JSON
# ============================================================

def cargar_json(nombre_archivo):

    ruta = (
        CARPETA_RESULTADOS
        / nombre_archivo
    )

    if not ruta.exists():

        print()
        print("ERROR: archivo no encontrado:")
        print(ruta)

        return None

    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as archivo:

        return json.load(
            archivo
        )


# ============================================================
# MOSTRAR CAMPO
# ============================================================

def mostrar_campo(
    nombre,
    datos
):

    if not datos.get(
        "encontrado",
        False
    ):

        print(
            f"{nombre:<25} "
            "→ NO ENCONTRADO"
        )

        return

    valor = datos.get(
        "valor"
    )

    metodo = datos.get(
        "metodo",
        ""
    )

    confianza = datos.get(
        "confianza",
        0.0
    )

    print(
        f"{nombre:<25} "
        f"→ {str(valor):<40} "
        f"método={metodo} "
        f"conf={confianza:.2f}"
    )

    bbox = datos.get(
        "bbox"
    )

    if bbox:

        print(
            f"{'':25} "
            f"BBox: "
            f"x={bbox.get('x', 0):.6f} "
            f"y={bbox.get('y', 0):.6f} "
            f"w={bbox.get('ancho', 0):.6f} "
            f"h={bbox.get('alto', 0):.6f}"
        )


# ============================================================
# PROBAR ARCHIVO
# ============================================================

def probar_archivo(
    nombre_archivo
):

    print()
    print("#" * 100)
    print(
        f"ARCHIVO: {nombre_archivo}"
    )
    print("#" * 100)

    datos = cargar_json(
        nombre_archivo
    )

    if datos is None:

        return None

    resultado = extraer(
        datos
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
        "Banco:",
        resultado.get(
            "banco"
        )
    )

    print(
        "Tipo:",
        resultado.get(
            "tipo"
        )
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

    for nombre, datos_campo in campos.items():

        mostrar_campo(
            nombre,
            datos_campo
        )

        if datos_campo.get(
            "encontrado",
            False
        ):

            encontrados += 1

    print()

    print(
        "-" * 100
    )

    print(
        f"Campos encontrados: "
        f"{encontrados}/{len(campos)}"
    )

    print()

    return resultado


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 100)
    print(
        "PRUEBA EXTRACTOR CEP - BANAMEX"
    )
    print("=" * 100)

    print()

    print(
        "Carpeta de resultados:"
    )

    print(
        CARPETA_RESULTADOS
    )

    print()

    print(
        "Archivos a probar:",
        len(ARCHIVOS)
    )

    resultados = []

    for archivo in ARCHIVOS:

        try:

            resultado = probar_archivo(
                archivo
            )

            if resultado is not None:

                resultados.append(
                    resultado
                )

        except Exception as error:

            print()
            print(
                "ERROR PROCESANDO:"
            )

            print(
                archivo
            )

            print()

            print(
                type(error).__name__
            )

            print(
                error
            )

    print()
    print("=" * 100)
    print(
        "PRUEBA TERMINADA"
    )
    print("=" * 100)

    print()

    print(
        "Archivos procesados:",
        len(resultados)
    )


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    main()