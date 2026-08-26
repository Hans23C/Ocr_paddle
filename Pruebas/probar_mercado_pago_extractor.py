from pathlib import Path
import json
from contextlib import redirect_stdout

from Services.extractores.mercado_pago.mercado_pago import extraer


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = (
    Path(__file__).resolve().parent.parent
)

CARPETA_RESULTADOS = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "MERCADO_PAGO"
)

ARCHIVO_TXT = (
    CARPETA_RESULTADOS
    / "resultado_extractor.txt"
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

SEPARADOR = "#" * 100


# ============================================================
# DETERMINAR SI UN CAMPO FUE ENCONTRADO
# ============================================================

def campo_fue_encontrado(campo):

    if not campo:
        return False

    valor = campo.get(
        "valor"
    )

    if valor is None:
        return False

    valor = str(
        valor
    ).strip()

    if not valor:
        return False

    if valor.upper() == "NO ENCONTRADO":
        return False

    return True


# ============================================================
# MOSTRAR CAMPO
# ============================================================

def mostrar_campo(
    nombre,
    campo
):

    if not campo_fue_encontrado(
        campo
    ):

        print(
            f"{nombre:<45} → NO ENCONTRADO"
        )

        return False

    valor = campo.get(
        "valor"
    )

    metodo = campo.get(
        "metodo",
        "N/A"
    )

    confianza = campo.get(
        "confianza",
        0.0
    )

    try:

        confianza = float(
            confianza
        )

    except (
        TypeError,
        ValueError
    ):

        confianza = 0.0

    print(
        f"{nombre:<45} → "
        f"{str(valor):<50} "
        f"método={metodo} "
        f"conf={confianza:.2f}"
    )

    bbox = campo.get(
        "bbox"
    )

    if bbox:

        print(
            f"{'':45}   "
            f"BBox: "
            f"x={bbox.get('x', 0):.6f} "
            f"y={bbox.get('y', 0):.6f} "
            f"w={bbox.get('w', 0):.6f} "
            f"h={bbox.get('h', 0):.6f}"
        )

    return True


# ============================================================
# PROCESAR ARCHIVO
# ============================================================

def procesar_archivo(
    ruta_json
):

    print()
    print(SEPARADOR)

    print(
        f"ARCHIVO: {ruta_json.name}"
    )

    print(SEPARADOR)

    # --------------------------------------------------------
    # LEER JSON
    # --------------------------------------------------------

    try:

        with open(
            ruta_json,
            "r",
            encoding="utf-8"
        ) as archivo:

            datos_json = json.load(
                archivo
            )

    except Exception as error:

        print()
        print(
            "ERROR LEYENDO JSON:"
        )

        print(
            type(error).__name__
        )

        print(
            error
        )

        return False, 0, 0

    # --------------------------------------------------------
    # EJECUTAR EXTRACTOR
    # --------------------------------------------------------

    try:

        resultado = extraer(
            datos_json
        )

    except Exception as error:

        print()
        print(
            "ERROR EN EL EXTRACTOR:"
        )

        print(
            type(error).__name__
        )

        print(
            error
        )

        return False, 0, 0

    # --------------------------------------------------------
    # MOSTRAR RESULTADO
    # --------------------------------------------------------

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

    print()

    print(
        "Banco:",
        resultado.get(
            "banco",
            "N/A"
        )
    )

    print(
        "Tipo:",
        resultado.get(
            "tipo",
            "N/A"
        )
    )

    print()

    print(
        "CAMPOS:"
    )

    print(
        "-" * 100
    )

    campos = resultado.get(
        "campos",
        {}
    )

    encontrados = 0

    total = len(
        campos
    )

    # --------------------------------------------------------
    # CONTAR SOLO LOS CAMPOS REALMENTE ENCONTRADOS
    # --------------------------------------------------------

    for nombre, campo in campos.items():

        encontrado = mostrar_campo(
            nombre,
            campo
        )

        if encontrado:

            encontrados += 1

    print()

    print(
        f"Campos encontrados: "
        f"{encontrados}/{total}"
    )

    return (
        True,
        encontrados,
        total
    )


# ============================================================
# EJECUTAR PRUEBA
# ============================================================

def ejecutar():

    print()

    print(
        "=" * 100
    )

    print(
        "PRUEBA EXTRACTOR - MERCADO PAGO"
    )

    print(
        "=" * 100
    )

    print()

    print(
        "Carpeta de resultados:"
    )

    print(
        CARPETA_RESULTADOS
    )

    print()

    print(
        "Archivo TXT:"
    )

    print(
        ARCHIVO_TXT
    )

    print()

    # --------------------------------------------------------
    # VALIDAR CARPETA
    # --------------------------------------------------------

    if not CARPETA_RESULTADOS.exists():

        print(
            "ERROR: No existe la carpeta:"
        )

        print(
            CARPETA_RESULTADOS
        )

        return

    # --------------------------------------------------------
    # OBTENER JSON
    # --------------------------------------------------------

    archivos = sorted(
        CARPETA_RESULTADOS.glob(
            "*.json"
        )
    )

    print(
        f"Archivos a probar: "
        f"{len(archivos)}"
    )

    print()

    if not archivos:

        print(
            "No se encontraron archivos JSON."
        )

        return

    # --------------------------------------------------------
    # CREAR ARCHIVO TXT
    # --------------------------------------------------------

    with open(
        ARCHIVO_TXT,
        "w",
        encoding="utf-8"
    ) as archivo_txt:

        with redirect_stdout(
            archivo_txt
        ):

            print(
                "=" * 100
            )

            print(
                "PRUEBA EXTRACTOR - MERCADO PAGO"
            )

            print(
                "=" * 100
            )

            print()

            print(
                "Carpeta de resultados:"
            )

            print(
                CARPETA_RESULTADOS
            )

            print()

            print(
                f"Archivos a probar: "
                f"{len(archivos)}"
            )

            print()

            # ------------------------------------------------
            # CONTADORES
            # ------------------------------------------------

            procesados = 0
            errores = 0

            total_encontrados = 0
            total_campos = 0

            # ------------------------------------------------
            # PROCESAR TODOS LOS JSON
            # ------------------------------------------------

            for ruta_json in archivos:

                (
                    correcto,
                    encontrados,
                    total
                ) = procesar_archivo(
                    ruta_json
                )

                if correcto:

                    procesados += 1

                    total_encontrados += (
                        encontrados
                    )

                    total_campos += (
                        total
                    )

                else:

                    errores += 1

            # ------------------------------------------------
            # RESUMEN
            # ------------------------------------------------

            print()

            print(
                "=" * 100
            )

            print(
                "PRUEBA TERMINADA"
            )

            print(
                "=" * 100
            )

            print()

            print(
                f"Archivos procesados: "
                f"{procesados}"
            )

            print(
                f"Archivos con error: "
                f"{errores}"
            )

            print()

            print(
                f"Campos encontrados en total: "
                f"{total_encontrados}/"
                f"{total_campos}"
            )

            print()

            if total_campos > 0:

                porcentaje = (
                    total_encontrados
                    / total_campos
                ) * 100

                print(
                    f"Porcentaje global REAL: "
                    f"{porcentaje:.2f}%"
                )

            print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    ejecutar()