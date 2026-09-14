from pathlib import Path
import json

from Services.extractores.compartamos_banco.compartamos_banco import (
    CompartamosBancoExtractor
)


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = Path(
    __file__
).resolve().parent.parent


CARPETA_JSON = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "COMPARTAMOS_BANCO"
)


# ============================================================
# COMPROBANTE A PROBAR
# ============================================================

ARCHIVO = "image_687.json"


RUTA_JSON = (
    CARPETA_JSON
    / ARCHIVO
)


# ============================================================
# EJECUCIÓN
# ============================================================

def main():

    print()
    print("=" * 90)
    print(
        "PRUEBA INDIVIDUAL - COMPARTAMOS BANCO"
    )
    print("=" * 90)

    print()
    print("JSON:")
    print(RUTA_JSON)

    print()
    print("Cargando JSON...")

    if not RUTA_JSON.exists():

        print(
            "ERROR: No existe el archivo JSON."
        )

        return

    try:

        with open(
            RUTA_JSON,
            "r",
            encoding="utf-8"
        ) as archivo:

            datos = json.load(
                archivo
            )

    except Exception as error:

        print(
            f"ERROR al cargar JSON: {error}"
        )

        return

    print(
        "JSON cargado correctamente."
    )

    detecciones = datos.get(
        "detecciones",
        []
    )

    print()
    print("=" * 90)
    print("INFORMACIÓN DEL COMPROBANTE")
    print("=" * 90)

    print()
    print(
        f"Archivo: "
        f"{datos.get('archivo')}"
    )

    print(
        f"Banco: "
        f"{datos.get('banco')}"
    )

    print(
        f"Ancho: "
        f"{datos.get('ancho_imagen')}"
    )

    print(
        f"Alto: "
        f"{datos.get('alto_imagen')}"
    )

    print(
        f"Detecciones OCR: "
        f"{len(detecciones)}"
    )

    print()
    print("=" * 90)
    print("DETECCIONES OCR")
    print("=" * 90)

    for i, deteccion in enumerate(
        detecciones
    ):

        print(
            f"{i:03d} | "
            f"x={deteccion.get('x', 0):7.2f} "
            f"y={deteccion.get('y', 0):7.2f} "
            f"ancho={deteccion.get('ancho', 0):7.2f} "
            f"alto={deteccion.get('alto', 0):7.2f} "
            f"conf={deteccion.get('confianza', 0):.4f} | "
            f"{deteccion.get('texto', '')}"
        )

    # ========================================================
    # EXTRACTOR
    # ========================================================

    print()
    print("=" * 90)
    print("EJECUTANDO EXTRACTOR COMPARTAMOS BANCO")
    print("=" * 90)

    extractor = CompartamosBancoExtractor()

    resultado = extractor.extraer(
        datos
    )

    print()
    print("=" * 90)
    print("RESULTADO DEL EXTRACTOR")
    print("=" * 90)

    print()
    print(
        f"Banco: {resultado.get('banco')}"
    )

    print(
        f"Tipo: {resultado.get('tipo')}"
    )

    campos = resultado.get(
        "campos",
        {}
    )

    print()
    print("CAMPOS:")
    print("-" * 90)

    encontrados = 0
    total = len(campos)

    for nombre, campo in campos.items():

        valor = campo.get(
            "valor"
        )

        metodo = campo.get(
            "metodo"
        )

        conf = campo.get(
            "confianza",
            0
        )

        print()
        print(
            f"{nombre:<30} → {valor}"
        )

        print(
            f"{'':30}   "
            f"método={metodo} "
            f"conf={conf:.2f}"
        )

        if valor is not None:

            encontrados += 1

    print()
    print(
        f"Campos encontrados: "
        f"{encontrados}/{total}"
    )

    print()
    print("=" * 90)
    print(
        "FIN DEL COMPROBANTE"
    )
    print("=" * 90)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    main()