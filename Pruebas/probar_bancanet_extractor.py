from pathlib import Path
import json

from Services.extractores.banamex.bancanet import (
    extraer_bancanet
)


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

CARPETA_RESULTADOS = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "BANAMEX"
)


# ============================================================
# CLASES COMPATIBLES CON EL EXTRACTOR
# ============================================================

class Deteccion:

    def __init__(
        self,
        datos
    ):

        self.texto = datos.get(
            "texto",
            ""
        )

        self.confianza = datos.get(
            "confianza",
            0.0
        )

        self.x_rel = datos.get(
            "x_rel",
            0.0
        )

        self.y_rel = datos.get(
            "y_rel",
            0.0
        )

        self.ancho_rel = datos.get(
            "ancho_rel",
            0.0
        )

        self.alto_rel = datos.get(
            "alto_rel",
            0.0
        )


class ResultadoOCR:

    def __init__(
        self,
        datos
    ):

        self.texto_completo = datos.get(
            "texto_completo",
            ""
        )

        self.detecciones = [

            Deteccion(
                deteccion
            )

            for deteccion
            in datos.get(
                "detecciones",
                []
            )

        ]


# ============================================================
# MOSTRAR RESULTADO
# ============================================================

def mostrar_resultado(
    resultado
):

    print()

    print(
        "=" * 90
    )

    print(
        "RESULTADO DEL EXTRACTOR"
    )

    print(
        "=" * 90
    )

    print()

    print(
        f"Banco: "
        f"{resultado.banco}"
    )

    print(
        f"Tipo: "
        f"{resultado.tipo_comprobante}"
    )

    print()

    print(
        "CAMPOS:"
    )

    print(
        "-" * 90
    )

    campos = [

        "numero_autorizacion",

        "cuenta_retiro",

        "clabe_asociada",

        "cuenta_deposito",

        "importe",

        "clave_rastreo",

        "tipo_cuenta",

        "tipo_persona",

        "referencia_numerica",

        "concepto",

        "fecha",

        "hora",

    ]

    for campo in campos:

        valor = getattr(
            resultado,
            campo,
            None
        )

        detalle = resultado.detalles.get(
            campo
        )

        if detalle is None:

            print(
                f"{campo:<25}"
                "→ SIN DETALLE"
            )

            continue

        if detalle.encontrado:

            print(
                f"{campo:<25}"
                f"→ {valor}"
            )

            print(
                f"{'':25}"
                f"método={detalle.metodo} "
                f"conf={detalle.confianza:.2f}"
            )

            if detalle.relacion:

                print(
                    f"{'':25}"
                    f"relación={detalle.relacion} "
                    f"dx={detalle.delta_x:.4f} "
                    f"dy={detalle.delta_y:.4f}"
                )

        else:

            print(
                f"{campo:<25}"
                "→ NO ENCONTRADO"
            )

    print()

    print(
        "-" * 90
    )

    print(
        "ESTADÍSTICAS"
    )

    print(
        "-" * 90
    )

    print(
        f"Campos encontrados: "
        f"{resultado.campos_encontrados}/"
        f"{resultado.total_campos}"
    )

    print(
        f"Confianza global: "
        f"{resultado.confianza_global:.4f}"
    )


# ============================================================
# PROCESAR ARCHIVO
# ============================================================

def procesar_archivo(
    ruta_json
):

    print()

    print(
        "#" * 90
    )

    print(
        f"ARCHIVO: {ruta_json.name}"
    )

    print(
        "#" * 90
    )

    try:

        with open(
            ruta_json,
            "r",
            encoding="utf-8"
        ) as archivo:

            datos = json.load(
                archivo
            )

        resultado_ocr = ResultadoOCR(
            datos
        )

        resultado = extraer_bancanet(
            resultado_ocr
        )

        if resultado is None:

            print()

            print(
                "El extractor NO identificó "
                "el comprobante como BancaNet."
            )

            return None

        mostrar_resultado(
            resultado
        )

        return resultado

    except Exception as error:

        print()

        print(
            "ERROR PROCESANDO:"
        )

        print(
            type(error).__name__
        )

        print(
            error
        )

        return None


# ============================================================
# PROCESAR TODAS LAS IMÁGENES
# ============================================================

def procesar():

    print()

    print(
        "=" * 90
    )

    print(
        "PRUEBA EXTRACTOR BANAMEX - BANCANET"
    )

    print(
        "=" * 90
    )

    print()

    print(
        "Carpeta:"
    )

    print(
        CARPETA_RESULTADOS
    )

    archivos = sorted(

        archivo

        for archivo
        in CARPETA_RESULTADOS.glob(
            "image_*.json"
        )

    )

    print()

    print(
        f"JSON encontrados: "
        f"{len(archivos)}"
    )

    print()

    if not archivos:

        print(
            "No se encontraron "
            "resultados OCR."
        )

        return

    resultados = []

    # ========================================================
    # PROCESAR
    # ========================================================

    for numero, archivo in enumerate(
        archivos,
        start=1
    ):

        print()

        print(
            f"[{numero}/{len(archivos)}]"
        )

        resultado = procesar_archivo(
            archivo
        )

        if resultado is not None:

            resultados.append({

                "archivo":
                    archivo.name,

                "resultado":
                    resultado.to_dict(),

            })

    # ========================================================
    # GUARDAR RESULTADOS
    # ========================================================

    salida = (
        CARPETA_RESULTADOS
        /
        "resultados_extractor_bancanet.json"
    )

    with open(
        salida,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(

            resultados,

            archivo,

            ensure_ascii=False,

            indent=4

        )

    # ========================================================
    # RESUMEN FINAL
    # ========================================================

    print()

    print(
        "=" * 90
    )

    print(
        "PRUEBA TERMINADA"
    )

    print(
        "=" * 90
    )

    print()

    print(
        f"Comprobantes BancaNet: "
        f"{len(resultados)}"
    )

    print()

    print(
        "Resultado guardado en:"
    )

    print(
        salida
    )


# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":

    procesar()