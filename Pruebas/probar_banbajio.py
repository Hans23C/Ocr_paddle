from pathlib import Path
import json
import sys

from Services.extractores.banbajio.banbajio import (
    BanBajioExtractor
)


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_JSON = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "BANBAJIO"
)


def main():

    print()
    print("=" * 100)
    print("PRUEBA MASIVA - BANBAJIO")
    print("=" * 100)

    print()
    print("Carpeta:")
    print(CARPETA_JSON)

    if not CARPETA_JSON.exists():

        print()
        print("ERROR: No existe la carpeta de JSON.")
        print(CARPETA_JSON)

        return

    archivos_json = sorted(
        CARPETA_JSON.glob("*.json")
    )

    print()
    print(
        f"Archivos JSON encontrados: "
        f"{len(archivos_json)}"
    )

    if not archivos_json:

        print()
        print("ERROR: No se encontraron archivos JSON.")

        return

    # ========================================================
    # RECORRER TODOS LOS COMPROBANTES
    # ========================================================

    for numero, ruta_json in enumerate(
        archivos_json,
        start=1
    ):

        print()
        print()
        print("#" * 100)
        print(
            f"COMPROBANTE {numero} DE "
            f"{len(archivos_json)}"
        )
        print("#" * 100)

        # ====================================================
        # JSON
        # ====================================================

        print()
        print("=" * 100)
        print("PRUEBA INDIVIDUAL - BANBAJIO")
        print("=" * 100)

        print()
        print("JSON:")
        print(ruta_json)

        if not ruta_json.exists():

            print()
            print("ERROR: No existe el archivo JSON.")
            print(ruta_json)

            continue

        print()
        print("Cargando JSON...")

        try:

            with open(
                ruta_json,
                "r",
                encoding="utf-8"
            ) as archivo:

                datos = json.load(
                    archivo
                )

            print(
                "JSON cargado correctamente."
            )

        except Exception as e:

            print()
            print(
                "ERROR AL CARGAR JSON:"
            )
            print(e)

            continue

        # ====================================================
        # INFORMACIÓN DEL COMPROBANTE
        # ====================================================

        print()
        print("=" * 100)
        print("INFORMACIÓN DEL COMPROBANTE")
        print("=" * 100)

        print()
        print("Archivo:")
        print(datos.get("archivo"))

        print()
        print("Banco:")
        print(datos.get("banco"))

        print()
        print("Ancho:")
        print(datos.get("ancho"))

        print()
        print("Alto:")
        print(datos.get("alto"))

        detecciones = datos.get(
            "detecciones",
            []
        )

        print()
        print(
            f"Detecciones OCR: "
            f"{len(detecciones)}"
        )

        # ====================================================
        # DETECCIONES OCR
        # ====================================================

        print()
        print("=" * 100)
        print("DETECCIONES OCR")
        print("=" * 100)

        for i, deteccion in enumerate(
            detecciones
        ):

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
                f"{i:03d} | "
                f"x={float(x):7.2f} "
                f"y={float(y):7.2f} "
                f"ancho={float(ancho):7.2f} "
                f"alto={float(alto):7.2f} "
                f"conf={float(confianza):.4f} | "
                f"{texto}"
            )

        # ====================================================
        # EJECUTAR EXTRACTOR
        # ====================================================

        print()
        print("=" * 100)
        print("EJECUTANDO EXTRACTOR BANBAJIO")
        print("=" * 100)

        try:

            extractor = BanBajioExtractor()

            resultado = extractor.extraer(
                datos
            )

        except Exception as e:

            print()
            print(
                "ERROR AL EJECUTAR EXTRACTOR:"
            )
            print(e)

            continue

        # ====================================================
        # RESULTADO
        # ====================================================

        print()
        print("=" * 100)
        print("RESULTADO DEL EXTRACTOR")
        print("=" * 100)

        print()
        print("Banco:")
        print(
            resultado.get(
                "banco"
            )
        )

        print()
        print("Campos:")

        campos = resultado.get(
            "campos",
            {}
        )

        for nombre, valor in campos.items():

            print()
            print(nombre)
            print("-" * 70)
            print(
                f"Valor: {valor}"
            )

        # ====================================================
        # FIN DEL COMPROBANTE
        # ====================================================

        print()
        print("=" * 100)
        print(
            f"FIN DEL COMPROBANTE "
            f"{numero} DE {len(archivos_json)}"
        )
        print("=" * 100)

    # ========================================================
    # FIN PRUEBA MASIVA
    # ========================================================

    print()
    print()
    print("=" * 100)
    print("FIN DE LA PRUEBA MASIVA - BANBAJIO")
    print("=" * 100)

    print()
    print(
        f"Total de comprobantes procesados: "
        f"{len(archivos_json)}"
    )

    print()


if __name__ == "__main__":
    main()