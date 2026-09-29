"""
PRUEBA MASIVA - FARMACIAS DEL AHORRO

Objetivo:
- Procesar todos los comprobantes de FARMACIAS_DE_AHORRO.
- Utilizar la imagen original.
- No modificar tamaño.
- No realizar recorte.
- Usar procesar_imagen_farmacias().
- Mostrar únicamente un resumen controlado por imagen.
- Guardar toda la salida de la prueba en un archivo TXT.

IMPORTANTE:
Este script no modifica paddle_ocr.py ni las configuraciones de otros bancos.
"""

import json
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

from Services.ocr.paddle_ocr import PaddleOCRServicio
from Services.extractores.farmacias_de_ahorro import crear_extractor


# ============================================================
# CONFIGURACION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CARPETA_IMAGENES = (
    BASE_DIR
    / "Comprobantes"
    / "FARMACIAS_DE_AHORRO"
)

CARPETA_RESULTADOS = (
    BASE_DIR
    / "Resultados_OCR"
    / "FARMACIAS_DE_AHORRO"
)

ARCHIVO_LOG = (
    BASE_DIR
    / "Pruebas"
    / "resultado_prueba_masiva_farmacias.txt"
)


# ============================================================
# FORMATO
# ============================================================

ANCHO = 100


def linea():
    return "=" * ANCHO


def separador():
    return "-" * ANCHO


def valor_campo(resultado, campo):
    try:
        return resultado["campos"][campo]["valor"]
    except (KeyError, TypeError):
        return None


def formatear_valor(valor):
    if valor is None:
        return "NO ENCONTRADO"
    return str(valor)


def cargar_resultado_json(ruta_json):
    try:
        with open(
            ruta_json,
            "r",
            encoding="utf-8"
        ) as archivo:
            return json.load(archivo)
    except Exception:
        return None


