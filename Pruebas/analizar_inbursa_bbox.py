from pathlib import Path
import json



# RUTAS


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

ARCHIVOS = [
    "image_058.json",
    "image_562.json",
    "image_665.json",
    "image_670.json",
    "image_683.json",
]



# MOSTRAR UNA DETECCIÓN


def escribir_deteccion(
    archivo_salida,
    indice,
    deteccion
):

    texto = str(
        deteccion.get(
            "texto",
            ""
        )
    ).strip()

    confianza = deteccion.get(
        "confianza",
        0
    )

    x = deteccion.get(
        "x_rel",
        0
    )

    y = deteccion.get(
        "y_rel",
        0
    )

    ancho = deteccion.get(
        "ancho_rel",
        0
    )

    alto = deteccion.get(
        "alto_rel",
        0
    )

    archivo_salida.write(
        f"[{indice:02d}] {texto}\n"
    )

    archivo_salida.write(
        f"      "
        f"x={x:.6f} "
        f"y={y:.6f} "
        f"w={ancho:.6f} "
        f"h={alto:.6f} "
        f"conf={confianza:.4f}\n"
    )



# ANALIZAR ARCHIVO

def analizar_archivo(
    nombre_archivo,
    archivo_salida
):

    ruta_json = (
        CARPETA_RESULTADOS
        / nombre_archivo
    )

    if not ruta_json.exists():

        archivo_salida.write(
            f"\n"
            f"ERROR: No existe "
            f"{ruta_json}\n"
        )

        return

    with open(
        ruta_json,
        "r",
        encoding="utf-8"
    ) as archivo:

        datos = json.load(
            archivo
        )

    detecciones = datos.get(
        "detecciones",
        []
    )

    archivo_salida.write(
        "\n"
    )

    archivo_salida.write(
        "=" * 110
        + "\n"
    )

    archivo_salida.write(
        nombre_archivo
        + "\n"
    )

    archivo_salida.write(
        "=" * 110
        + "\n"
    )

    archivo_salida.write(
        f"Tamaño imagen: "
        f"{datos.get('ancho_imagen', 0)} "
        f"x "
        f"{datos.get('alto_imagen', 0)}\n"
    )

    archivo_salida.write(
        f"Detecciones: "
        f"{len(detecciones)}\n"
    )

    archivo_salida.write(
        "\n"
    )

    for indice, deteccion in enumerate(
        detecciones
    ):

        escribir_deteccion(
            archivo_salida,
            indice,
            deteccion
        )



# MAIN


def main():

    CARPETA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True
    )

    ruta_txt = (
        CARPETA_RESULTADOS
        / "analisis_inbursa_bbox.txt"
    )

    print()
    print("=" * 100)
    print("ANALISIS BBOX INBURSA")
    print("=" * 100)

    print()
    print(
        "Generando archivo:"
    )

    print(
        ruta_txt
    )

    print()

    with open(
        ruta_txt,
        "w",
        encoding="utf-8"
    ) as archivo_salida:

        archivo_salida.write(
            "=" * 110
            + "\n"
        )

        archivo_salida.write(
            "ANALISIS BBOX INBURSA\n"
        )

        archivo_salida.write(
            "=" * 110
            + "\n\n"
        )

        total = len(
            ARCHIVOS
        )

        for numero, nombre_archivo in enumerate(
            ARCHIVOS,
            start=1
        ):

            print(
                f"[{numero}/{total}] "
                f"Analizando "
                f"{nombre_archivo}..."
            )

            analizar_archivo(
                nombre_archivo,
                archivo_salida
            )

    print()
    print(
        "ANALISIS TERMINADO."
    )

    print()
    print(
        "Archivo generado:"
    )

    print(
        ruta_txt
    )

    print()



# EJECUCIÓN


if __name__ == "__main__":

    main()