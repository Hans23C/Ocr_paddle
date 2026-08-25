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


# ============================================================
# ARCHIVOS CEP A INSPECCIONAR
# ============================================================

ARCHIVOS = [

    "image_070.json",

    "image_203.json",

    "image_469.json",

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

    print()

    print("=" * 110)

    print(
        nombre_archivo
    )

    print("=" * 110)

    # ========================================================
    # VERIFICAR ARCHIVO
    # ========================================================

    if not ruta.exists():

        print()

        print(
            "ERROR: archivo no encontrado:"
        )

        print(
            ruta
        )

        return

    # ========================================================
    # CARGAR JSON
    # ========================================================

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

    # ========================================================
    # INFORMACIÓN DE IMAGEN
    # ========================================================

    print()

    print(
        "Tamaño:"
    )

    print(
        f"{datos.get('ancho_imagen', 0)} "
        f"x "
        f"{datos.get('alto_imagen', 0)}"
    )

    print()

    print(
        "Detecciones:",
        len(detecciones)
    )

    print()

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

    print(
        "INSPECCIÓN COMPLETA DE BBOX - CEP BANAMEX"
    )

    print("=" * 110)

    print()

    print(
        "Carpeta:"
    )

    print(
        CARPETA_RESULTADOS
    )

    print()

    print(
        "Archivos a inspeccionar:",
        len(ARCHIVOS)
    )

    # ========================================================
    # PROCESAR ARCHIVOS
    # ========================================================

    for archivo in ARCHIVOS:

        inspeccionar_archivo(
            archivo
        )

    # ========================================================
    # FIN
    # ========================================================

    print()

    print("=" * 110)

    print(
        "INSPECCIÓN TERMINADA"
    )

    print("=" * 110)


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    main()