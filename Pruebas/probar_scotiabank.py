from pathlib import Path
import json
import sys

from Services.extractores.scotiabank.scotiabank import ScotiabankExtractor


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_JSON = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "SCOTIABANK"
)


# ============================================================
# CAMPOS ESPERADOS
# ============================================================

CAMPOS_SCOTIABANK = [

    "banco",
    "monto",
    "fecha",
    "cuenta_ordenante",
    "cuenta_beneficiario",
    "concepto",
    "referencia",
    "folio",

]


# ============================================================
# OBTENER CAMPOS ENCONTRADOS
# ============================================================

def campos_encontrados(campos):

    encontrados = []

    for nombre in CAMPOS_SCOTIABANK:

        datos = campos.get(nombre)

        if not datos:
            continue

        valor = datos.get("valor")

        if valor is None:
            continue

        if str(valor).strip() == "":
            continue

        encontrados.append(nombre)

    return encontrados


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print("=" * 100)
    print("PRUEBA FINAL MASIVA - SCOTIABANK")
    print("=" * 100)

    print()

    print("Carpeta de JSON:")

    print(CARPETA_JSON)

    # --------------------------------------------------------
    # VALIDAR CARPETA
    # --------------------------------------------------------

    if not CARPETA_JSON.exists():

        print()

        print(
            "ERROR: No existe la carpeta de resultados OCR."
        )

        print(
            CARPETA_JSON
        )

        sys.exit(1)

    # --------------------------------------------------------
    # OBTENER JSON
    # --------------------------------------------------------

    archivos_json = sorted(
        CARPETA_JSON.glob("*.json")
    )

    print()

    print(
        f"Comprobantes encontrados: "
        f"{len(archivos_json)}"
    )

    if not archivos_json:

        print()

        print(
            "No se encontraron archivos JSON."
        )

        sys.exit(0)

    print()

    print("=" * 100)

    # ========================================================
    # CONTADORES
    # ========================================================

    total = 0
    correctos = 0
    errores = 0
    no_identificados = 0
    errores_extractor = 0

    comprobantes_con_errores = []
    comprobantes_no_identificados = []

    # ========================================================
    # CONTADORES POR TIPO
    # ========================================================

    tipos = {}

    # ========================================================
    # PROCESAR CADA COMPROBANTE
    # ========================================================

    for indice, ruta_json in enumerate(
        archivos_json,
        start=1
    ):

        total += 1

        print()

        print("=" * 100)

        print(
            f"[{indice}/{len(archivos_json)}] "
            f"{ruta_json.name}"
        )

        print("=" * 100)

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

            errores_extractor += 1

            print()

            print(
                "ERROR LEYENDO JSON:"
            )

            print(
                f"{type(error).__name__}: {error}"
            )

            continue

        # ----------------------------------------------------
        # EJECUTAR EXTRACTOR
        # ----------------------------------------------------

        try:

            extractor = ScotiabankExtractor()

            resultado = extractor.extraer(
                datos
            )

        except Exception as error:

            errores_extractor += 1

            print()

            print(
                "ERROR EJECUTANDO EXTRACTOR:"
            )

            print(
                f"{type(error).__name__}: {error}"
            )

            continue

        # ----------------------------------------------------
        # RESULTADO
        # ----------------------------------------------------

        tipo = resultado.get(
            "tipo",
            "NO_IDENTIFICADO"
        )

        campos = resultado.get(
            "campos",
            {}
        )

        print()

        print(
            f"Tipo detectado: {tipo}"
        )

        # ----------------------------------------------------
        # NO IDENTIFICADO
        # ----------------------------------------------------

        if (
            not tipo
            or tipo == "NO_IDENTIFICADO"
        ):

            no_identificados += 1

            comprobantes_no_identificados.append(
                ruta_json.name
            )

            print()

            print(
                "ESTADO: NO IDENTIFICADO"
            )

            continue

        # ----------------------------------------------------
        # REGISTRAR TIPO
        # ----------------------------------------------------

        if tipo not in tipos:

            tipos[tipo] = {
                "total": 0,
                "correctos": 0,
                "errores": 0,
            }

        tipos[tipo]["total"] += 1

        # ----------------------------------------------------
        # CAMPOS
        # ----------------------------------------------------

        encontrados = campos_encontrados(
            campos
        )

        cantidad_encontrados = len(
            encontrados
        )

        cantidad_total = len(
            CAMPOS_SCOTIABANK
        )

        faltantes = [

            campo

            for campo in CAMPOS_SCOTIABANK

            if campo not in encontrados

        ]

        porcentaje = (

            cantidad_encontrados
            / cantidad_total
            * 100

        )

        print()

        print(
            f"Campos: "
            f"{cantidad_encontrados}/"
            f"{cantidad_total}"
        )

        print(
            f"Porcentaje: "
            f"{porcentaje:.2f}%"
        )

        # ----------------------------------------------------
        # CORRECTO
        # ----------------------------------------------------

        if not faltantes:

            correctos += 1

            tipos[tipo]["correctos"] += 1

            print()

            print(
                "Estado: CORRECTO"
            )

        # ----------------------------------------------------
        # CON ERRORES
        # ----------------------------------------------------

        else:

            errores += 1

            tipos[tipo]["errores"] += 1

            comprobantes_con_errores.append(
                {
                    "archivo": ruta_json.name,
                    "tipo": tipo,
                    "faltantes": faltantes,
                }
            )

            print()

            print(
                "Estado: CON ERRORES"
            )

            print()

            print(
                "CAMPOS FALTANTES:"
            )

            for campo in faltantes:

                print(
                    f"  - {campo}"
                )

    # ========================================================
    # RESUMEN FINAL
    # ========================================================

    print()

    print("=" * 100)
    print("RESUMEN FINAL SCOTIABANK")
    print("=" * 100)

    print()

    print(
        f"Total comprobantes: "
        f"{total}"
    )

    print(
        f"Correctos:          "
        f"{correctos}"
    )

    print(
        f"Con errores:        "
        f"{errores}"
    )

    print(
        f"No identificados:   "
        f"{no_identificados}"
    )

    print(
        f"Errores extractor:   "
        f"{errores_extractor}"
    )

    if total > 0:

        porcentaje_final = (

            correctos
            / total
            * 100

        )

    else:

        porcentaje_final = 0

    print(
        f"Porcentaje de comprobantes "
        f"completamente correctos: "
        f"{porcentaje_final:.2f}%"
    )

    # ========================================================
    # RESULTADO POR TIPO
    # ========================================================

    print()

    print("=" * 100)
    print("RESULTADO POR TIPO DE COMPROBANTE")
    print("=" * 100)

    for tipo, datos_tipo in tipos.items():

        total_tipo = datos_tipo["total"]

        correctos_tipo = datos_tipo["correctos"]

        errores_tipo = datos_tipo["errores"]

        if total_tipo > 0:

            porcentaje_tipo = (

                correctos_tipo
                / total_tipo
                * 100

            )

        else:

            porcentaje_tipo = 0

        print()

        print(tipo)

        print(
            "-" * 70
        )

        print(
            f"Total:       {total_tipo}"
        )

        print(
            f"Correctos:   {correctos_tipo}"
        )

        print(
            f"Errores:     {errores_tipo}"
        )

        print(
            f"Porcentaje:  "
            f"{porcentaje_tipo:.2f}%"
        )

    # ========================================================
    # COMPROBANTES CON ERRORES
    # ========================================================

    print()

    print("=" * 100)
    print("COMPROBANTES CON ERRORES")
    print("=" * 100)

    if not comprobantes_con_errores:

        print()

        print(
            "NINGUNO"
        )

    else:

        for comprobante in comprobantes_con_errores:

            print()

            print(
                comprobante["archivo"]
            )

            print(
                f"Tipo: "
                f"{comprobante['tipo']}"
            )

            print(
                "Faltantes:"
            )

            for campo in comprobante["faltantes"]:

                print(
                    f"  - {campo}"
                )

    # ========================================================
    # NO IDENTIFICADOS
    # ========================================================

    print()

    print("=" * 100)
    print("COMPROBANTES NO IDENTIFICADOS")
    print("=" * 100)

    if not comprobantes_no_identificados:

        print()

        print(
            "NINGUNO"
        )

    else:

        for archivo in comprobantes_no_identificados:

            print(
                f"- {archivo}"
            )

    # ========================================================
    # ESTADO FINAL
    # ========================================================

    print()

    print("=" * 100)

    if (
        errores == 0
        and no_identificados == 0
        and errores_extractor == 0
    ):

        print(
            "SCOTIABANK: TODOS LOS COMPROBANTES CORRECTOS"
        )

    else:

        print(
            "SCOTIABANK: HAY COMPROBANTES "
            "QUE REQUIEREN REVISION"
        )

    print("=" * 100)

    print()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    main()