import json
from pathlib import Path

from Services.ocr import PaddleOCRServicio
from Services.extractores.nu_mexico.nu_mexico import extraer


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

IMAGEN = (
    RAIZ_PROYECTO
    / "Comprobantes"
    / "NU_MEXICO"
    / "image_079.jpg"
)

JSON_TEMPORAL = (
    RAIZ_PROYECTO
    / "Pruebas"
    / "nu_uno_reprocesado.json"
)


# ============================================================
# EJECUTAR
# ============================================================

def ejecutar():

    print()
    print("=" * 100)
    print("PRUEBA INDIVIDUAL - NU MÉXICO")
    print("=" * 100)
    print()

    print("Imagen:")
    print(IMAGEN)

    print()

    if not IMAGEN.exists():

        print("ERROR: No existe la imagen.")

        return

    # ========================================================
    # OCR
    # ========================================================

    print("=" * 100)
    print("EJECUTANDO OCR NU")
    print("=" * 100)
    print()

    ocr = PaddleOCRServicio(
        idioma="es"
    )

    resultado_ocr = ocr.procesar_imagen(
        str(IMAGEN),
        reprocesar_nu=True
    )

    # ========================================================
    # CONVERTIR OCR A FORMATO JSON
    # ========================================================

    detecciones = []

    for deteccion in resultado_ocr.detecciones:

        detecciones.append(
            {
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
        )

    datos_json = {

        "archivo": IMAGEN.name,

        "banco": "NU_MEXICO",

        "ancho_imagen": resultado_ocr.ancho_imagen,

        "alto_imagen": resultado_ocr.alto_imagen,

        "detecciones": detecciones,

        "lineas": resultado_ocr.lineas,

        "texto_completo": resultado_ocr.texto_completo,
    }

    # ========================================================
    # GUARDAR JSON TEMPORAL
    # ========================================================

    with open(
        JSON_TEMPORAL,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            datos_json,
            archivo,
            ensure_ascii=False,
            indent=4
        )

    print("JSON temporal generado:")

    print(JSON_TEMPORAL)

    print()

    # ========================================================
    # EJECUTAR EXTRACTOR
    # ========================================================

    print("=" * 100)
    print("RESULTADO DEL EXTRACTOR")
    print("=" * 100)
    print()

    resultado = extraer(
        datos_json
    )

    print(
        "Banco:",
        resultado.get(
            "banco",
            "N/A"
        )
    )

    print(
        "Tipo:",
        resultado.get(
            "tipo",
            "N/A"
        )
    )

    print()

    print("CAMPOS:")
    print("-" * 100)

    campos = resultado.get(
        "campos",
        {}
    )

    for nombre, campo in campos.items():

        print()
        print(nombre)

        print(
            campo
        )

    # ========================================================
    # MOSTRAR DETECCIONES RELACIONADAS CON FECHA
    # ========================================================

    print()
    print("=" * 100)
    print("DETECCIONES QUE CONTIENEN INFORMACIÓN DE FECHA")
    print("=" * 100)
    print()

    encontrados_fecha = False

    for deteccion in resultado_ocr.detecciones:

        texto = deteccion.texto.lower()

        if (
            "jul" in texto
            or "jun" in texto
            or "may" in texto
            or "abr" in texto
            or "mar" in texto
            or "feb" in texto
            or "ene" in texto
            or "2026" in texto
            or ":" in texto
            or "hora" in texto
        ):

            encontrados_fecha = True

            print(
                f"x={deteccion.x:.2f} "
                f"y={deteccion.y:.2f} "
                f"conf={deteccion.confianza:.4f} | "
                f"{deteccion.texto}"
            )

    if not encontrados_fecha:

        print(
            "No se encontraron detecciones "
            "relacionadas con fecha."
        )

    print()

    print("=" * 100)
    print("FIN DE PRUEBA")
    print("=" * 100)
    print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    ejecutar()