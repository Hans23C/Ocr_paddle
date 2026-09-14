
import json
import os
import sys


# ============================================================
# RUTA BASE DEL PROYECTO
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if BASE_DIR not in sys.path:
    sys.path.insert(
        0,
        BASE_DIR
    )


# ============================================================
# IMPORTAR EXTRACTOR
# ============================================================

from Services.extractores.claro_pay import (
    crear_extractor
)


# ============================================================
# CARPETA DE RESULTADOS OCR
# ============================================================

CARPETA_JSON = os.path.join(
    BASE_DIR,
    "Resultados_OCR",
    "CLARO_PAY"
)


# ============================================================
# RESULTADOS ESPERADOS
# ============================================================
#
# Estos valores corresponden a los comprobantes que
# estamos utilizando para validar Claro Pay.
#
# ============================================================

RESULTADOS_ESPERADOS = {

    "image_644.json": {

        "banco":
            "Claro Pay",

        "fecha":
            "29/06/26 12:05",

        "monto":
            "$300.00",

        "cuenta_origen":
            "Claro pay *******530",

        "cuenta_destino":
            "mnet",

        "concepto":
            "pago internet",

        "referencia":
            "2906202",

        "clave_rastreo":
            "036CLAR29062026282526981",
    },

    "image_691.json": {

        "banco":
            "Claro Pay",

        "fecha":
            "08/06/26 10:53",

        "monto":
            "$300.00",

        "cuenta_origen":
            "Claro pay *******530",

        "cuenta_destino":
            "mnet",

        "concepto":
            "Internet de Monserrath Mayen",

        "referencia":
            "806202",

        "clave_rastreo":
            "036CLAR08062026278400100",
    },

    "image_710.json": {

        "banco":
            "Claro Pay",

        "fecha":
            "09/07/26 12:16",

        "monto":
            "$350.00",

        "cuenta_origen":
            "Claro pay *******530",

        "cuenta_destino":
            "mnet",

        "concepto":
            "internet",

        "referencia":
            "907202",

        "clave_rastreo":
            "036CLAR09072026284640631",
    },

    "image_716.json": {

        "banco":
            "Claro Pay",

        "fecha":
            "07/07/26 13:36",

        "monto":
            "$300.00",

        "cuenta_origen":
            "Claro pay *******530",

        "cuenta_destino":
            "mnet",

        "concepto":
            None,

        "referencia":
            "707202",

        "clave_rastreo":
            "036CLAR07072026284291811",
    },
}


# ============================================================
# CAMPOS A COMPARAR
# ============================================================

CAMPOS = [
    "banco",
    "fecha",
    "monto",
    "cuenta_origen",
    "cuenta_destino",
    "concepto",
    "referencia",
    "clave_rastreo",
]


# ============================================================
# NORMALIZAR VALOR
# ============================================================

def normalizar_valor(valor):
    """
    Normalización únicamente para comparación.

    No modifica el valor real extraído.
    """

    if valor is None:
        return None

    valor = str(
        valor
    )

    valor = valor.strip()

    valor = " ".join(
        valor.split()
    )

    return valor.lower()


# ============================================================
# OBTENER CAMPOS DEL RESULTADO
# ============================================================

def obtener_campos(resultado):
    """
    Convierte el resultado del extractor a un diccionario
    plano para facilitar la comparación.
    """

    campos = resultado.get(
        "campos",
        {}
    )

    if not isinstance(
        campos,
        dict
    ):
        campos = {}

    return {

        "banco":
            resultado.get(
                "banco"
            ),

        "fecha":
            campos.get(
                "fecha"
            ),

        "monto":
            campos.get(
                "monto"
            ),

        "cuenta_origen":
            campos.get(
                "cuenta_origen"
            ),

        "cuenta_destino":
            campos.get(
                "cuenta_destino"
            ),

        "concepto":
            campos.get(
                "concepto"
            ),

        "referencia":
            campos.get(
                "referencia"
            ),

        "clave_rastreo":
            campos.get(
                "clave_rastreo"
            ),
    }


# ============================================================
# MOSTRAR OCR
# ============================================================

def mostrar_ocr(datos):
    """
    Muestra las detecciones OCR del comprobante.
    """

    detecciones = datos.get(
        "detecciones",
        []
    )

    print(
        "\n"
        + "-" * 100
    )

    print(
        "DETECCIONES OCR"
    )

    print(
        "-" * 100
    )

    for indice, deteccion in enumerate(
        detecciones
    ):

        texto = deteccion.get(
            "texto",
            ""
        )

        x = deteccion.get(
            "x",
            0
        )

        y = deteccion.get(
            "y",
            0
        )

        confianza = deteccion.get(
            "confianza",
            0
        )

        try:
            x = float(x)
        except (
            TypeError,
            ValueError
        ):
            x = 0.0

        try:
            y = float(y)
        except (
            TypeError,
            ValueError
        ):
            y = 0.0

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
            f"{indice:03d} | "
            f"x={x:8.2f} | "
            f"y={y:8.2f} | "
            f"conf={confianza:.4f} | "
            f"{texto}"
        )


