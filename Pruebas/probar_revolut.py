from pathlib import Path
import json
import sys

from Services.extractores.revolut.revolut import (
    RevolutExtractor
)


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_JSON = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "REVOLUT"
)


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print("=" * 100)
    print("PRUEBA FINAL MASIVA - REVOLUT")
    print("=" * 100)

    print()

    print("Carpeta de JSON:")

    print(
        CARPETA_JSON
    )

    print()

    # --------------------------------------------------------
    # VALIDAR CARPETA
    # --------------------------------------------------------

    if not CARPETA_JSON.exists():

        print(
            "ERROR: No existe la carpeta de JSON."
        )

        print()

        print(
            CARPETA_JSON
        )

        sys.exit(1)

    # --------------------------------------------------------
    # BUSCAR JSON
    # --------------------------------------------------------

    archivos_json = sorted(
        CARPETA_JSON.glob("*.json")
    )

    print(
        f"JSON encontrados: "
        f"{len(archivos_json)}"
    )

    print()

    if not archivos_json:

        print(
            "ERROR: No se encontraron archivos JSON."
        )

        print()

        sys.exit(1)

    # --------------------------------------------------------
    # EXTRACTOR
    # --------------------------------------------------------

    extractor = RevolutExtractor()

    # --------------------------------------------------------
    # CONTADORES
    # --------------------------------------------------------

    total_archivos = len(
        archivos_json
    )

    archivos_ok = 0
    archivos_error = 0

    total_campos = 0
    campos_encontrados = 0
    campos_no_encontrados = 0

    # --------------------------------------------------------
    # PROCESAR ARCHIVOS
    # --------------------------------------------------------

    for indice, ruta_json in enumerate(
        archivos_json,
        start=1
    ):

        print("=" * 100)

        print(
            f"[{indice}/{total_archivos}] "
            f"{ruta_json.name}"
        )

        print("=" * 100)

        print()

        # ----------------------------------------------------
        # CARGAR JSON
        # ----------------------------------------------------

        try:

            with open(
                ruta_json,
                "r",
                encoding="utf-8"
            ) as archivo:

                datos = json.load(
                    archivo
                )

        except Exception as error:

            archivos_error += 1

            print(
                "ERROR LEYENDO JSON:"
            )

            print(
                f"{type(error).__name__}: "
                f"{error}"
            )

            print()

            continue

        # ----------------------------------------------------
        # OCR
        # ----------------------------------------------------

        detecciones = datos.get(
            "detecciones",
            []
        )

        print(
            f"Detecciones OCR: "
            f"{len(detecciones)}"
        )

        print()

        # ----------------------------------------------------
        # EJECUTAR EXTRACTOR
        # ----------------------------------------------------

        try:

            resultado = extractor.extraer(
                datos
            )

        except Exception as error:

            archivos_error += 1

            print(
                "ERROR EJECUTANDO EXTRACTOR:"
            )

            print(
                f"{type(error).__name__}: "
                f"{error}"
            )

            print()

            continue

        archivos_ok += 1

        # ----------------------------------------------------
        # BANCO
        # ----------------------------------------------------

        print(
            f"Banco: "
            f"{resultado.get('banco')}"
        )

        print(
            f"Tipo:  "
            f"{resultado.get('tipo')}"
        )

        print()

        # ----------------------------------------------------
        # CAMPOS
        # ----------------------------------------------------

        campos = resultado.get(
            "campos",
            {}
        )

        if not campos:

            print(
                "No hay campos extraídos."
            )

            print()

            continue

        encontrados_archivo = 0
        no_encontrados_archivo = 0

        for nombre, datos_campo in campos.items():

            valor = datos_campo.get(
                "valor",
                "NO ENCONTRADO"
            )

            metodo = datos_campo.get(
                "metodo",
                "N/A"
            )

            confianza = datos_campo.get(
                "confianza",
                0
            )

            total_campos += 1

            if valor == "NO ENCONTRADO":

                no_encontrados_archivo += 1
                campos_no_encontrados += 1

                estado = "NO ENCONTRADO"

            else:

                encontrados_archivo += 1
                campos_encontrados += 1

                estado = "OK"

            print(
                f"{nombre:<25} | "
                f"{estado:<14} | "
                f"{valor}"
            )

            print(
                f"{'':<25} | "
                f"Método: {metodo}"
            )

            print(
                f"{'':<25} | "
                f"Confianza: {confianza:.4f}"
            )

            print()

        # ----------------------------------------------------
        # RESUMEN DEL ARCHIVO
        # ----------------------------------------------------

        total_campos_archivo = (
            encontrados_archivo
            + no_encontrados_archivo
        )

        print("-" * 100)

        print(
            f"Resumen archivo: "
            f"{encontrados_archivo}/"
            f"{total_campos_archivo} "
            f"campos encontrados"
        )

        if total_campos_archivo > 0:

            porcentaje_archivo = (
                encontrados_archivo
                / total_campos_archivo
            ) * 100

            print(
                f"Porcentaje: "
                f"{porcentaje_archivo:.2f}%"
            )

        print()

    # ========================================================
    # RESUMEN FINAL
    # ========================================================

    print()
    print("=" * 100)
    print("RESUMEN FINAL")
    print("=" * 100)

    print()

    print(
        f"Total de JSON:          "
        f"{total_archivos}"
    )

    print(
        f"Archivos procesados:    "
        f"{archivos_ok}"
    )

    print(
        f"Archivos con error:     "
        f"{archivos_error}"
    )

    print()

    print(
        f"Total de campos:        "
        f"{total_campos}"
    )

    print(
        f"Campos encontrados:     "
        f"{campos_encontrados}"
    )

    print(
        f"Campos no encontrados:  "
        f"{campos_no_encontrados}"
    )

    print()

    if total_campos > 0:

        porcentaje_total = (
            campos_encontrados
            / total_campos
        ) * 100

        print(
            f"Porcentaje general:     "
            f"{porcentaje_total:.2f}%"
        )

    print()

    # --------------------------------------------------------
    # ESTADO FINAL
    # --------------------------------------------------------

    if (
        archivos_error == 0
        and total_campos > 0
        and campos_no_encontrados == 0
    ):

        print(
            "RESULTADO FINAL: "
            "TODOS LOS COMPROBANTES "
            "Y CAMPOS FUERON PROCESADOS CORRECTAMENTE."
        )

    elif archivos_error > 0:

        print(
            "RESULTADO FINAL: "
            "HAY ARCHIVOS CON ERROR."
        )

    else:

        print(
            "RESULTADO FINAL: "
            "HAY CAMPOS NO ENCONTRADOS."
        )

    print()

    print("=" * 100)
    print("FIN DE PRUEBA MASIVA")
    print("=" * 100)

    print()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    main()