def _serializar_ocr(obj):
    """Convierte recursivamente objetos OCR a estructuras JSON."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _serializar_ocr(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serializar_ocr(v) for v in obj]
    if hasattr(obj, "__dict__"):
        return {str(k): _serializar_ocr(v) for k, v in vars(obj).items()}
    return str(obj)


def resultado_ocr_a_dict(resultado_ocr):
    """Convierte ResultadoOCR y sus OCRDeteccion a un dict JSON-serializable."""
    return {
        "dimensiones": {
            "ancho": resultado_ocr.ancho_imagen,
            "alto": resultado_ocr.alto_imagen,
        },
        "detecciones": _serializar_ocr(resultado_ocr.detecciones),
        "lineas": _serializar_ocr(resultado_ocr.lineas),
        "texto_completo": resultado_ocr.texto_completo,
    }


def guardar_json(ruta_json, resultado_ocr):
    ruta_json.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        ruta_json,
        "w",
        encoding="utf-8"
    ) as archivo:
        json.dump(
            resultado_ocr,
            archivo,
            ensure_ascii=False,
            indent=2
        )


def imprimir_resultado_comprobante(
    indice,
    total,
    ruta_imagen,
    tiempo_ocr,
    ruta_json,
    resultado,
):
    print()
    print(f"OCR terminado en {tiempo_ocr:.3f} s")
    print()

    # --------------------------------------------------------
    # Dimensiones y detecciones
    # --------------------------------------------------------

    dimensiones = resultado.get(
        "dimensiones",
        {}
    )

    ancho = dimensiones.get(
        "ancho",
        "N/D"
    )

    alto = dimensiones.get(
        "alto",
        "N/D"
    )

    detecciones = resultado.get(
        "detecciones",
        []
    )

    print(
        f"Dimensiones detectadas: "
        f"{ancho} x {alto}"
    )

    print(
        f"Detecciones: {len(detecciones)}"
    )

    print(
        f"JSON generado: "
        f"{ruta_json}"
    )

    print()
    print(separador())

    nombre = ruta_imagen.stem

    print(nombre)

    print(
        "Tipo Comprobante   "
        f"{formatear_valor(resultado.get('tipo'))}"
    )

    print(
        "Fecha              "
        f"{formatear_valor(valor_campo(resultado, 'fecha'))}"
    )

    print(
        "Monto              "
        f"{formatear_valor(valor_campo(resultado, 'monto'))}"
    )

    print(
        "Transaccion        "
        f"{formatear_valor(valor_campo(resultado, 'transaccion'))}"
    )

    print(
        "Autorizacion       "
        f"{formatear_valor(valor_campo(resultado, 'autorizacion'))}"
    )

    print(
        "Referencia         "
        f"{formatear_valor(valor_campo(resultado, 'referencia'))}"
    )

    print(
        "Deposito           "
        f"{formatear_valor(valor_campo(resultado, 'deposito'))}"
    )

    # --------------------------------------------------------
    # En esta prueba NO se utilizan valores esperados para
    # corregir OCR.
    #
    # Solamente se reportan campos no encontrados.
    # --------------------------------------------------------

    campos = [
        "fecha",
        "monto",
        "transaccion",
        "autorizacion",
        "referencia",
        "deposito",
    ]

    campos_no_encontrados = []

    for campo in campos:
        if valor_campo(resultado, campo) is None:
            campos_no_encontrados.append(campo)

    tipo = resultado.get("tipo")

    if tipo is None:
        campos_no_encontrados.append("tipo")

    total_campos = 7
    correctos = total_campos - len(
        campos_no_encontrados
    )

    print()

    if campos_no_encontrados:
        print("CAMPOS QUE REQUIEREN REVISION:")

        for campo in campos_no_encontrados:
            print(f"  - {campo}")

    else:
        print("CAMPOS QUE REQUIEREN REVISION:")
        print("  - ninguno")

    print()
    print(
        f"CAMPOS: {correctos}/{total_campos} "
        "con valor encontrado"
    )


def ejecutar_prueba():
    inicio_total = time.perf_counter()

    ARCHIVO_LOG.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    CARPETA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True
    )

    imagenes = sorted(
      [
        ruta
        for ruta in CARPETA_IMAGENES.iterdir()
        if ruta.is_file()
        and ruta.suffix.lower() in {".jpg", ".jpeg", ".png"}
      ],
      key=lambda ruta: ruta.name.lower()
    )

    if not imagenes:
        print(
            "ERROR: No se encontraron imágenes en:"
        )
        print(CARPETA_IMAGENES)
        return

    total = len(imagenes)

    # --------------------------------------------------------
    # El TXT recibe exactamente la misma salida de consola.
    # --------------------------------------------------------

    class SalidaDuplicada:
        def __init__(self, *salidas):
            self.salidas = salidas

        def write(self, texto):
            for salida in self.salidas:
                salida.write(texto)
                salida.flush()

        def flush(self):
            for salida in self.salidas:
                salida.flush()

    with open(
        ARCHIVO_LOG,
        "w",
        encoding="utf-8"
    ) as archivo_log:

        salida = SalidaDuplicada(
            sys.stdout,
            archivo_log
        )

        with redirect_stdout(salida):

            print(linea())
            print(
                "PRUEBA MASIVA - FARMACIAS DEL AHORRO"
            )
            print(linea())
            print()
            print(
                f"Comprobantes encontrados: {total}"
            )
            print(
                f"Carpeta: {CARPETA_IMAGENES}"
            )
            print()
            print(
                "IMPORTANTE:"
            )
            print(
                "- Se utilizarán las imágenes originales."
            )
            print(
                "- No se modifica su tamaño."
            )
            print(
                "- No se realiza redimensionamiento."
            )
            print(
                "- No se realiza recorte."
            )
            print(
                "- No se utilizan valores esperados "
                "para corregir OCR."
            )
            print(
                "- Se utiliza exclusivamente "
                "procesar_imagen_farmacias()."
            )
            print()

            # ------------------------------------------------
            # Inicializar OCR UNA SOLA VEZ.
            # ------------------------------------------------

            print(
                "Inicializando OCR de Farmacias..."
            )

            ocr = PaddleOCRServicio(
                idioma="es"
            )

            extractor = crear_extractor()

            print(
                "OCR inicializado."
            )
            print()

            procesados = 0
            errores = 0
            total_campos_encontrados = 0
            total_campos = total * 7

            inicio_procesamiento = time.perf_counter()

            for indice, ruta_imagen in enumerate(
                imagenes,
                start=1
            ):

                inicio_imagen = time.perf_counter()

                try:
                    print()
                    print(linea())
                    print(f"[{indice}/{total}] {ruta_imagen.name}")
                    print(linea())
                    print()
                    print(f"Imagen: {ruta_imagen}")
                    print("IMPORTANTE:")
                    print("Se utilizará la imagen original.")
                    print("No se modifica su tamaño.")
                    print("No se realiza redimensionamiento.")
                    print("No se realiza recorte.")
                    print()
                    print("Ejecutando OCR...")

                    inicio_ocr = time.perf_counter()

                    # IMPORTANTE:
                    # Esta es la única llamada OCR utilizada.
                    resultado_ocr = (
                        ocr.procesar_imagen_farmacias(
                            str(ruta_imagen)
                        )
                    )

                    tiempo_ocr = (
                        time.perf_counter()
                        - inicio_ocr
                    )

                    print()
                    print(
                        f"OCR terminado en "
                        f"{tiempo_ocr:.3f} s"
                    )
                    print()

                    # ------------------------------------------------
                    # ADAPTAR RESULTADO OCR
                    # ------------------------------------------------
                    # procesar_imagen_farmacias() devuelve un objeto
                    # ResultadoOCR. El extractor de Farmacias trabaja
                    # con la estructura tipo diccionario de las
                    # detecciones.
                    #
                    # Si en algún momento el OCR devuelve directamente
                    # un diccionario, se conserva ese comportamiento.
                    # ------------------------------------------------
                    if isinstance(resultado_ocr, dict):
                        datos_ocr = resultado_ocr
                    else:
                        datos_ocr = resultado_ocr_a_dict(
                            resultado_ocr
                        )

                    # ------------------------------------------------
                    # El resultado generado por
                    # procesar_imagen_farmacias ya contiene las
                    # detecciones. Se adapta únicamente para guardarlo
                    # como JSON y pasarlo al extractor.
                    # ------------------------------------------------

                    ruta_json = (
                        CARPETA_RESULTADOS
                        / f"{ruta_imagen.stem}.json"
                    )

                    guardar_json(
                        ruta_json,
                        datos_ocr
                    )

                    # ------------------------------------------------
                    # Extractor Farmacias
                    # ------------------------------------------------

                    resultado = extractor.extraer(
                        datos_ocr
                    )

                    imprimir_resultado_comprobante(
                        indice,
                        total,
                        ruta_imagen,
                        tiempo_ocr,
                        ruta_json,
                        resultado,
                    )

                    campos = [
                        "fecha",
                        "monto",
                        "transaccion",
                        "autorizacion",
                        "referencia",
                        "deposito",
                    ]

                    encontrados = sum(
                        1
                        for campo in campos
                        if valor_campo(
                            resultado,
                            campo
                        ) is not None
                    )

                    if resultado.get("tipo") is not None:
                        encontrados += 1

                    total_campos_encontrados += (
                        encontrados
                    )

                    tiempo_imagen = (
                        time.perf_counter()
                        - inicio_imagen
                    )

                    print()
                    print(
                        f"Tiempo imagen: "
                        f"{tiempo_imagen:.3f} s"
                    )

                    procesados += 1

                except Exception as error:
                    errores += 1

                    tiempo_imagen = (
                        time.perf_counter()
                        - inicio_imagen
                    )

                    print()
                    print(
                        "ERROR AL PROCESAR "
                        f"{ruta_imagen.name}"
                    )
                    print(
                        f"Detalle: {error}"
                    )
                    print(
                        f"Tiempo imagen: "
                        f"{tiempo_imagen:.3f} s"
                    )

            tiempo_procesamiento = (
                time.perf_counter()
                - inicio_procesamiento
            )

            tiempo_total = (
                time.perf_counter()
                - inicio_total
            )

            print()
            print()
            print(linea())
            print(
                "RESUMEN PRUEBA MASIVA"
            )
            print(linea())
            print()
            print(
                f"Comprobantes encontrados: "
                f"{total}"
            )
            print(
                f"Comprobantes procesados: "
                f"{procesados}"
            )
            print(
                f"Comprobantes con error: "
                f"{errores}"
            )
            print(
                f"Campos encontrados: "
                f"{total_campos_encontrados}/"
                f"{total_campos}"
            )
            print(
                f"Tiempo total procesamiento: "
                f"{tiempo_procesamiento:.3f} s"
            )
            print(
                f"Tiempo total prueba: "
                f"{tiempo_total:.3f} s"
            )
            print()
            print(
                f"TXT generado:"
            )
            print(
                f"{ARCHIVO_LOG}"
            )
            print()
            print(linea())


if __name__ == "__main__":
    ejecutar_prueba()