# ============================================================
# MOSTRAR RESULTADO
# ============================================================

def mostrar_resultado(
    resultado
):
    """
    Muestra los campos obtenidos por el extractor.
    """

    campos = obtener_campos(
        resultado
    )

    print(
        "\n"
        + "-" * 100
    )

    print(
        "RESULTADO DEL EXTRACTOR"
    )

    print(
        "-" * 100
    )

    for campo in CAMPOS:

        valor = campos.get(
            campo
        )

        if valor is None:

            valor_mostrar = (
                "NO ENCONTRADO"
            )

        else:

            valor_mostrar = valor

        print(
            f"{campo:<20} : "
            f"{valor_mostrar}"
        )

    return campos


# ============================================================
# COMPARAR CAMPOS
# ============================================================

def comparar_resultados(
    obtenido,
    esperado
):
    """
    Compara campo por campo.

    Devuelve:

        correctos
        errores
    """

    correctos = 0
    errores = 0

    print(
        "\n"
        + "-" * 100
    )

    print(
        "COMPARACIÓN CONTRA RESULTADO ESPERADO"
    )

    print(
        "-" * 100
    )

    for campo in CAMPOS:

        valor_obtenido = obtenido.get(
            campo
        )

        valor_esperado = esperado.get(
            campo
        )

        correcto = (
            normalizar_valor(
                valor_obtenido
            )
            ==
            normalizar_valor(
                valor_esperado
            )
        )

        if correcto:

            estado = "OK"

            correctos += 1

        else:

            estado = "ERROR"

            errores += 1

        obtenido_mostrar = (
            "None"
            if valor_obtenido is None
            else str(valor_obtenido)
        )

        esperado_mostrar = (
            "None"
            if valor_esperado is None
            else str(valor_esperado)
        )

        print(
            f"{campo:<20} | "
            f"{estado:<6} | "
            f"Obtenido: {obtenido_mostrar:<45} | "
            f"Esperado: {esperado_mostrar}"
        )

    return correctos, errores


# ============================================================
# PROCESAR ARCHIVO
# ============================================================

