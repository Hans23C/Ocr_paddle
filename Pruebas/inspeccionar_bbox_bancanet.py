from pathlib import Path
import json


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


ARCHIVOS = [
    "image_173.json",
    "image_326.json",
    "image_409.json",
]


# ============================================================
# PALABRAS QUE INDICAN INICIO DE BLOQUE
# ============================================================

ETIQUETAS = [

    "cuenta de depósito",

    "cuenta de retiro",

    "detalle del pago",

    "importe",

    "tipo de cuenta",

    "concepto de pago",

    "fecha",

    "hora",

]


# ============================================================
# MOSTRAR DETECCIÓN
# ============================================================

def mostrar_deteccion(
    indice,
    deteccion
):

    texto = str(
        deteccion.get(
            "texto",
            ""
        )
    ).strip()

    print(
        f"[{indice:02d}] "
        f"{texto}"
    )

    print(
        f"      "
        f"x={deteccion.get('x_rel', 0):.6f} "
        f"y={deteccion.get('y_rel', 0):.6f} "
        f"w={deteccion.get('ancho_rel', 0):.6f} "
        f"h={deteccion.get('alto_rel', 0):.6f} "
        f"conf={deteccion.get('confianza', 0):.4f}"
    )


# ============================================================
# INSPECCIONAR ARCHIVO
# ============================================================

def inspeccionar_archivo(
    nombre_archivo
):

    ruta = (
        CARPETA_RESULTADOS
        / nombre_archivo
    )

    with open(
        ruta,
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

    print()
    print("=" * 110)
    print(nombre_archivo)
    print("=" * 110)

    # ========================================================
    # MOSTRAR TODAS LAS DETECCIONES
    # ========================================================

    for indice, deteccion in enumerate(
        detecciones
    ):

        mostrar_deteccion(
            indice,
            deteccion
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 110)
    print("INSPECCIÓN COMPLETA DE BBOX - BANCANET")
    print("=" * 110)

    for archivo in ARCHIVOS:

        inspeccionar_archivo(
            archivo
        )

    print()
    print("=" * 110)
    print("INSPECCIÓN TERMINADA")
    print("=" * 110)


if __name__ == "__main__":

    main()