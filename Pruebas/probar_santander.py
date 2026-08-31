from pathlib import Path
import json

from Services.extractores.santander.santander import SantanderExtractor


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_JSON = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "SANTANDER"
)


# ============================================================
# CAMPOS ESPERADOS POR COMPROBANTE
#
# IMPORTANTE:
# No todos los Santander tienen los mismos campos.
# Aquí solamente evaluamos los campos que realmente existen
# en cada comprobante según tu TXT.
# ============================================================

CAMPOS_ESPERADOS = {

    # --------------------------------------------------------
    # REF. SUPERMÓVIL
    # --------------------------------------------------------

    "image_089.json": [
        "banco_emisor",
        "monto",
        "fecha_hora_operacion",
        "cuenta_origen",
        "banco_destino",
        "estatus",
        "ref_supermovil",
        "tipo_operacion",
        "concepto",
    ],

    "image_145.json": [
        "banco_emisor",
        "monto",
        "fecha_hora_operacion",
        "cuenta_origen",
        "banco_destino",
        "estatus",
        "ref_supermovil",
    ],

    "image_181.json": [
        "banco_emisor",
        "monto",
        "fecha_hora_operacion",
        "cuenta_origen",
        "banco_destino",
        "estatus",
        "ref_supermovil",
        "tipo_operacion",
    ],

    "image_187.json": [
        "banco_emisor",
        "monto",
        "fecha_hora_operacion",
        "cuenta_origen",
        "banco_destino",
        "estatus",
        "ref_supermovil",
        "tipo_operacion",
    ],

    "image_339.json": [
        "banco_emisor",
        "monto",
        "fecha_hora_operacion",
        "cuenta_origen",
        "banco_destino",
        "estatus",
        "ref_supermovil",
        "tipo_operacion",
    ],

    "image_341.json": [
        "banco_emisor",
        "monto",
        "fecha_hora_operacion",
        "cuenta_origen",
        "banco_destino",
        "estatus",
        "ref_supermovil",
        "tipo_operacion",
    ],

    "image_407.json": [
        "banco_emisor",
        "monto",
        "fecha_hora_operacion",
        "cuenta_origen",
        "banco_destino",
        "estatus",
        "ref_supermovil",
        "tipo_operacion",
        "concepto",
    ],

    "image_435.json": [
        "banco_emisor",
        "monto",
        "fecha_hora_operacion",
        "cuenta_origen",
        "banco_destino",
        "estatus",
        "ref_supermovil",
    ],

    "image_527.json": [
        "banco_emisor",
        "monto",
        "fecha_hora_operacion",
        "cuenta_origen",
        "banco_destino",
        "estatus",
        "ref_supermovil",
        "tipo_operacion",
    ],

    "image_528.json": [
        "banco_emisor",
        "monto",
        "fecha_hora_operacion",
        "cuenta_origen",
        "banco_destino",
        "estatus",
        "ref_supermovil",
        "tipo_operacion",
        "concepto",
    ],

    "image_598.json": [
        "banco_emisor",
        "monto",
        "fecha_hora_operacion",
        "cuenta_origen",
        "banco_destino",
        "estatus",
        "ref_supermovil",
        "tipo_operacion",
    ],

    "image_601.json": [
        "banco_emisor",
        "monto",
        "fecha_hora_operacion",
        "cuenta_origen",
        "banco_destino",
        "estatus",
        "ref_supermovil",
        "tipo_operacion",
    ],

    "image_661.json": [
        "banco_emisor",
        "monto",
        "fecha_hora_operacion",
        "cuenta_origen",
        "banco_destino",
        "estatus",
        "ref_supermovil",
        "tipo_operacion",
    ],


    # --------------------------------------------------------
    # TRANSFERENCIA CON REFERENCIA
    # --------------------------------------------------------

    "image_125.json": [
        "banco_emisor",
        "monto",
        "fecha",
        "concepto",
        "banco_destino",
        "cuenta_destino",
        "cuenta",
        "sucursal",
        "referencia",
        "saldo_posterior",
        "hora",
        "numero_referencia",
        "clave_rastreo",
    ],

    "image_511.json": [
        "banco_emisor",
        "monto",
        "cuenta",
        "sucursal",
        "referencia",
        "saldo_posterior",
        "hora",
        "numero_referencia",
        "clave_rastreo",
    ],


    # --------------------------------------------------------
    # CEP
    # --------------------------------------------------------

    "image_140.json": [
        "institucion_emisora",
        "fecha_operacion",
        "concepto",
        "monto",
        "referencia_numerica",
        "clave_rastreo",
        "institucion_receptora",
        "titular_cuenta_beneficiario",
        "clabe_beneficiario",
    ],

    "image_493.json": [
        "institucion_emisora",
        "fecha_operacion",
        "concepto",
        "monto",
        "referencia_numerica",
        "clave_rastreo",
        "institucion_receptora",
        "titular_cuenta_beneficiario",
        "clabe_beneficiario",
    ],
}


# ============================================================
# NOMBRES BONITOS PARA MOSTRAR
# ============================================================

NOMBRES_TIPO = {
    "REF_SUPERMOVIL_SANTANDER": "REF_SUPERMOVIL_SANTANDER",
    "TRANSFERENCIA_SANTANDER_REFERENCIA": (
        "TRANSFERENCIA_SANTANDER_REFERENCIA"
    ),
    "CEP_SANTANDER": "CEP_SANTANDER",
    "NO_IDENTIFICADO": "NO_IDENTIFICADO",
}