def procesar_archivo(
    ruta_json,
    extractor
):
    """
    Procesa un archivo JSON individual.
    """

    nombre_archivo = os.path.basename(
        ruta_json
    )

    print(
        "\n\n"
        + "=" * 100
    )

    print(
        f"ARCHIVO: {nombre_archivo}"
    )

    print(
        "=" * 100
    )

    # --------------------------------------------------------
    # Cargar JSON
    # --------------------------------------------------------

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

        print(
            "\nERROR AL CARGAR JSON:"
        )

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )

        return 0, 1

    print(
        "\nJSON cargado correctamente."
    )

    # --------------------------------------------------------
    # Mostrar cantidad de detecciones
    # --------------------------------------------------------

    detecciones = datos.get(
        "detecciones",
        []
    )

    print(
        f"Detecciones OCR: "
        f"{len(detecciones)}"
    )

    # --------------------------------------------------------
    # Mostrar OCR
    # --------------------------------------------------------

    mostrar_ocr(
        datos
    )

    # --------------------------------------------------------
    # Ejecutar extractor
    # --------------------------------------------------------

    try:

        resultado = extractor.extraer(
            datos
        )

    except Exception as error:

        print(
            "\n"
            + "-" * 100
        )

        print(
            "ERROR DURANTE LA EXTRACCIÓN"
        )

        print(
            "-" * 100
        )

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )

        return 0, 1

    # --------------------------------------------------------
    # Mostrar resultado
    # --------------------------------------------------------

    obtenido = mostrar_resultado(
        resultado
    )

    # --------------------------------------------------------
    # Obtener esperado
    # --------------------------------------------------------

    esperado = RESULTADOS_ESPERADOS.get(
        nombre_archivo
    )

    if esperado is None:

        print(
            "\nAVISO:"
        )

        print(
            "No existe resultado esperado "
            f"para {nombre_archivo}."
        )

        return 0, 0

    # --------------------------------------------------------
    # Comparar
    # --------------------------------------------------------

    correctos, errores = (
        comparar_resultados(
            obtenido,
            esperado
        )
    )

    # --------------------------------------------------------
    # Resultado del archivo
    # --------------------------------------------------------

    print(
        "\n"
        + "-" * 100
    )

    if errores == 0:

        print(
            f"RESULTADO: CORRECTO "
            f"({correctos}/{len(CAMPOS)})"
        )

    else:

        print(
            f"RESULTADO: "
            f"{correctos}/{len(CAMPOS)} "
            f"correctos, "
            f"{errores} errores"
        )

    print(
        "-" * 100
    )

    return correctos, errores


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n"
        + "=" * 100
    )

    print(
        "PRUEBA MASIVA - CLARO PAY"
    )

    print(
        "=" * 100
    )

    print(
        "\nCarpeta:"
    )

    print(
        CARPETA_JSON
    )

    # --------------------------------------------------------
    # Verificar carpeta
    # --------------------------------------------------------

    if not os.path.isdir(
        CARPETA_JSON
    ):

        print(
            "\nERROR:"
        )

        print(
            "No existe la carpeta:"
        )

        print(
            CARPETA_JSON
        )

        return

    # --------------------------------------------------------
    # Buscar archivos JSON
    # --------------------------------------------------------

    archivos = []

    for nombre in os.listdir(
        CARPETA_JSON
    ):

        if nombre.lower().endswith(
            ".json"
        ):

            archivos.append(
                nombre
            )

    archivos.sort()

    print(
        f"\nArchivos JSON encontrados: "
        f"{len(archivos)}"
    )

    if not archivos:

        print(
            "\nNo se encontraron archivos JSON."
        )

        return

    # --------------------------------------------------------
    # Mostrar archivos
    # --------------------------------------------------------

    print(
        "\nArchivos a procesar:"
    )

    for nombre in archivos:

        print(
            f"  - {nombre}"
        )

    # --------------------------------------------------------
    # Crear extractor
    # --------------------------------------------------------

    print(
        "\nInicializando extractor..."
    )

    try:

        extractor = crear_extractor()

    except Exception as error:

        print(
            "\nERROR AL CREAR EL EXTRACTOR:"
        )

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )

        return

    print(
        "Extractor inicializado correctamente."
    )

    # --------------------------------------------------------
    # Contadores
    # --------------------------------------------------------

    total_correctos = 0
    total_errores = 0
    archivos_correctos = 0
    archivos_con_error = 0

    total_campos = (
        len(archivos)
        * len(CAMPOS)
    )

    # --------------------------------------------------------
    # Procesar todos
    # --------------------------------------------------------

    for nombre in archivos:

        ruta_json = os.path.join(
            CARPETA_JSON,
            nombre
        )

        correctos, errores = (
            procesar_archivo(
                ruta_json,
                extractor
            )
        )

        total_correctos += correctos
        total_errores += errores

        if errores == 0:

            archivos_correctos += 1

        else:

            archivos_con_error += 1

    # --------------------------------------------------------
    # Porcentaje
    # --------------------------------------------------------

    if total_campos > 0:

        porcentaje = (
            total_correctos
            / total_campos
        ) * 100

    else:

        porcentaje = 0.0

    # --------------------------------------------------------
    # RESUMEN FINAL
    # --------------------------------------------------------

    print(
        "\n\n"
        + "=" * 100
    )

    print(
        "RESUMEN FINAL - CLARO PAY"
    )

    print(
        "=" * 100
    )

    print(
        f"\nArchivos procesados:"
        f" {len(archivos)}"
    )

    print(
        f"Archivos correctos:"
        f" {archivos_correctos}"
    )

    print(
        f"Archivos con errores:"
        f" {archivos_con_error}"
    )

    print(
        f"\nCampos correctos:"
        f" {total_correctos}"
    )

    print(
        f"Campos con error:"
        f" {total_errores}"
    )

    print(
        f"Total de campos evaluados:"
        f" {total_campos}"
    )

    print(
        f"\nPrecisión total:"
        f" {porcentaje:.2f}%"
    )

    # --------------------------------------------------------
    # ESTADO FINAL
    # --------------------------------------------------------

    print(
        "\n"
        + "-" * 100
    )

    if (
        total_errores == 0
        and len(archivos) > 0
    ):

        print(
            "TODOS LOS COMPROBANTES "
            "FUERON EXTRAÍDOS CORRECTAMENTE."
        )

    elif total_correctos > 0:

        print(
            "LA PRUEBA TERMINÓ CON "
            "ALGUNOS CAMPOS PENDIENTES."
        )

    else:

        print(
            "LA PRUEBA TERMINÓ CON ERRORES."
        )

    print(
        "-" * 100
    )

    print(
        "\n"
        + "=" * 100
    )

    print(
        "PRUEBA MASIVA TERMINADA"
    )

    print(
        "=" * 100
    )


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    main()