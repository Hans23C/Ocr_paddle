from pathlib import Path
import json


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_RESULTADOS = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "BANAMEX"
)


# ============================================================
# CAMPOS QUE QUEREMOS INSPECCIONAR
# ============================================================

PALABRAS_CLAVE = [

    "autorizacion",
    "autorización",

    "clabe",

    "cuenta",

    "retiro",

    "asociada",

]


# ============================================================
# NORMALIZAR
# ============================================================

def normalizar(texto):

    texto = str(texto).lower()

    reemplazos = {

        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",

    }

    for original, nuevo in reemplazos.items():

        texto = texto.replace(
            original,
            nuevo
        )

    return texto


# ============================================================
# INSPECCIONAR ARCHIVO
# ============================================================

def inspeccionar(
    ruta
):

    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as archivo:

        datos = json.load(
            archivo
        )

    print()
    print("=" * 100)
    print(datos.get("archivo"))
    print("=" * 100)

    detecciones = datos.get(
        "detecciones",
        []
    )

    encontradas = []

    # --------------------------------------------------------
    # BUSCAR PALABRAS RELACIONADAS
    # --------------------------------------------------------

    for indice, deteccion in enumerate(
        detecciones
    ):

        texto = str(
            deteccion.get(
                "texto",
                ""
            )
        ).strip()

        texto_norm = normalizar(
            texto
        )

        if any(
            palabra in texto_norm
            for palabra in PALABRAS_CLAVE
        ):

            encontradas.append(
                indice
            )

    # --------------------------------------------------------
    # MOSTRAR DETECCIONES
    # --------------------------------------------------------

    for indice in encontradas:

        deteccion = detecciones[
            indice
        ]

        print()
        print(
            f"[DETECCIÓN {indice}]"
        )

        print(
            f"Texto: "
            f"{deteccion.get('texto')}"
        )

        print(
            f"Confianza: "
            f"{deteccion.get('confianza')}"
        )

        print(
            f"x_rel: "
            f"{deteccion.get('x_rel')}"
        )

        print(
            f"y_rel: "
            f"{deteccion.get('y_rel')}"
        )

        print(
            f"ancho_rel: "
            f"{deteccion.get('ancho_rel')}"
        )

        print(
            f"alto_rel: "
            f"{deteccion.get('alto_rel')}"
        )

        print(
            "-" * 70
        )

        # ----------------------------------------------------
        # MOSTRAR DETECCIONES CERCANAS
        # ----------------------------------------------------

        inicio = max(
            0,
            indice - 3
        )

        fin = min(
            len(detecciones),
            indice + 4
        )

        print(
            "DETECCIONES CERCANAS:"
        )

        for vecino in range(
            inicio,
            fin
        ):

            d = detecciones[
                vecino
            ]

            print(

                f"  [{vecino:03d}] "

                f"{d.get('texto', ''):<50} "

                f"x={d.get('x_rel', 0):.4f} "

                f"y={d.get('y_rel', 0):.4f}"

            )


# ============================================================
# EJECUTAR
# ============================================================

def main():

    archivos = [

        CARPETA_RESULTADOS
        / "image_173.json",

        CARPETA_RESULTADOS
        / "image_326.json",

        CARPETA_RESULTADOS
        / "image_409.json",

    ]

    for archivo in archivos:

        if not archivo.exists():

            print(
                "NO EXISTE:",
                archivo
            )

            continue

        inspeccionar(
            archivo
        )


if __name__ == "__main__":

    main()