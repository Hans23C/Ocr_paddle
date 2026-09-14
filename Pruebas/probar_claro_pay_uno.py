# ============================================================
# PRUEBA INDIVIDUAL - CLARO PAY
# ============================================================

import json
import os
import sys


# ============================================================
# RUTA BASE DEL PROYECTO
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if BASE_DIR not in sys.path:
    sys.path.insert(
        0,
        BASE_DIR
    )


# ============================================================
# IMPORTAR EXTRACTOR
# ============================================================

from Services.extractores.claro_pay.claro_pay import (
    crear_extractor
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

CARPETA_JSON = os.path.join(
    BASE_DIR,
    "Resultados_OCR",
    "CLARO_PAY"
)

ARCHIVO = "image_716.json"


# ============================================================
# CARGAR JSON
# ============================================================

def cargar_json(ruta):

    try:

        with open(
            ruta,
            "r",
            encoding="utf-8"
        ) as archivo:

            return json.load(
                archivo
            )

    except Exception as error:

        print(
            "\nERROR AL CARGAR EL JSON:"
        )

        print(error)

        return None


# ============================================================
# MOSTRAR OCR
# ============================================================

def mostrar_ocr(datos):

    detecciones = datos.get(
        "detecciones",
        []
    )

    print(
        "\n"
        + "=" * 100
    )

    print(
        "TEXTO DETECTADO POR PADDLE OCR"
    )

    print(
        "=" * 100
    )

    for indice, deteccion in enumerate(
        detecciones
    ):

        texto = deteccion.get(
            "texto",
            ""
        )

        x = deteccion.get(
            "x",
            0
        )

        y = deteccion.get(
            "y",
            0
        )

        confianza = deteccion.get(
            "confianza",
            0
        )

        print(
            f"{indice:03d} | "
            f"x={float(x):8.2f} | "
            f"y={float(y):8.2f} | "
            f"conf={float(confianza):.4f} | "
            f"{texto}"
        )


# ============================================================
# MOSTRAR RESULTADO
# ============================================================

def mostrar_resultado(resultado):

    print(
        "\n"
        + "=" * 100
    )

    print(
        "RESULTADO DEL EXTRACTOR - CLARO PAY"
    )

    print(
        "=" * 100
    )

    print(
        f"\nBanco:"
        f"\n{resultado.get('banco')}"
    )

    print(
        f"\nTipo:"
        f"\n{resultado.get('tipo')}"
    )

    campos = resultado.get(
        "campos",
        {}
    )

    print(
        "\n"
        + "-" * 100
    )

    print(
        "CAMPOS EXTRAÍDOS"
    )

    print(
        "-" * 100
    )

    for campo, valor in campos.items():

        if valor is None:
            valor = "NO ENCONTRADO"

        print(
            f"{campo:<20} : {valor}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n"
        + "=" * 100
    )

    print(
        "PRUEBA INDIVIDUAL - CLARO PAY"
    )

    print(
        "=" * 100
    )

    ruta_json = os.path.join(
        CARPETA_JSON,
        ARCHIVO
    )

    print(
        f"\nArchivo:"
        f"\n{ruta_json}"
    )

    # --------------------------------------------------------
    # Verificar archivo
    # --------------------------------------------------------

    if not os.path.isfile(
        ruta_json
    ):

        print(
            "\nERROR:"
        )

        print(
            "No existe el archivo:"
        )

        print(
            ruta_json
        )

        return

    # --------------------------------------------------------
    # Cargar JSON
    # --------------------------------------------------------

    datos = cargar_json(
        ruta_json
    )

    if datos is None:
        return

    print(
        "\nJSON cargado correctamente."
    )

    # --------------------------------------------------------
    # Mostrar OCR
    # --------------------------------------------------------

    mostrar_ocr(
        datos
    )

    # --------------------------------------------------------
    # Crear extractor
    # --------------------------------------------------------

    extractor = crear_extractor()

    # --------------------------------------------------------
    # Ejecutar extractor
    # --------------------------------------------------------

    try:

        resultado = extractor.extraer(
            datos
        )

    except Exception as error:

        print(
            "\n"
            + "=" * 100
        )

        print(
            "ERROR DURANTE LA EXTRACCIÓN"
        )

        print(
            "=" * 100
        )

        print(
            f"\n{type(error).__name__}: "
            f"{error}"
        )

        return

    # --------------------------------------------------------
    # Mostrar resultado
    # --------------------------------------------------------

    mostrar_resultado(
        resultado
    )

    # --------------------------------------------------------
    # FIN
    # --------------------------------------------------------

    print(
        "\n"
        + "=" * 100
    )

    print(
        "PRUEBA INDIVIDUAL TERMINADA"
    )

    print(
        "=" * 100
    )


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    main()