# ============================================================
# OBTENER VALOR
# ============================================================

def campo_encontrado(campos, nombre):

    datos = campos.get(nombre)

    if not datos:
        return False

    valor = datos.get("valor")

    if valor is None:
        return False

    if isinstance(valor, str) and not valor.strip():
        return False

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 100)
    print("PRUEBA FINAL MASIVA - SANTANDER")
    print("=" * 100)

    print()
    print("Carpeta de JSON:")
    print(CARPETA_JSON)

    archivos = sorted(
        CARPETA_JSON.glob("*.json")
    )

    print()
    print(
        f"Comprobantes encontrados: "
        f"{len(archivos)}"
    )

    extractor = SantanderExtractor()

    total = 0
    correctos = 0
    errores = 0
    no_identificados = 0
    errores_extractor = 0

    resultados = []

    # ========================================================
    # PROCESAR TODOS
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

                datos = json.load(archivo)

        except Exception as error:

            errores_extractor += 1

            print()
            print("ERROR LEYENDO JSON:")
            print(error)

            resultados.append({
                "archivo": ruta_json.name,
                "tipo": "ERROR",
                "faltantes": [],
                "error": True,
            })

            continue

        # ----------------------------------------------------
        # EJECUTAR EXTRACTOR
        # ----------------------------------------------------

        try:

            resultado = extractor.extraer(
                datos
            )

        except Exception as error:

            errores_extractor += 1

            print()
            print("ERROR EJECUTANDO EXTRACTOR:")
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

        tipo = resultado.get(
            "tipo",
            "NO_IDENTIFICADO"
        )

        print()
        print(
            f"Tipo detectado: {tipo}"
        )

        # ----------------------------------------------------
        # NO IDENTIFICADO
        # ----------------------------------------------------

        if tipo == "NO_IDENTIFICADO":

            no_identificados += 1

            print(
                "ESTADO: NO IDENTIFICADO"
            )

            resultados.append({
                "archivo": ruta_json.name,
                "tipo": tipo,
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

        # Si todavía no tenemos definido el comprobante,
        # no inventamos sus campos.
        if campos_esperados is None:

            print()
            print(
                "ADVERTENCIA: "
                "No hay estructura esperada definida "
                "para este comprobante."
            )

            print(
                "No se marcará como error automáticamente."
            )

            resultados.append({
                "archivo": ruta_json.name,
                "tipo": tipo,
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
        # COMPARAR
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

        porcentaje = (
            encontrados
            / len(campos_esperados)
            * 100
        )

        # ----------------------------------------------------
        # RESULTADO
        # ----------------------------------------------------

        print()
        print(
            f"Campos: "
            f"{encontrados}/"
            f"{len(campos_esperados)}"
        )

        print(
            f"Porcentaje: "
            f"{porcentaje:.2f}%"
        )

        if not faltantes:

            correctos += 1

            print(
                "Estado: CORRECTO"
            )

        else:

            errores += 1

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

        resultados.append({
            "archivo": ruta_json.name,
            "tipo": tipo,
            "faltantes": faltantes,
            "error": bool(faltantes),
            "no_identificado": False,
        })

    # ========================================================
    # RESUMEN FINAL
    # ========================================================

    print()
    print("=" * 100)
    print("RESUMEN FINAL SANTANDER")
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

        porcentaje_global = (
            correctos
            / total
            * 100
        )

    else:

        porcentaje_global = 0

    print(
        f"Porcentaje de comprobantes "
        f"completamente correctos: "
        f"{porcentaje_global:.2f}%"
    )

    # ========================================================
    # POR TIPO
    # ========================================================

    print()
    print("=" * 100)
    print("RESULTADO POR TIPO DE COMPROBANTE")
    print("=" * 100)

    tipos = {}

    for resultado in resultados:

        if resultado.get(
            "no_identificado",
            False
        ):

            continue

        tipo = resultado.get(
            "tipo"
        )

        if tipo not in tipos:

            tipos[tipo] = {
                "total": 0,
                "correctos": 0,
                "errores": 0,
            }

        tipos[tipo]["total"] += 1

        if resultado.get(
            "error",
            False
        ):

            tipos[tipo]["errores"] += 1

        else:

            tipos[tipo]["correctos"] += 1

    for tipo, datos_tipo in tipos.items():

        total_tipo = datos_tipo["total"]
        correctos_tipo = datos_tipo["correctos"]
        errores_tipo = datos_tipo["errores"]

        porcentaje_tipo = (
            correctos_tipo
            / total_tipo
            * 100
        )

        print()
        print(tipo)
        print("-" * 70)

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
    # ERRORES
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

        print(
            "Faltantes:"
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
    # FINAL
    # ========================================================

    print()

    if (
        errores == 0
        and no_identificados == 0
        and errores_extractor == 0
    ):

        print("=" * 100)
        print(
            "SANTANDER: TODOS LOS COMPROBANTES CORRECTOS"
        )
        print("=" * 100)

    else:

        print("=" * 100)
        print(
            "SANTANDER: HAY COMPROBANTES "
            "QUE REQUIEREN REVISION"
        )
        print("=" * 100)

    print()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    main()