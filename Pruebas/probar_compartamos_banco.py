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
# FORMATO DE SALIDA
# ============================================================

def imprimir_resultado(
    archivo,
    resultado
):

    print()
    print("=" * 90)
    print(
        f"ARCHIVO: {archivo}"
    )
    print("=" * 90)

    print()
    print(
        f"Banco: "
        f"{resultado.get('banco')}"
    )

    print(
        f"Tipo: "
        f"{resultado.get('tipo')}"
    )

    print()
    print("CAMPOS:")
    print("-" * 90)

    campos = resultado.get(
        "campos",
        {}
    )

    encontrados = 0

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
        f"{encontrados}/{len(campos)}"
    )

    return encontrados


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 90)
    print(
        "PRUEBA MASIVA - COMPARTAMOS BANCO"
    )
    print("=" * 90)

    print()
    print("Carpeta:")

    print(
        CARPETA_JSON
    )

    if not CARPETA_JSON.exists():

        print()
        print(
            "ERROR: No existe la carpeta."
        )

        return

    archivos = sorted(
        CARPETA_JSON.glob(
            "*.json"
        )
    )

    print()
    print(
        f"Archivos JSON encontrados: "
        f"{len(archivos)}"
    )

    if not archivos:

        print()
        print(
            "No hay archivos JSON."
        )

        return

    extractor = (
        CompartamosBancoExtractor()
    )

    total_encontrados = 0
    total_campos = 0

    for numero, ruta in enumerate(
        archivos,
        start=1
    ):

        print()
        print("#" * 90)
        print(
            f"COMPROBANTE "
            f"{numero} DE "
            f"{len(archivos)}"
        )
        print("#" * 90)

        try:

            with open(
                ruta,
                "r",
                encoding="utf-8"
            ) as archivo:

                datos = json.load(
                    archivo
                )

        except Exception as error:

            print()
            print(
                f"ERROR leyendo "
                f"{ruta.name}: {error}"
            )

            continue

        resultado = extractor.extraer(
            datos
        )

        encontrados = imprimir_resultado(
            ruta.name,
            resultado
        )

        campos = resultado.get(
            "campos",
            {}
        )

        total_encontrados += (
            encontrados
        )

        total_campos += len(
            campos
        )

    print()
    print("=" * 90)
    print(
        "RESUMEN FINAL"
    )
    print("=" * 90)

    print()
    print(
        f"Comprobantes procesados: "
        f"{len(archivos)}"
    )

    print(
        f"Campos encontrados: "
        f"{total_encontrados}/"
        f"{total_campos}"
    )

    if total_campos:

        porcentaje = (
            total_encontrados
            / total_campos
        ) * 100

        print(
            f"Porcentaje de extracción: "
            f"{porcentaje:.2f}%"
        )

    print()
    print("=" * 90)
    print(
        "PRUEBA TERMINADA"
    )
    print("=" * 90)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    main()