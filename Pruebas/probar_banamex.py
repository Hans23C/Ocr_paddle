from pathlib import Path
import json
import sys
import io

from Services.extractores.banamex.banamex import (
    BanamexExtractor
)


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_JSON = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "BANAMEX"
)


# ============================================================
# CAMPOS ESPERADOS POR COMPROBANTE
#
# IMPORTANTE:
# No todos los comprobantes Banamex tienen los mismos campos.
# Aquí solamente evaluamos los campos que realmente existen
# en cada comprobante.
# ============================================================

CAMPOS_ESPERADOS = {

    # --------------------------------------------------------
    # TRANSFERENCIAS NORMALES
    # --------------------------------------------------------

    "image_032.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
    ],

    "image_070.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
        "concepto",
        "referencia",
    ],

    "image_084.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
    ],

    "image_104.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
        "concepto",
        "referencia",
    ],

    "image_128.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
    ],

    "image_154.json": [
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
    ],

    "image_157.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
    ],

    "image_159.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
    ],

    "image_173.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
        "concepto",
        "referencia",
    ],

    "image_174.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
    ],

    "image_196.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
    ],

    "image_203.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
        "concepto",
        "referencia",
    ],

    "image_235.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
    ],

    "image_237.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
    ],

    "image_280.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
        "concepto",
        "referencia",
    ],

    "image_284.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
        "concepto",
        "referencia",
    ],

    "image_312.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
    ],

    "image_326.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
        "concepto",
        "referencia",
    ],

    "image_327.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
    ],

    "image_350.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
        "concepto",
        "referencia",
    ],

    "image_363.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
    ],

    "image_380.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
        "concepto",
        "referencia",
    ],

    "image_384.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
    ],

    # --------------------------------------------------------
    # CEP / BANXICO
    # --------------------------------------------------------

    "image_392.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "beneficiario",
        "clave_rastreo",
        "referencia",
    ],

    "image_400.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "beneficiario",
        "clave_rastreo",
    ],

    # --------------------------------------------------------
    # BANCA NET
    # --------------------------------------------------------

    "image_409.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
        "concepto",
        "referencia",
    ],

    # --------------------------------------------------------
    # CEP / SPEI
    # --------------------------------------------------------

    "image_416.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "concepto",
        "referencia",
        "clave_rastreo",
    ],

    "image_469.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "beneficiario",
        "clave_rastreo",
        "concepto",
        "referencia",
    ],

    "image_526.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
        "concepto",
        "referencia",
    ],

    "image_529.json": [
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "clave_rastreo",
    ],
}


# ============================================================
# OBTENER VALOR
# ============================================================

def campo_encontrado(campos, nombre):

    if not isinstance(campos, dict):
        return False

    if nombre not in campos:
        return False

    valor = campos.get(nombre)

    if valor is None:
        return False

    if isinstance(valor, str):
        return bool(valor.strip())

    return bool(valor)


# ============================================================
# MOSTRAR DETECCIONES OCR
# ============================================================

def mostrar_detecciones(datos):

    detecciones = datos

    # --------------------------------------------------------
    # El JSON puede contener directamente una lista
    # o una estructura con una clave de detecciones.
    # --------------------------------------------------------

    if isinstance(datos, dict):

        for clave in [
            "detecciones",
            "resultados",
            "ocr",
            "data"
        ]:

            if isinstance(datos.get(clave), list):
                detecciones = datos[clave]
                break

    if not isinstance(detecciones, list):

        print()
        print(
            "No fue posible obtener la lista de detecciones OCR."
        )

        return

    print()
    print(
        f"Detecciones OCR: {len(detecciones)}"
    )

    print()
    print("=" * 100)
    print("DETECCIONES OCR")
    print("=" * 100)

    for indice, deteccion in enumerate(detecciones):

        if not isinstance(deteccion, dict):
            continue

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

        print(
            f"{indice:03d} | "
            f"x={float(x):.2f} "
            f"y={float(y):.2f} "
            f"conf={float(confianza):.4f} | "
            f"{texto}"
        )


# ============================================================
# MOSTRAR RESULTADO DEL EXTRACTOR
# ============================================================

def mostrar_resultado(resultado):

    print()
    print("=" * 100)
    print("RESULTADO DEL EXTRACTOR")
    print("=" * 100)

    banco = resultado.get(
        "banco",
        "NO IDENTIFICADO"
    )

    print()
    print("Banco:")
    print(banco)

    campos = resultado.get(
        "campos",
        {}
    )

    print()
    print("Campos:")

    if not campos:

        print()
        print("No se encontraron campos.")

        return

    for nombre, valor in campos.items():

        print()
        print(nombre)

        print(
            "-" * 70
        )

        print(
            f"Valor: {valor}"
        )


