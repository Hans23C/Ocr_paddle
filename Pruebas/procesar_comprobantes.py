from pathlib import Path
import json
import sys

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from Services.ocr import PaddleOCRServicio


# ============================================================
# RUTAS
# ============================================================

CARPETA_COMPROBANTES = (
    RAIZ_PROYECTO
    / "Comprobantes"
)

CARPETA_RESULTADOS = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
)

MAPA_CARPETAS_ENTRADA = {
    "HEY_BANCO": Path("HEY, BANCO"),
    "HEY, BANCO": Path("HEY, BANCO"),
    "FINANCIERA_BIENESTAR": Path("BIENESTAR") / "PAGO_FINANCIERA_BIENESTAR",
    "TRANSFERENCIA_BIENESTAR": Path("BIENESTAR") / "TRANSFERECIA",
}

MAPA_CARPETAS_SALIDA = {
    "HEY, BANCO": "HEY_BANCO",
}


# ============================================================
# CONVERTIR DETECCIÓN A DICCIONARIO
# ============================================================

def convertir_deteccion(deteccion):

    return {

        "texto": deteccion.texto,

        "confianza": deteccion.confianza,

        "bbox": deteccion.bbox,

        "x": deteccion.x,

        "y": deteccion.y,

        "ancho": deteccion.ancho,

        "alto": deteccion.alto,

        "x_rel": deteccion.x_rel,

        "y_rel": deteccion.y_rel,

        "ancho_rel": deteccion.ancho_rel,

        "alto_rel": deteccion.alto_rel,

    }


# ============================================================
# PROCESAR BANCO
# ============================================================

