import json
from pathlib import Path

from Services.extractores.spin_by_oxxo.spin_by_oxxo import (
    SpinByOxxoExtractor
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CARPETA_JSON = (
    BASE_DIR
    / "Resultados_OCR"
    / "SPIN_BY_OXXO"
)


# ============================================================
# CARGAR JSON
# ============================================================

def cargar_json(ruta):

    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as archivo:

        return json.load(archivo)


# ============================================================
# OBTENER DETECCIONES
#
# IMPORTANTE:
#
# NO CAMBIAMOS "texto" A "text".
#
# El extractor SPIN BY OXXO trabaja con:
#
#     texto
#     confianza
#     x
#     y
#
# ============================================================

def obtener_detecciones(data):

    # --------------------------------------------------------
    # Si el JSON directamente es una lista
    # --------------------------------------------------------

    if isinstance(data, list):

        return data

    # --------------------------------------------------------
    # Si el JSON es un diccionario
    # --------------------------------------------------------

    if isinstance(data, dict):

        posibles_claves = [
            "detecciones",
            "ocr",
            "resultados",
            "results",
            "data"
        ]

        for clave in posibles_claves:

            valor = data.get(clave)

            if isinstance(valor, list):

                return valor

    return []


# ============================================================
# NORMALIZAR DETECCIONES
#
# IMPORTANTE:
#
# Conservamos las claves que utiliza el extractor:
#
#     texto
#     confianza
#     x
#     y
#
# ============================================================

def normalizar_deteccion(deteccion):

    if not isinstance(
        deteccion,
        dict
    ):

        return None

    # --------------------------------------------------------
    # TEXTO
    # --------------------------------------------------------

    texto = (
        deteccion.get("texto")
        or deteccion.get("text")
        or deteccion.get("value")
        or deteccion.get("transcription")
        or ""
    )

    # --------------------------------------------------------
    # CONFIANZA
    # --------------------------------------------------------

    confianza = (
        deteccion.get("confianza")
        if deteccion.get("confianza") is not None
        else deteccion.get("confidence")
        if deteccion.get("confidence") is not None
        else deteccion.get("conf")
        if deteccion.get("conf") is not None
        else deteccion.get("score")
        if deteccion.get("score") is not None
        else 0.0
    )

    # --------------------------------------------------------
    # X
    # --------------------------------------------------------

    x = deteccion.get(
        "x",
        0.0
    )

    # --------------------------------------------------------
    # Y
    # --------------------------------------------------------

    y = deteccion.get(
        "y",
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

    # --------------------------------------------------------
    # IMPORTANTE:
    #
    # La clave es "texto", NO "text".
    # --------------------------------------------------------

    return {
        "texto": str(texto).strip(),
        "confianza": confianza,
        "x": x,
        "y": y
    }


# ============================================================
# PREPARAR DATOS PARA EL EXTRACTOR
# ============================================================

def preparar_datos(data):

    detecciones_originales = obtener_detecciones(
        data
    )

    detecciones = []

    for deteccion in detecciones_originales:

        normalizada = normalizar_deteccion(
            deteccion
        )

        if normalizada is None:

            continue

        if not normalizada["texto"]:

            continue

        detecciones.append(
            normalizada
        )

    # --------------------------------------------------------
    # IMPORTANTE:
    #
    # El extractor acepta:
    #
    # {
    #     "detecciones": [...]
    # }
    #
    # --------------------------------------------------------

    return {
        "detecciones": detecciones
    }


# ============================================================
# OBTENER VALOR DE CAMPO
# ============================================================

def obtener_valor(campo):

    if isinstance(
        campo,
        dict
    ):

        if "valor" in campo:

            return campo["valor"]

        if "value" in campo:

            return campo["value"]

    return campo


# ============================================================
# OBTENER MÉTODO
# ============================================================

def obtener_metodo(campo):

    if not isinstance(
        campo,
        dict
    ):

        return ""

    return campo.get(
        "metodo",
        campo.get(
            "method",
            ""
        )
    )


# ============================================================
# OBTENER CONFIANZA
# ============================================================

def obtener_confianza(campo):

    if not isinstance(
        campo,
        dict
    ):

        return None

    return campo.get(
        "confianza",
        campo.get(
            "confidence"
        )
    )


# ============================================================
# MOSTRAR RESULTADO
# ============================================================

def mostrar_resultado(resultado):

    if not isinstance(
        resultado,
        dict
    ):

        print()
        print("RESULTADO INVALIDO:")
        print(resultado)

        return False

    # --------------------------------------------------------
    # DATOS GENERALES
    # --------------------------------------------------------

    banco = resultado.get(
        "banco",
        "SPIN BY OXXO"
    )

    tipo = resultado.get(
        "tipo",
        "TRANSFERENCIA_SPIN_BY_OXXO"
    )

    campos = resultado.get(
        "campos"
    )

    # --------------------------------------------------------
    # VALIDAR CAMPOS
    # --------------------------------------------------------

    if not isinstance(
        campos,
        dict
    ):

        print()
        print(
            "ESTADO: ERROR"
        )

        print(
            "El extractor no devolvió "
            "un diccionario de campos."
        )

        return False

    if not campos:

        print()
        print(
            "ESTADO: ERROR"
        )

        print(
            "El extractor no devolvió "
            "campos válidos."
        )

        return False

    # ========================================================
    # MOSTRAR RESULTADO
    # ========================================================

    print()
    print(
        "RESULTADO:"
    )

    print()
    print(
        f"  banco                     : "
        f"{banco}"
    )

    print(
        f"  tipo                      : "
        f"{tipo}"
    )

    print()

    for nombre_campo, datos in campos.items():

        valor = obtener_valor(
            datos
        )

        metodo = obtener_metodo(
            datos
        )

        confianza = obtener_confianza(
            datos
        )

        print(
            f"  {nombre_campo:25} : "
            f"{valor}"
        )

        if metodo:

            print(
                f"      método                : "
                f"{metodo}"
            )

        if confianza is not None:

            try:

                print(
                    f"      confianza             : "
                    f"{float(confianza):.4f}"
                )

            except (
                TypeError,
                ValueError
            ):

                print(
                    f"      confianza             : "
                    f"{confianza}"
                )

    return True


# ============================================================
# PRUEBA MASIVA
# ============================================================

def main():

    print()
    print("=" * 100)
    print(
        "PRUEBA MASIVA - SPIN BY OXXO"
    )
    print("=" * 100)

    print()
    print(
        "Carpeta de JSON:"
    )

    print(
        CARPETA_JSON
    )

    # ========================================================
    # VALIDAR CARPETA
    # ========================================================

    if not CARPETA_JSON.exists():

        print()
        print(
            "ERROR:"
        )

        print(
            "No existe la carpeta:"
        )

        print(
            CARPETA_JSON
        )

        return

    # ========================================================
    # BUSCAR JSON
    # ========================================================

    archivos = sorted(
        CARPETA_JSON.glob("*.json"),
        key=lambda archivo: archivo.name.lower()
    )

    print()
    print(
        f"Archivos JSON encontrados: "
        f"{len(archivos)}"
    )

    if not archivos:

        print()
        print(
            "No se encontraron archivos JSON."
        )

        return

    # ========================================================
    # CONTADORES
    # ========================================================

    exitosos = 0
    errores = 0

    # ========================================================
    # RECORRER COMPROBANTES
    # ========================================================

    for numero, archivo in enumerate(
        archivos,
        start=1
    ):

        print()
        print("=" * 100)

        print(
            f"[{numero}/{len(archivos)}] "
            f"{archivo.name}"
        )

        print("=" * 100)

        try:

            # =================================================
            # CARGAR JSON
            # =================================================

            data = cargar_json(
                archivo
            )

            # =================================================
            # PREPARAR DETECCIONES
            # =================================================

            datos = preparar_datos(
                data
            )

            detecciones = datos.get(
                "detecciones",
                []
            )

            print()
            print(
                f"Detecciones OCR: "
                f"{len(detecciones)}"
            )

            # =================================================
            # VALIDACIÓN
            # =================================================

            if not detecciones:

                print()
                print(
                    "ESTADO: ERROR"
                )

                print(
                    "No se encontraron "
                    "detecciones OCR válidas."
                )

                errores += 1

                continue

            # =================================================
            # CREAR EXTRACTOR
            #
            # IMPORTANTE:
            #
            # RESPETAMOS EXACTAMENTE EL CONSTRUCTOR
            # DEL EXTRACTOR ACTUAL.
            # =================================================

            extractor = SpinByOxxoExtractor(
                detecciones
            )

            # =================================================
            # EXTRAER
            #
            # IMPORTANTE:
            #
            # Tu función actual es:
            #
            #     extraer(self, datos)
            #
            # Por eso aquí SI se manda "datos".
            #
            # NO cambiar por:
            #
            #     extractor.extraer()
            #
            # =================================================

            resultado = extractor.extraer(
                datos
            )

            # =================================================
            # MOSTRAR
            # =================================================

            if mostrar_resultado(
                resultado
            ):

                exitosos += 1

            else:

                errores += 1

        except Exception as error:

            errores += 1

            print()
            print(
                "ERROR EJECUTANDO EXTRACTOR:"
            )

            print(
                type(error).__name__
            )

            print(
                str(error)
            )

    # ========================================================
    # RESUMEN FINAL
    # ========================================================

    print()
    print()

    print("=" * 100)
    print(
        "RESUMEN FINAL - SPIN BY OXXO"
    )
    print("=" * 100)

    print()

    print(
        f"Total de archivos : "
        f"{len(archivos)}"
    )

    print(
        f"Procesados OK     : "
        f"{exitosos}"
    )

    print(
        f"Con errores       : "
        f"{errores}"
    )

    if archivos:

        porcentaje = (
            exitosos
            / len(archivos)
        ) * 100

        print(
            f"Porcentaje OK     : "
            f"{porcentaje:.2f}%"
        )

    print()

    print("=" * 100)

    print(
        "FIN DE PRUEBA MASIVA"
    )

    print("=" * 100)


# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":

    main()