# ============================================================
# MAIN
# ============================================================

def ejecutar_prueba():

    print()
    print("=" * 100)
    print("PRUEBA MASIVA - BANAMEX")
    print("=" * 100)

    print()
    print("Carpeta:")
    print(CARPETA_JSON)

    archivos = sorted(
        CARPETA_JSON.glob("*.json")
    )

    print()
    print(
        f"Archivos JSON encontrados: "
        f"{len(archivos)}"
    )

    extractor = BanamexExtractor()

    total = 0
    correctos = 0
    errores = 0
    no_identificados = 0
    errores_extractor = 0

    resultados = []

    # ========================================================
    # PROCESAR TODOS LOS COMPROBANTES
    # ========================================================

    for indice, ruta_json in enumerate(
        archivos,
        start=1
    ):

        total += 1

        print()
        print("=" * 100)
        print(
            f"[{indice}/{len(archivos)}] "
            f"COMPROBANTE: {ruta_json.name}"
        )
        print("=" * 100)

        print()
        print("JSON:")
        print(ruta_json)

        # ----------------------------------------------------
        # CARGAR JSON
        # ----------------------------------------------------

        print()
        print("Cargando JSON...")

        try:

            with open(
                ruta_json,
                "r",
                encoding="utf-8"
            ) as archivo:

                datos = json.load(archivo)

            print(
                "JSON cargado correctamente."
            )

        except Exception as error:

            errores_extractor += 1

            print()
            print(
                "ERROR LEYENDO JSON:"
            )

            print(error)

            resultados.append({
                "archivo": ruta_json.name,
                "tipo": "ERROR",
                "faltantes": [],
                "error": True,
            })

            continue

        # ----------------------------------------------------
        # MOSTRAR OCR
        # ----------------------------------------------------

        mostrar_detecciones(datos)

        # ----------------------------------------------------
        # EJECUTAR EXTRACTOR
        # ----------------------------------------------------

        print()
        print("=" * 100)
        print("EJECUTANDO EXTRACTOR BANAMEX")
        print("=" * 100)

        try:

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
                type(error).__name__,
                error
            )

            resultados.append({
                "archivo": ruta_json.name,
                "tipo": "ERROR_EXTRACTOR",
                "faltantes": [],
                "error": True,
            })

            continue

        # ----------------------------------------------------
        # MOSTRAR RESULTADO
        # ----------------------------------------------------

        mostrar_resultado(
            resultado
        )

        # ----------------------------------------------------
        # BANCO
        # ----------------------------------------------------

        banco = resultado.get(
            "banco",
            "NO_IDENTIFICADO"
        )

        if not banco:

            banco = "NO_IDENTIFICADO"

        # ----------------------------------------------------
        # NO IDENTIFICADO
        # ----------------------------------------------------

        if banco == "NO_IDENTIFICADO":

            no_identificados += 1

            print()
            print(
                "ESTADO: NO IDENTIFICADO"
            )

            resultados.append({
                "archivo": ruta_json.name,
                "tipo": banco,
                "faltantes": [],
                "error": False,
                "no_identificado": True,
            })

            continue

        # ----------------------------------------------------
        # CAMPOS ESPERADOS
        # ----------------------------------------------------

        campos_esperados = CAMPOS_ESPERADOS.get(
            ruta_json.name
        )

        if campos_esperados is None:

            print()
            print(
                "ADVERTENCIA:"
            )

            print(
                "No hay estructura esperada definida "
                "para este comprobante."
            )

            resultados.append({
                "archivo": ruta_json.name,
                "tipo": banco,
                "faltantes": [],
                "error": False,
                "sin_estructura": True,
            })

            continue

        campos = resultado.get(
            "campos",
            {}
        )

        # ----------------------------------------------------
        # COMPARAR CAMPOS
        # ----------------------------------------------------

        faltantes = []

        for nombre in campos_esperados:

            if not campo_encontrado(
                campos,
                nombre
            ):

                faltantes.append(
                    nombre
                )

        encontrados = (
            len(campos_esperados)
            - len(faltantes)
        )

        if len(campos_esperados) > 0:

            porcentaje = (
                encontrados
                / len(campos_esperados)
                * 100
            )

        else:

            porcentaje = 100

        # ----------------------------------------------------
        # RESULTADO DEL COMPROBANTE
        # ----------------------------------------------------

        print()
        print("=" * 100)
        print("VALIDACIÓN DEL COMPROBANTE")
        print("=" * 100)

        print()
        print(
            f"Campos encontrados: "
            f"{encontrados}/"
            f"{len(campos_esperados)}"
        )

        print(
            f"Porcentaje: "
            f"{porcentaje:.2f}%"
        )

        if not faltantes:

            correctos += 1

            print()
            print(
                "ESTADO: CORRECTO"
            )

        else:

            errores += 1

            print()
            print(
                "ESTADO: CON ERRORES"
            )

            print()
            print(
                "CAMPOS FALTANTES:"
            )

            for campo in faltantes:

                print(
                    f"  - {campo}"
                )

        resultados.append({
            "archivo": ruta_json.name,
            "tipo": banco,
            "faltantes": faltantes,
            "error": bool(faltantes),
            "no_identificado": False,
        })

        print()
        print("=" * 100)
        print(
            f"FIN DE COMPROBANTE: "
            f"{ruta_json.name}"
        )
        print("=" * 100)

    # ========================================================
    # RESUMEN FINAL
    # ========================================================

    print()
    print()
    print("=" * 100)
    print("RESUMEN PRUEBA MASIVA - BANAMEX")
    print("=" * 100)

    print()
    print(
        f"Comprobantes procesados: "
        f"{total}"
    )

    print(
        f"Comprobantes correctos:   "
        f"{correctos}"
    )

    print(
        f"Comprobantes con errores:  "
        f"{errores}"
    )

    print(
        f"No identificados:          "
        f"{no_identificados}"
    )

    print(
        f"Errores del extractor:      "
        f"{errores_extractor}"
    )

    if total > 0:

        porcentaje_global = (
            correctos
            / total
            * 100
        )

    else:

        porcentaje_global = 0

    print()
    print(
        f"Porcentaje completamente "
        f"correctos: "
        f"{porcentaje_global:.2f}%"
    )

    # ========================================================
    # COMPROBANTES CON ERRORES
    # ========================================================

    print()
    print("=" * 100)
    print("COMPROBANTES CON ERRORES")
    print("=" * 100)

    hay_errores = False

    for resultado in resultados:

        if not resultado.get(
            "error",
            False
        ):
            continue

        hay_errores = True

        print()
        print(
            resultado["archivo"]
        )

        print(
            f"Tipo: "
            f"{resultado['tipo']}"
        )

        if resultado["faltantes"]:

            print(
                "Campos faltantes:"
            )

            for campo in resultado["faltantes"]:

                print(
                    f"  - {campo}"
                )

    if not hay_errores:

        print()
        print(
            "NINGÚN COMPROBANTE CON ERRORES"
        )

    # ========================================================
    # NO IDENTIFICADOS
    # ========================================================

    print()
    print("=" * 100)
    print("COMPROBANTES NO IDENTIFICADOS")
    print("=" * 100)

    hay_no_identificados = False

    for resultado in resultados:

        if not resultado.get(
            "no_identificado",
            False
        ):
            continue

        hay_no_identificados = True

        print(
            f"- {resultado['archivo']}"
        )

    if not hay_no_identificados:

        print(
            "NINGUNO"
        )

    # ========================================================
    # RESULTADO FINAL
    # ========================================================

    print()
    print("=" * 100)

    if (
        errores == 0
        and no_identificados == 0
        and errores_extractor == 0
    ):

        print(
            "BANAMEX: TODOS LOS COMPROBANTES "
            "CORRECTOS"
        )

    else:

        print(
            "BANAMEX: HAY COMPROBANTES "
            "QUE REQUIEREN REVISION"
        )

    print("=" * 100)

    print()


# ============================================================
# GUARDAR RESULTADO EN TXT
# ============================================================

def main():

    carpeta_resultados = (
        RAIZ_PROYECTO
        / "Resultados_Pruebas"
    )

    carpeta_resultados.mkdir(
        parents=True,
        exist_ok=True
    )

    archivo_txt = (
        carpeta_resultados
        / "resultado_masivo_banamex.txt"
    )

    # --------------------------------------------------------
    # Capturar toda la salida de la prueba
    # --------------------------------------------------------

    salida = io.StringIO()

    stdout_original = sys.stdout

    try:

        sys.stdout = salida

        ejecutar_prueba()

    finally:

        sys.stdout = stdout_original

    contenido = salida.getvalue()

    # --------------------------------------------------------
    # Guardar resultado completo en TXT
    # --------------------------------------------------------

    archivo_txt.write_text(
        contenido,
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Mostrar también el resultado en consola
    # --------------------------------------------------------

    print(contenido)

    print()
    print("=" * 100)
    print("ARCHIVO TXT GENERADO")
    print("=" * 100)
    print()
    print(archivo_txt)
    print()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    main()
