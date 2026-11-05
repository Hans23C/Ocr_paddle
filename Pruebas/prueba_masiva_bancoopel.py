"""
PRUEBA MASIVA OCR - BANCOPPEL

Evalúa cuatro variantes de imagen utilizando el híbrido actualizado:
- original
- escalada_2x
- contraste_clahe
- umbral_adaptativo

Genera reportes TXT y JSON con los resultados obtenidos.
No modifica el extractor ni las imágenes originales.
"""

from pathlib import Path
import importlib.util
import json
import re
import sys
import time
import traceback

import cv2

from Services.ocr.paddle_ocr import PaddleOCRServicio


# ============================================================
# CONFIGURACIÓN
# ============================================================

VARIANTES = (
    "original",
    "escalada_2x",
    "contraste_clahe",
    "umbral_adaptativo",
)

CAMPOS = (
    "banco_emisor",
    "fecha",
    "beneficiario",
    "concepto",
    "monto",
    "referencia",
    "clave_rastreo",
    "clabe_receptor",
)


# ============================================================
# LOCALIZAR LA RAÍZ DEL PROYECTO
# ============================================================

def encontrar_raiz():
    actual = Path(__file__).resolve()

    for ruta in actual.parents:
        if (
            (ruta / "Comprobantes").is_dir()
            and (ruta / "Services").is_dir()
        ):
            return ruta

    return actual.parent.parent


# ============================================================
# CARGAR EL HÍBRIDO ACTUALIZADO
# ============================================================

def cargar_hibrido(ruta):
    spec = importlib.util.spec_from_file_location(
        "bancoppel_hibrido_actualizado",
        str(ruta),
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"No se pudo cargar el híbrido: {ruta}"
        )

    modulo = importlib.util.module_from_spec(spec)

    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)

    if not hasattr(modulo, "extraer"):
        raise AttributeError(
            "El híbrido no contiene la función extraer(datos)."
        )

    return modulo


# ============================================================
# GENERAR LAS CUATRO VARIANTES DE CADA COMPROBANTE
# ============================================================

def crear_variantes(ruta_imagen, carpeta_salida):
    imagen = cv2.imread(
        str(ruta_imagen),
        cv2.IMREAD_COLOR,
    )

    if imagen is None:
        raise ValueError(
            f"No se pudo leer la imagen: {ruta_imagen}"
        )

    gris = cv2.cvtColor(
        imagen,
        cv2.COLOR_BGR2GRAY,
    )

    alto, ancho = gris.shape[:2]

    # Variante 1: imagen original.
    original = imagen

    # Variante 2: ampliación al doble.
    escalada = cv2.resize(
        imagen,
        (ancho * 2, alto * 2),
        interpolation=cv2.INTER_CUBIC,
    )

    # Variante 3: mejora de contraste mediante CLAHE.
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    contraste_gris = clahe.apply(gris)

    contraste = cv2.cvtColor(
        contraste_gris,
        cv2.COLOR_GRAY2BGR,
    )

    # Variante 4: umbralización adaptativa.
    umbral_gris = cv2.adaptiveThreshold(
        gris,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )

    umbral = cv2.cvtColor(
        umbral_gris,
        cv2.COLOR_GRAY2BGR,
    )

    matrices = {
        "original": original,
        "escalada_2x": escalada,
        "contraste_clahe": contraste,
        "umbral_adaptativo": umbral,
    }

    carpeta_salida.mkdir(
        parents=True,
        exist_ok=True,
    )

    rutas = {}

    for nombre, matriz in matrices.items():
        destino = carpeta_salida / (
            f"{ruta_imagen.stem}_{nombre}.png"
        )

        if not cv2.imwrite(str(destino), matriz):
            raise IOError(
                f"No se pudo guardar la variante: {destino}"
            )

        rutas[nombre] = destino

    return rutas


# ============================================================
# CONVERTIR LAS DETECCIONES OCR A JSON
# ============================================================

def resultado_a_json(resultado, nombre_imagen, variante):
    detecciones = []

    for deteccion in (
        getattr(resultado, "detecciones", []) or []
    ):
        detecciones.append({
            "texto": str(
                getattr(deteccion, "texto", "") or ""
            ),
            "confianza": float(
                getattr(deteccion, "confianza", 0.0) or 0.0
            ),
            "x": float(
                getattr(deteccion, "x", 0.0) or 0.0
            ),
            "y": float(
                getattr(deteccion, "y", 0.0) or 0.0
            ),
            "ancho": float(
                getattr(deteccion, "ancho", 0.0) or 0.0
            ),
            "alto": float(
                getattr(deteccion, "alto", 0.0) or 0.0
            ),
        })

    return {
        "archivo": nombre_imagen,
        "banco": "BANCOPPEL",
        "variante": variante,
        "ancho_imagen": int(
            getattr(resultado, "ancho_imagen", 0) or 0
        ),
        "alto_imagen": int(
            getattr(resultado, "alto_imagen", 0) or 0
        ),
        "texto_completo": str(
            getattr(resultado, "texto_completo", "") or ""
        ),
        "detecciones": detecciones,
    }


