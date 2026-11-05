from pathlib import Path
import json
import sys
from datetime import datetime

from Services.extractores.azteca.azteca import (
    AztecaExtractor
)


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_JSON = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "AZTECA"
)

ARCHIVO_SALIDA = (
    CARPETA_JSON
    / "prueba_masiva_azteca.txt"
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

# True  = muestra todas las detecciones OCR en el TXT
# False = solamente muestra información general y resultado
MOSTRAR_DETECCIONES = True


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def escribir(archivo, texto=""):
    """
    Escribe una línea tanto en el archivo TXT como,
    opcionalmente, en consola.
    """
    archivo.write(texto + "\n")


def separador(archivo, caracter="=", cantidad=100):
    escribir(
        archivo,
        caracter * cantidad
    )


def valor_seguro(valor, default=""):
    """
    Convierte valores None a texto vacío para evitar
    problemas durante la generación del reporte.
    """
    if valor is None:
        return default

    return str(valor)


# ============================================================
# PROCESAR UN JSON
# ============================================================

def procesar_json(
    ruta_json,
    archivo_salida,
    extractor
):
    """
    Procesa un comprobante AZTECA individual y escribe
    todo su resultado en el TXT.

    Devuelve:
        True  -> extracción ejecutada correctamente
        False -> ocurrió un error
    """

    nombre_json = ruta_json.name

    separador(
        archivo_salida
    )

    escribir(
        archivo_salida,
        f"JSON: {nombre_json}"
    )

    separador(
        archivo_salida,
        "-"
    )

    # ========================================================
    # CARGAR JSON
    # ========================================================

    try:

        with open(
            ruta_json,
            "r",
            encoding="utf-8"
        ) as archivo:

            datos = json.load(archivo)

    except Exception as error:

        escribir(
            archivo_salida,
            "ERROR AL CARGAR JSON"
        )

        escribir(
            archivo_salida,
            f"Tipo: {type(error).__name__}"
        )

        escribir(
            archivo_salida,
            f"Mensaje: {error}"
        )

        return False

    # ========================================================
    # INFORMACIÓN GENERAL
    # ========================================================

    escribir(
        archivo_salida
    )

    escribir(
        archivo_salida,
        "INFORMACIÓN DEL COMPROBANTE"
    )

    separador(
        archivo_salida,
        "-"
    )

    escribir(
        archivo_salida,
        f"Archivo: "
        f"{valor_seguro(datos.get('archivo'))}"
    )

    escribir(
        archivo_salida,
        f"Banco: "
        f"{valor_seguro(datos.get('banco'))}"
    )

    escribir(
        archivo_salida,
        f"Ancho: "
        f"{valor_seguro(datos.get('ancho_imagen'))}"
    )

    escribir(
        archivo_salida,
        f"Alto: "
        f"{valor_seguro(datos.get('alto_imagen'))}"
    )

    # ========================================================
    # DETECCIONES
    # ========================================================

    detecciones = datos.get(
        "detecciones",
        []
    )

    escribir(
        archivo_salida
    )

    escribir(
        archivo_salida,
        f"Detecciones OCR: {len(detecciones)}"
    )

    # ========================================================
    # MOSTRAR DETECCIONES
    # ========================================================

    if MOSTRAR_DETECCIONES:

        escribir(
            archivo_salida
        )

        escribir(
            archivo_salida,
            "DETECCIONES OCR"
        )

        separador(
            archivo_salida,
            "-"
        )

        for i, deteccion in enumerate(
            detecciones
        ):

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

            ancho = deteccion.get(
                "ancho",
                0
            )

            alto = deteccion.get(
                "alto",
                0
            )

            try:
                x = float(x)
            except Exception:
                x = 0.0

            try:
                y = float(y)
            except Exception:
                y = 0.0

            try:
                ancho = float(ancho)
            except Exception:
                ancho = 0.0

            try:
                alto = float(alto)
            except Exception:
                alto = 0.0

            try:
                confianza = float(confianza)
            except Exception:
                confianza = 0.0

            escribir(
                archivo_salida,
                f"{i:03d} | "
                f"x={x:.2f} "
                f"y={y:.2f} "
                f"ancho={ancho:.2f} "
                f"alto={alto:.2f} "
                f"conf={confianza:.4f} | "
                f"{texto}"
            )

    # ========================================================
    # EJECUTAR EXTRACTOR AZTECA
    # ========================================================

    escribir(
        archivo_salida
    )

    escribir(
        archivo_salida,
        "RESULTADO DEL EXTRACTOR AZTECA"
    )

    separador(
        archivo_salida,
        "-"
    )

    try:

        resultado = extractor.extraer(
            datos
        )

    except Exception as error:

        escribir(
            archivo_salida,
            "ERROR EJECUTANDO EXTRACTOR"
        )

        escribir(
            archivo_salida,
            f"Tipo: {type(error).__name__}"
        )

        escribir(
            archivo_salida,
            f"Mensaje: {error}"
        )

        return False

    # ========================================================
    # BANCO
    # ========================================================

    escribir(
        archivo_salida,
        f"Banco: "
        f"{valor_seguro(resultado.get('banco'))}"
    )

    # ========================================================
    # CAMPOS
    # ========================================================

    campos = resultado.get(
        "campos",
        {}
    )

    escribir(
        archivo_salida
    )

    escribir(
        archivo_salida,
        "Campos:"
    )

    for nombre, valor in campos.items():

        escribir(
            archivo_salida
        )

        escribir(
            archivo_salida,
            nombre
        )

        escribir(
            archivo_salida,
            "-" * 70
        )

        escribir(
            archivo_salida,
            f"Valor: {valor_seguro(valor)}"
        )

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 100)
    print("PRUEBA MASIVA - AZTECA")
    print("=" * 100)

    # ========================================================
    # VALIDAR CARPETA
    # ========================================================

    print()
    print("Carpeta de JSON:")
    print(CARPETA_JSON)

    if not CARPETA_JSON.exists():

        print()
        print(
            "ERROR: No existe la carpeta de resultados OCR."
        )

        print()
        print(
            f"Ruta esperada: {CARPETA_JSON}"
        )

        sys.exit(1)

    # ========================================================
    # BUSCAR JSON
    # ========================================================

    archivos_json = sorted(
        CARPETA_JSON.glob("*.json"),
        key=lambda archivo: archivo.name.lower()
    )

    if not archivos_json:

        print()
        print(
            "ERROR: No se encontraron archivos JSON."
        )

        sys.exit(1)

    # ========================================================
    # MOSTRAR INFORMACIÓN
    # ========================================================

    print()
    print(
        f"JSON encontrados: {len(archivos_json)}"
    )

    print()
    print(
        "Archivo de salida:"
    )

    print(
        ARCHIVO_SALIDA
    )

    # ========================================================
    # CREAR EXTRACTOR UNA SOLA VEZ
    # ========================================================

    print()
    print(
        "Inicializando AztecaExtractor..."
    )

    try:

        extractor = AztecaExtractor()

    except Exception as error:

        print()
        print(
            "ERROR inicializando AztecaExtractor:"
        )

        print(
            type(error).__name__,
            error
        )

        sys.exit(1)

    print(
        "AztecaExtractor inicializado correctamente."
    )

    # ========================================================
    # CONTADORES
    # ========================================================

    total = len(
        archivos_json
    )

    procesados_correctamente = 0
    errores_json = 0
    errores_extractor = 0

    inicio = datetime.now()

    # ========================================================
    # ABRIR TXT
    # ========================================================

    try:

        with open(
            ARCHIVO_SALIDA,
            "w",
            encoding="utf-8"
        ) as archivo_salida:

            # ====================================================
            # ENCABEZADO
            # ====================================================

            separador(
                archivo_salida
            )

            escribir(
                archivo_salida,
                "PRUEBA MASIVA - AZTECA"
            )

            separador(
                archivo_salida
            )

            escribir(
                archivo_salida,
                f"Fecha de ejecución: "
                f"{inicio.strftime('%d/%m/%Y %H:%M:%S')}"
            )

            escribir(
                archivo_salida,
                f"Total de JSON: {total}"
            )

            escribir(
                archivo_salida,
                f"Carpeta: {CARPETA_JSON}"
            )

            escribir(
                archivo_salida
            )

            escribir(
                archivo_salida,
                "Este archivo contiene el resultado"
            )

            escribir(
                archivo_salida,
                "completo de cada comprobante AZTECA."
            )

            # ====================================================
            # PROCESAR TODOS
            # ====================================================

            for posicion, ruta_json in enumerate(
                archivos_json,
                start=1
            ):

                print(
                    f"[{posicion}/{total}] "
                    f"{ruta_json.name}",
                    end=" "
                )

                # ------------------------------------------------
                # Procesar JSON
                # ------------------------------------------------

                try:

                    resultado_ok = procesar_json(
                        ruta_json,
                        archivo_salida,
                        extractor
                    )

                    if resultado_ok:

                        procesados_correctamente += 1

                        print(
                            "OK"
                        )

                    else:

                        # Determinar si el problema fue JSON
                        # o extractor revisando el archivo.
                        try:

                            with open(
                                ruta_json,
                                "r",
                                encoding="utf-8"
                            ) as archivo:

                                json.load(archivo)

                            errores_extractor += 1

                        except Exception:

                            errores_json += 1

                        print(
                            "ERROR"
                        )

                except Exception as error:

                    errores_extractor += 1

                    escribir(
                        archivo_salida
                    )

                    escribir(
                        archivo_salida,
                        "ERROR NO CONTROLADO"
                    )

                    escribir(
                        archivo_salida,
                        f"Tipo: {type(error).__name__}"
                    )

                    escribir(
                        archivo_salida,
                        f"Mensaje: {error}"
                    )

                    print(
                        "ERROR"
                    )

            # ====================================================
            # TIEMPO FINAL
            # ====================================================

            fin = datetime.now()

            duracion = fin - inicio

            # ====================================================
            # RESUMEN
            # ====================================================

            separador(
                archivo_salida
            )

            escribir(
                archivo_salida,
                "RESUMEN DE LA PRUEBA"
            )

            separador(
                archivo_salida
            )

            escribir(
                archivo_salida,
                f"Total JSON: "
                f"{total}"
            )

            escribir(
                archivo_salida,
                f"Procesados correctamente: "
                f"{procesados_correctamente}"
            )

            escribir(
                archivo_salida,
                f"Errores de JSON: "
                f"{errores_json}"
            )

            escribir(
                archivo_salida,
                f"Errores del extractor: "
                f"{errores_extractor}"
            )

            escribir(
                archivo_salida
            )

            escribir(
                archivo_salida,
                f"Inicio: "
                f"{inicio.strftime('%d/%m/%Y %H:%M:%S')}"
            )

            escribir(
                archivo_salida,
                f"Fin: "
                f"{fin.strftime('%d/%m/%Y %H:%M:%S')}"
            )

            escribir(
                archivo_salida,
                f"Duración: "
                f"{duracion}"
            )

            separador(
                archivo_salida
            )

            escribir(
                archivo_salida,
                "FIN DE PRUEBA MASIVA"
            )

            separador(
                archivo_salida
            )

    except Exception as error:

        print()
        print(
            "ERROR creando/escribiendo el TXT:"
        )

        print(
            type(error).__name__,
            error
        )

        sys.exit(1)

    # ========================================================
    # RESULTADO EN CONSOLA
    # ========================================================

    print()
    print("=" * 100)
    print("PRUEBA MASIVA TERMINADA")
    print("=" * 100)

    print()
    print(
        f"Total JSON: {total}"
    )

    print(
        f"Procesados correctamente: "
        f"{procesados_correctamente}"
    )

    print(
        f"Errores de JSON: "
        f"{errores_json}"
    )

    print(
        f"Errores del extractor: "
        f"{errores_extractor}"
    )

    print()
    print(
        "Resultado guardado en:"
    )

    print(
        ARCHIVO_SALIDA
    )

    print()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    main()