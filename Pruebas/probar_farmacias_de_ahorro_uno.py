# ============================================================
# PRUEBA INDIVIDUAL
# FARMACIAS DEL AHORRO
# ============================================================

import json
from pathlib import Path

from Services.extractores.farmacias_de_ahorro import (
    crear_extractor
)


# ============================================================
# CONFIGURACION
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent.parent

CARPETA_JSON = (
    BASE_DIR
    / "Resultados_OCR"
    / "FARMACIAS_DE_AHORRO"
)

ARCHIVO_JSON = (
    CARPETA_JSON
    / "image_223.json"
)


# ============================================================
# MOSTRAR DETECCIONES
# ============================================================

def mostrar_detecciones(
    datos
):

    if isinstance(
        datos,
        dict
    ):

        detecciones = datos.get(
            "detecciones",
            []
        )

    elif isinstance(
        datos,
        list
    ):

        detecciones = datos

    else:

        detecciones = []

    print()
    print(
        "=" * 100
    )

    print(
        "DETECCIONES OCR"
    )

    print(
        "=" * 100
    )

    print(
        f"Total: {len(detecciones)}"
    )

    print()

    for indice, deteccion in enumerate(
        detecciones
    ):

        if not isinstance(
            deteccion,
            dict
        ):

            continue

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
            f"{indice:03d} | "
            f"x={float(x):8.2f} "
            f"y={float(y):8.2f} "
            f"w={float(ancho):8.2f} "
            f"h={float(alto):8.2f} "
            f"conf={float(confianza):.4f} | "
            f"{texto}"
        )


# ============================================================
# MOSTRAR RESULTADO
# ============================================================

def mostrar_resultado(
    resultado
):

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

    print(
        f"Banco: {resultado.get('banco')}"
    )

    print(
        f"Tipo: {resultado.get('tipo')}"
    )

    print()

    campos = resultado.get(
        "campos",
        {}
    )

    for nombre, campo in campos.items():

        print(
            "-" * 100
        )

        print(
            nombre
        )

        if not isinstance(
            campo,
            dict
        ):

            print(
                f"Valor: {campo}"
            )

            continue

        valor = campo.get(
            "valor"
        )

        metodo = campo.get(
            "metodo",
            ""
        )

        confianza = campo.get(
            "confianza",
            0
        )

        print(
            f"Valor: {valor}"
        )

        print(
            f"Método: {metodo}"
        )

        print(
            f"Confianza: {confianza:.4f}"
        )

        bbox = campo.get(
            "bbox"
        )

        if bbox:

            print(
                "BBox: "
                f"x={bbox.get('x', 0):.2f} "
                f"y={bbox.get('y', 0):.2f} "
                f"w={bbox.get('ancho', 0):.2f} "
                f"h={bbox.get('alto', 0):.2f}"
            )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "=" * 100
    )

    print(
        "PRUEBA INDIVIDUAL - FARMACIAS DEL AHORRO"
    )

    print(
        "=" * 100
    )

    print()

    print(
        "JSON:"
    )

    print(
        ARCHIVO_JSON
    )

    if not ARCHIVO_JSON.exists():

        print()

        print(
            "ERROR: No existe el archivo JSON."
        )

        return

    # --------------------------------------------------------
    # CARGAR JSON
    # --------------------------------------------------------

    print()

    print(
        "Cargando JSON..."
    )

    try:

        with open(
            ARCHIVO_JSON,
            "r",
            encoding="utf-8"
        ) as archivo:

            datos = json.load(
                archivo
            )

    except Exception as error:

        print(
            f"ERROR AL CARGAR JSON: {error}"
        )

        return

    print(
        "JSON cargado correctamente."
    )

    # --------------------------------------------------------
    # INFORMACION
    # --------------------------------------------------------

    print()

    print(
        "=" * 100
    )

    print(
        "INFORMACION DEL COMPROBANTE"
    )

    print(
        "=" * 100
    )

    if isinstance(
        datos,
        dict
    ):

        print(
            f"Archivo: {datos.get('archivo')}"
        )

        print(
            f"Banco: {datos.get('banco')}"
        )

        print(
            f"Ancho: {datos.get('ancho_imagen')}"
        )

        print(
            f"Alto: {datos.get('alto_imagen')}"
        )

    # --------------------------------------------------------
    # DETECCIONES
    # --------------------------------------------------------

    mostrar_detecciones(
        datos
    )

    # --------------------------------------------------------
    # EJECUTAR EXTRACTOR
    # --------------------------------------------------------

    print()

    print(
        "=" * 100
    )

    print(
        "EJECUTANDO EXTRACTOR FARMACIAS DEL AHORRO"
    )

    print(
        "=" * 100
    )

    extractor = crear_extractor()

    try:

        resultado = extractor.extraer(
            datos
        )

    except Exception as error:

        print()

        print(
            "ERROR EN EL EXTRACTOR:"
        )

        print(
            error
        )

        return

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    mostrar_resultado(
        resultado
    )

    print()

    print(
        "=" * 100
    )

    print(
        "FIN DE LA PRUEBA"
    )

    print(
        "=" * 100
    )


# ============================================================
# EJECUCION
# ============================================================

if __name__ == "__main__":

    main()