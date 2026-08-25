from pathlib import Path
import json

from Services.ocr import PaddleOCRServicio



# RUTAS


RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_BANAMEX = (
    RAIZ_PROYECTO
    / "Comprobantes"
    / "BANAMEX"
)

CARPETA_RESULTADOS = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "BANAMEX"
)



# CONVERTIR DETECCIÓN A DICCIONARIO


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



# PROCESAR BANAMEX


def procesar():

    print()
    print("=" * 70)
    print("PRUEBA PADDLEOCR - BANAMEX")
    print("=" * 70)

    print()
    print("Raíz del proyecto:")
    print(RAIZ_PROYECTO)

    print()
    print("Carpeta Banamex:")
    print(CARPETA_BANAMEX)

    print()

    if not CARPETA_BANAMEX.exists():

        print("ERROR:")
        print("No existe la carpeta de comprobantes Banamex.")

        return

    # Crear carpeta de resultados
    CARPETA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True
    )

    # Inicializar OCR
    print("Inicializando PaddleOCR...")

    ocr = PaddleOCRServicio(
        idioma="es"
    )

    print("PaddleOCR inicializado correctamente.")

    print()

    # Obtener imágenes
    archivos = sorted(
        archivo
        for archivo in CARPETA_BANAMEX.iterdir()
        if archivo.suffix.lower()
        in (
            ".png",
            ".jpg",
            ".jpeg",
            ".webp"
        )
    )

    print(
        f"Imágenes encontradas: {len(archivos)}"
    )

    print()

    
    # PROCESAR IMÁGENES
    

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

            resultado = ocr.procesar_imagen(
                str(archivo)
            )

            # ------------------------------------------------
            # CREAR JSON
            # ------------------------------------------------

            datos = {

                "archivo": archivo.name,

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

            nombre_json = (
                archivo.stem
                + ".json"
            )

            ruta_json = (
                CARPETA_RESULTADOS
                / nombre_json
            )

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
                len(resultado.detecciones)
            )

            print()

            print("LINEAS:")

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

    print("=" * 70)

    print("PROCESAMIENTO TERMINADO")

    print("=" * 70)





if __name__ == "__main__":

    procesar()