# ============================================================
# NORMALIZAR Y EXTRAER LOS CAMPOS
# ============================================================

def limpiar(valor):
    return re.sub(
        r"\s+",
        " ",
        str(valor or ""),
    ).strip()


def obtener_campos(resultado):
    campos = (
        resultado.get("campos", {})
        if isinstance(resultado, dict)
        else {}
    )

    valores = {}

    for campo in CAMPOS:
        informacion = campos.get(campo, {})

        if isinstance(informacion, dict):
            valor = informacion.get("valor", "")
        else:
            valor = informacion

        valores[campo] = limpiar(valor)

    return valores


# ============================================================
# PROCESAR COMPROBANTES
# ============================================================

def main():
    raiz = encontrar_raiz()

    carpeta_comprobantes = (
        raiz / "Comprobantes" / "BANCOPPEL"
    )

    carpeta_salida = (
        raiz
        / "Resultados_OCR"
        / "BANCOPPEL"
        / "Prueba_Masiva"
    )

    ruta_hibrido = (
        raiz
        / "Pruebas"
        / "probar_hibrido_bancoopel.py"
    )

    # --------------------------------------------------------
    # VALIDACIONES
    # --------------------------------------------------------

    if not ruta_hibrido.is_file():
        raise SystemExit(
            f"No se encontró el híbrido actualizado:\n"
            f"{ruta_hibrido}"
        )

    if not carpeta_comprobantes.is_dir():
        raise SystemExit(
            f"No se encontró la carpeta de comprobantes:\n"
            f"{carpeta_comprobantes}"
        )

    modulo_hibrido = cargar_hibrido(ruta_hibrido)

    extensiones = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
        ".webp",
    }

    imagenes = sorted(
        [
            archivo
            for archivo in carpeta_comprobantes.iterdir()
            if archivo.is_file()
            and archivo.suffix.lower() in extensiones
        ],
        key=lambda archivo: (
            int(re.search(
                r"(\d+)",
                archivo.stem,
            ).group(1))
            if re.search(r"(\d+)", archivo.stem)
            else 10**12,
            archivo.name.lower(),
        ),
    )

    if not imagenes:
        raise SystemExit(
            "No se encontraron imágenes en "
            f"{carpeta_comprobantes}"
        )

    carpeta_salida.mkdir(
        parents=True,
        exist_ok=True,
    )

    carpeta_variantes = carpeta_salida / "variantes"
    carpeta_json = carpeta_salida / "ocr_json"

    carpeta_variantes.mkdir(exist_ok=True)
    carpeta_json.mkdir(exist_ok=True)

    print("=" * 75)
    print("PRUEBA MASIVA OCR - BANCOPPEL")
    print("=" * 75)
    print(f"Comprobantes encontrados: {len(imagenes)}")
    print(f"Híbrido: {ruta_hibrido}")
    print(f"Resultados: {carpeta_salida}")
    print("Variantes:", ", ".join(VARIANTES))
    print("=" * 75)

    print("\nInicializando PaddleOCR...")

    servicio = PaddleOCRServicio(idioma="es")

    registros = []
    errores = []
    inicio_total = time.time()

    # --------------------------------------------------------
    # PROCESAMIENTO MASIVO
    # --------------------------------------------------------

    for indice, imagen in enumerate(imagenes, start=1):
        print(
            f"\n[{indice}/{len(imagenes)}] "
            f"{imagen.name}"
        )

        registro = {
            "imagen": imagen.name,
            "variantes": {},
            "error": "",
        }

        try:
            rutas = crear_variantes(
                imagen,
                carpeta_variantes / imagen.stem,
            )

            for variante in VARIANTES:
                print(f"  Procesando: {variante}")

                inicio_ocr = time.time()

                resultado_ocr = servicio.procesar_imagen(
                    str(rutas[variante])
                )

                tiempo_ocr = round(
                    time.time() - inicio_ocr,
                    3,
                )

                datos = resultado_a_json(
                    resultado_ocr,
                    imagen.name,
                    variante,
                )

                # El híbrido recibe los datos OCR de esta variante.
                resultado_extraccion = (
                    modulo_hibrido.extraer(datos)
                )

                valores = obtener_campos(
                    resultado_extraccion
                )

                registro["variantes"][variante] = {
                    "segundos_ocr": tiempo_ocr,
                    "detecciones": len(
                        datos["detecciones"]
                    ),
                    "campos": valores,
                    "texto_completo": datos[
                        "texto_completo"
                    ],
                }

                ruta_json = (
                    carpeta_json
                    / f"{imagen.stem}_{variante}.json"
                )

                with ruta_json.open(
                    "w",
                    encoding="utf-8",
                ) as archivo:
                    json.dump(
                        {
                            "ocr": datos,
                            "extraccion": resultado_extraccion,
                        },
                        archivo,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    )

                print(
                    f"    Tiempo OCR: {tiempo_ocr}s | "
                    f"Detecciones: {len(datos['detecciones'])}"
                )

                for campo, valor in valores.items():
                    print(f"    {campo}: {valor}")

        except Exception as exc:
            mensaje_error = (
                f"{type(exc).__name__}: {exc}"
            )

            registro["error"] = mensaje_error

            errores.append({
                "imagen": imagen.name,
                "error": mensaje_error,
            })

            print(f"  ERROR: {mensaje_error}")
            traceback.print_exc()

        registros.append(registro)

    # --------------------------------------------------------
    # GENERAR REPORTE TXT
    # --------------------------------------------------------

    tiempo_total = round(
        time.time() - inicio_total,
        2,
    )

    ruta_reporte_txt = (
        carpeta_salida / "reporte_prueba_masiva.txt"
    )

    ruta_reporte_json = (
        carpeta_salida / "reporte_prueba_masiva.json"
    )

    with ruta_reporte_txt.open(
        "w",
        encoding="utf-8",
    ) as archivo:

        archivo.write("PRUEBA MASIVA OCR - BANCOPPEL\n")
        archivo.write("=" * 80 + "\n")
        archivo.write(
            f"Imágenes encontradas: {len(imagenes)}\n"
        )
        archivo.write(
            f"Imágenes procesadas: {len(registros)}\n"
        )
        archivo.write(
            f"Errores: {len(errores)}\n"
        )
        archivo.write(
            f"Tiempo total: {tiempo_total} segundos\n"
        )
        archivo.write(
            f"Híbrido utilizado: {ruta_hibrido}\n"
        )
        archivo.write(
            "Variantes: " + ", ".join(VARIANTES) + "\n"
        )

        archivo.write("\nRESUMEN POR VARIANTE\n")
        archivo.write("=" * 80 + "\n")

        for variante in VARIANTES:
            tiempos = [
                datos["segundos_ocr"]
                for registro in registros
                for nombre, datos
                in registro["variantes"].items()
                if nombre == variante
            ]

            promedio = (
                sum(tiempos) / len(tiempos)
                if tiempos
                else 0
            )

            archivo.write(
                f"\n{variante}\n"
                f"  Procesamientos completados: {len(tiempos)}\n"
                f"  Tiempo OCR promedio: {promedio:.3f}s\n"
            )

        archivo.write("\nDETALLE POR COMPROBANTE\n")
        archivo.write("=" * 80 + "\n")

        for registro in registros:
            archivo.write(
                f"\n\nIMAGEN: {registro['imagen']}\n"
            )

            if registro["error"]:
                archivo.write(
                    f"ERROR: {registro['error']}\n"
                )

            for variante, datos in (
                registro["variantes"].items()
            ):
                archivo.write(
                    f"\n  VARIANTE: {variante}\n"
                )
                archivo.write(
                    f"  Tiempo OCR: "
                    f"{datos['segundos_ocr']}s\n"
                )
                archivo.write(
                    f"  Detecciones: "
                    f"{datos['detecciones']}\n"
                )

                for campo, valor in (
                    datos["campos"].items()
                ):
                    archivo.write(
                        f"  {campo}: {valor}\n"
                    )

                archivo.write(
                    "  Texto OCR: "
                    f"{datos['texto_completo']}\n"
                )

        if errores:
            archivo.write("\nERRORES DETECTADOS\n")
            archivo.write("=" * 80 + "\n")

            for error in errores:
                archivo.write(
                    f"{error['imagen']}: "
                    f"{error['error']}\n"
                )

    # --------------------------------------------------------
    # GENERAR REPORTE JSON GENERAL
    # --------------------------------------------------------

    reporte = {
        "banco": "BANCOPPEL",
        "hibrido": str(ruta_hibrido),
        "total_imagenes": len(imagenes),
        "total_registros": len(registros),
        "tiempo_total_segundos": tiempo_total,
        "variantes": list(VARIANTES),
        "errores": errores,
        "resultados": registros,
    }

    with ruta_reporte_json.open(
        "w",
        encoding="utf-8",
    ) as archivo:
        json.dump(
            reporte,
            archivo,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

    # --------------------------------------------------------
    # RESUMEN FINAL
    # --------------------------------------------------------

    print("\n" + "=" * 75)
    print("PRUEBA MASIVA TERMINADA")
    print("=" * 75)
    print(f"Imágenes: {len(imagenes)}")
    print(f"Errores: {len(errores)}")
    print(f"Tiempo total: {tiempo_total}s")
    print(f"Reporte TXT: {ruta_reporte_txt}")
    print(f"Reporte JSON: {ruta_reporte_json}")
    print("=" * 75)


if __name__ == "__main__":
    main()