def procesar_banco(nombre_banco, ocr=None):

    # --------------------------------------------------------
    # Normalizar nombre
    # --------------------------------------------------------

    nombre_banco = (
        nombre_banco
        .strip()
        .upper()
    )

    subruta_entrada = MAPA_CARPETAS_ENTRADA.get(
        nombre_banco,
        Path(nombre_banco)
    )

    nombre_salida = MAPA_CARPETAS_SALIDA.get(
        nombre_banco,
        nombre_banco
    )

    carpeta_banco = (
        CARPETA_COMPROBANTES
        / subruta_entrada
    )

    carpeta_resultados = (
        CARPETA_RESULTADOS
        / nombre_salida
    )

    # --------------------------------------------------------
    # ENCABEZADO
    # --------------------------------------------------------

    print()

    print("=" * 70)
    print(
        f"PRUEBA PADDLEOCR - {nombre_salida}"
    )
    print("=" * 70)

    print()

    print("Raíz del proyecto:")
    print(RAIZ_PROYECTO)

    print()

    print("Carpeta de comprobantes:")
    print(carpeta_banco)

    print()

    print("Carpeta de resultados:")
    print(carpeta_resultados)

    print()

    # --------------------------------------------------------
    # VALIDAR CARPETA
    # --------------------------------------------------------

    if not carpeta_banco.exists():

        print("ERROR:")

        print(
            "No existe la carpeta del banco."
        )

        print()

        print(
            "Debe existir:"
        )

        print(
            carpeta_banco
        )

        print()

        return

    # --------------------------------------------------------
    # CREAR RESULTADOS
    # --------------------------------------------------------

    carpeta_resultados.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # INICIALIZAR OCR
    # --------------------------------------------------------

    if ocr is None:
        print(
            "Inicializando PaddleOCR..."
        )

        try:

            ocr = PaddleOCRServicio(
                idioma="es"
            )

        except Exception as error:

            print()

            print(
                "ERROR INICIALIZANDO PADDLEOCR:"
            )

            print(
                type(error).__name__
            )

            print(
                error
            )

            return

        print(
            "PaddleOCR inicializado correctamente."
        )

        print()

    # --------------------------------------------------------
    # OBTENER IMÁGENES
    # --------------------------------------------------------

    extensiones = (
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".bmp"
    )

    archivos = sorted(
        archivo
        for archivo in carpeta_banco.iterdir()
        if (
            archivo.is_file()
            and
            archivo.suffix.lower()
            in extensiones
        )
    )

    print(
        f"Imágenes encontradas: {len(archivos)}"
    )

    print()

    if not archivos:

        print(
            "No se encontraron imágenes."
        )

        print()

        print(
            "Coloca los comprobantes en:"
        )

        print(
            carpeta_banco
        )

        return

    # --------------------------------------------------------
    # PROCESAR IMÁGENES
    # --------------------------------------------------------

    procesadas = 0
    errores = 0

    for numero, archivo in enumerate(
        archivos,
        start=1
    ):

        print("=" * 70)

        print(
            f"[{numero}/{len(archivos)}] "
            f"{archivo.name}"
        )

        print("=" * 70)

        try:

            # ------------------------------------------------
            # OCR
            # ------------------------------------------------
            #
            # Santander mantiene su procesamiento especial.
            #
            # Klar utiliza su nuevo procesamiento exclusivo.
            #
            # Farmacias del Ahorro utiliza su procesamiento exclusivo.
            #
            # Los demás bancos continúan exactamente
            # con el procesamiento normal.
            #
            # ------------------------------------------------

            if nombre_salida == "SANTANDER":

                resultado = (
                    ocr.procesar_imagen(
                        str(archivo),
                        reprocesar_santander=True
                    )
                )

            elif nombre_salida == "KLAR":

                resultado = (
                    ocr.procesar_imagen_klar(
                        str(archivo)
                    )
                )

            elif nombre_salida == "FARMACIAS_DE_AHORRO":

                resultado = (
                    ocr.procesar_imagen_farmacias(
                        str(archivo)
                    )
                )

            elif nombre_salida == "FINANCIERA_BIENESTAR":

                resultado = (
                    ocr.procesar_imagen_financiera_bienestar(
                        str(archivo)
                    )
                )

            elif nombre_salida == "TRANSFERENCIA_BIENESTAR":

                resultado = (
                    ocr.procesar_imagen_transferencia_bienestar(
                        str(archivo)
                    )
                )

            elif nombre_salida == "BANORTE":

                resultado = (
                    ocr.procesar_imagen_banorte(
                        str(archivo)
                    )
                )

            elif nombre_salida == "BBVA":

                resultado = (
                    ocr.procesar_imagen_bbva(
                        str(archivo)
                    )
                )

            elif nombre_salida == "ALBO":

                resultado = (
                    ocr.procesar_imagen_albo(
                        str(archivo)
                    )
                )

            elif nombre_salida == "HEY_BANCO":

                resultado = (
                    ocr.procesar_imagen_hey_banco(
                        str(archivo)
                    )
                )

            elif nombre_salida == "FONDEADORA":

                resultado = (
                    ocr.procesar_imagen_fondeadora(
                        str(archivo)
                    )
                )

            elif nombre_salida == "NU_MEXICO":

                resultado = (
                    ocr.procesar_imagen_nu_mexico(
                        str(archivo)
                    )
                )

            elif nombre_salida == "PAGO_OXXO":

                resultado = (
                    ocr.procesar_imagen_oxxo(
                        str(archivo)
                    )
                )

            else:

                resultado = (
                    ocr.procesar_imagen(
                        str(archivo)
                    )
                )

            # ------------------------------------------------
            # CREAR JSON
            # ------------------------------------------------

            datos = {

                "archivo": archivo.name,

                "banco": nombre_salida,

                "ancho_imagen":
                    resultado.ancho_imagen,

                "alto_imagen":
                    resultado.alto_imagen,

                "detecciones": [

                    convertir_deteccion(
                        deteccion
                    )

                    for deteccion
                    in resultado.detecciones

                ],

                "lineas":
                    resultado.lineas,

                "texto_completo":
                    resultado.texto_completo,

            }

            # ------------------------------------------------
            # NOMBRE JSON
            # ------------------------------------------------

            nombre_json = (
                archivo.stem
                + ".json"
            )

            ruta_json = (
                carpeta_resultados
                / nombre_json
            )

            # ------------------------------------------------
            # GUARDAR JSON
            # ------------------------------------------------

            with open(
                ruta_json,
                "w",
                encoding="utf-8"
            ) as archivo_json:

                json.dump(
                    datos,
                    archivo_json,
                    ensure_ascii=False,
                    indent=4
                )

            procesadas += 1

            # ------------------------------------------------
            # MOSTRAR RESULTADO
            # ------------------------------------------------

            print()

            print(
                "Tamaño imagen:"
            )

            print(
                f"{resultado.ancho_imagen} x "
                f"{resultado.alto_imagen}"
            )

            print()

            print(
                "Detecciones:",
                len(
                    resultado.detecciones
                )
            )

            print()

            print(
                "LINEAS:"
            )

            for indice, linea in enumerate(
                resultado.lineas,
                start=1
            ):

                print(
                    f"{indice:02d}. {linea}"
                )

            print()

            print(
                "JSON generado:"
            )

            print(
                ruta_json
            )

            print()

        except Exception as error:

            errores += 1

            print()

            print(
                "ERROR PROCESANDO:"
            )

            print(
                archivo.name
            )

            print()

            print(
                type(error).__name__
            )

            print(
                error
            )

            print()

    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------

    print("=" * 70)

    print(
        "PROCESAMIENTO TERMINADO"
    )

    print("=" * 70)

    print()

    print(
        f"Imágenes encontradas: {len(archivos)}"
    )

    print(
        f"Procesadas correctamente: {procesadas}"
    )

    print(
        f"Con errores: {errores}"
    )

    print()

    print(
        "Resultados guardados en:"
    )

    print(
        carpeta_resultados
    )

    print()


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    # --------------------------------------------------------
    # Verificar argumento
    # --------------------------------------------------------

    if len(sys.argv) < 2:

        print()

        print("=" * 70)

        print(
            "PROCESADOR GENERICO DE COMPROBANTES"
        )

        print("=" * 70)

        print()

        print(
            "Uso:"
        )

        print(
            "python -m Pruebas.procesar_comprobantes BANCO"
        )

        print()

        print(
            "Ejemplos:"
        )

        print(
            "python -m Pruebas.procesar_comprobantes BANAMEX"
        )

        print(
            "python -m Pruebas.procesar_comprobantes INBURSA"
        )

        print(
            "python -m Pruebas.procesar_comprobantes MERCADO_PAGO"
        )

        print(
            "python -m Pruebas.procesar_comprobantes HSBC"
        )

        print(
            "python -m Pruebas.procesar_comprobantes SANTANDER"
        )

        print(
            "python -m Pruebas.procesar_comprobantes KLAR"
        )

        print()

        return

    # --------------------------------------------------------
    # Obtener banco(s)
    # --------------------------------------------------------

    ocr_compartido = None
    for nombre_banco in sys.argv[1:]:
        if ocr_compartido is None:
            print("Inicializando PaddleOCR...")
            ocr_compartido = PaddleOCRServicio(idioma="es")
            print("PaddleOCR inicializado correctamente.\n")
        procesar_banco(
            nombre_banco,
            ocr=ocr_compartido
        )


# ============================================================
# EJECUCION
# ============================================================

if __name__ == "__main__":

    main()
