from pathlib import Path
import json
import sys


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

ARCHIVO_SALIDA = (
    CARPETA_RESULTADOS
    / "analisis_cep_bbox.txt"
)


# ============================================================
# ARCHIVOS A ANALIZAR
# ============================================================

ARCHIVOS = [
    "image_070.json",
    "image_203.json",
    "image_469.json",
]


# ============================================================
# ETIQUETAS
# ============================================================

ETIQUETAS = [

    "CLABE interbancaria",

    "Tipo de cuenta",

    "Tipo de beneficiario",

    "Concepto",

    "Referencia Numérica",

    "Número de autorización",

    "Clave de rastreo",

    "Fecha y hora",

]


# ============================================================
# NORMALIZAR
# ============================================================

def normalizar(texto):

    if texto is None:
        return ""

    texto = str(texto).strip().lower()

    reemplazos = {

        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",

        "ñ": "n",

    }

    for origen, destino in reemplazos.items():

        texto = texto.replace(
            origen,
            destino
        )

    return texto


# ============================================================
# CARGAR JSON
# ============================================================

def cargar(nombre):

    ruta = (
        CARPETA_RESULTADOS
        / nombre
    )

    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as archivo:

        return json.load(
            archivo
        )


# ============================================================
# CENTROS BBOX
# ============================================================

def centro_x(deteccion):

    return (
        deteccion.get(
            "x_rel",
            0
        )
        +
        deteccion.get(
            "ancho_rel",
            0
        ) / 2
    )


def centro_y(deteccion):

    return (
        deteccion.get(
            "y_rel",
            0
        )
        +
        deteccion.get(
            "alto_rel",
            0
        ) / 2
    )


# ============================================================
# ESCRITURA
# ============================================================

def escribir(archivo, texto=""):

    archivo.write(
        texto + "\n"
    )


# ============================================================
# ANALIZAR ETIQUETA
# ============================================================

def analizar_etiqueta(
    etiqueta,
    detecciones,
    archivo_salida
):

    etiqueta_normalizada = normalizar(
        etiqueta
    )

    encontrada = None

    # --------------------------------------------------------
    # BUSCAR ETIQUETA
    # --------------------------------------------------------

    for deteccion in detecciones:

        texto = normalizar(
            deteccion.get(
                "texto",
                ""
            )
        )

        if texto == etiqueta_normalizada:

            encontrada = deteccion

            break

    escribir(
        archivo_salida
    )

    escribir(
        archivo_salida,
        "=" * 100
    )

    escribir(
        archivo_salida,
        f"ETIQUETA: {etiqueta}"
    )

    escribir(
        archivo_salida,
        "=" * 100
    )

    # --------------------------------------------------------
    # SI NO EXISTE
    # --------------------------------------------------------

    if encontrada is None:

        escribir(
            archivo_salida,
            "ETIQUETA NO ENCONTRADA"
        )

        return

    # --------------------------------------------------------
    # BBOX ETIQUETA
    # --------------------------------------------------------

    ex = encontrada.get(
        "x_rel",
        0
    )

    ey = encontrada.get(
        "y_rel",
        0
    )

    ew = encontrada.get(
        "ancho_rel",
        0
    )

    eh = encontrada.get(
        "alto_rel",
        0
    )

    ecx = centro_x(
        encontrada
    )

    ecy = centro_y(
        encontrada
    )

    escribir(
        archivo_salida,
        "BBOX DE LA ETIQUETA:"
    )

    escribir(
        archivo_salida,
        f"    x={ex:.6f} "
        f"y={ey:.6f} "
        f"w={ew:.6f} "
        f"h={eh:.6f}"
    )

    escribir(
        archivo_salida,
        f"    centro_x={ecx:.6f} "
        f"centro_y={ecy:.6f}"
    )

    # --------------------------------------------------------
    # CANDIDATOS
    # --------------------------------------------------------

    candidatos = []

    for deteccion in detecciones:

        if deteccion is encontrada:
            continue

        texto = str(
            deteccion.get(
                "texto",
                ""
            )
        ).strip()

        if not texto:
            continue

        x = deteccion.get(
            "x_rel",
            0
        )

        y = deteccion.get(
            "y_rel",
            0
        )

        w = deteccion.get(
            "ancho_rel",
            0
        )

        h = deteccion.get(
            "alto_rel",
            0
        )

        cx = centro_x(
            deteccion
        )

        cy = centro_y(
            deteccion
        )

        # ----------------------------------------------------
        # RELACIONES
        # ----------------------------------------------------

        limite_derecho = (
            ex + ew
        )

        limite_inferior = (
            ey + eh
        )

        if x >= limite_derecho:

            relacion = "DERECHA"

        elif y >= limite_inferior:

            relacion = "DEBAJO"

        elif (
            x + w <= ex
        ):

            relacion = "IZQUIERDA"

        else:

            relacion = "SOLAPADO"

        # ----------------------------------------------------
        # DELTAS
        # ----------------------------------------------------

        dx = (
            x
            -
            limite_derecho
        )

        dy = (
            cy
            -
            ecy
        )

        distancia_x = abs(
            dx
        )

        distancia_y = abs(
            dy
        )

        candidatos.append({

            "texto": texto,

            "relacion": relacion,

            "dx": dx,

            "dy": dy,

            "distancia_x": distancia_x,

            "distancia_y": distancia_y,

            "x": x,

            "y": y,

            "w": w,

            "h": h,

            "confianza": deteccion.get(
                "confianza",
                0
            ),

        })

    # --------------------------------------------------------
    # ORDENAR
    # --------------------------------------------------------

    candidatos.sort(
        key=lambda candidato: (
            candidato["distancia_y"],
            candidato["distancia_x"]
        )
    )

    # --------------------------------------------------------
    # MOSTRAR CANDIDATOS
    # --------------------------------------------------------

    escribir(
        archivo_salida
    )

    escribir(
        archivo_salida,
        "CANDIDATOS MÁS CERCANOS:"
    )

    escribir(
        archivo_salida,
        "-" * 100
    )

    for numero, candidato in enumerate(
        candidatos[:15],
        start=1
    ):

        escribir(
            archivo_salida
        )

        escribir(
            archivo_salida,
            f"[{numero:02d}] "
            f"{candidato['texto']}"
        )

        escribir(
            archivo_salida,
            f"     relación = "
            f"{candidato['relacion']}"
        )

        escribir(
            archivo_salida,
            f"     dx = "
            f"{candidato['dx']:.6f}"
        )

        escribir(
            archivo_salida,
            f"     dy = "
            f"{candidato['dy']:.6f}"
        )

        escribir(
            archivo_salida,
            f"     distancia_x = "
            f"{candidato['distancia_x']:.6f}"
        )

        escribir(
            archivo_salida,
            f"     distancia_y = "
            f"{candidato['distancia_y']:.6f}"
        )

        escribir(
            archivo_salida,
            f"     x={candidato['x']:.6f} "
            f"y={candidato['y']:.6f} "
            f"w={candidato['w']:.6f} "
            f"h={candidato['h']:.6f}"
        )

        escribir(
            archivo_salida,
            f"     confianza="
            f"{candidato['confianza']:.4f}"
        )


# ============================================================
# ANALIZAR ARCHIVO
# ============================================================

def analizar_archivo(
    nombre,
    archivo_salida
):

    datos = cargar(
        nombre
    )

    detecciones = datos.get(
        "detecciones",
        []
    )

    escribir(
        archivo_salida
    )

    escribir(
        archivo_salida,
        "#" * 110
    )

    escribir(
        archivo_salida,
        f"ARCHIVO: {nombre}"
    )

    escribir(
        archivo_salida,
        "#" * 110
    )

    escribir(
        archivo_salida,
        f"Detecciones: {len(detecciones)}"
    )

    for etiqueta in ETIQUETAS:

        analizar_etiqueta(
            etiqueta,
            detecciones,
            archivo_salida
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "=" * 100
    )

    print(
        "ANALISIS BBOX CEP BANAMEX"
    )

    print(
        "=" * 100
    )

    print()

    print(
        "Generando archivo:"
    )

    print(
        ARCHIVO_SALIDA
    )

    CARPETA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        ARCHIVO_SALIDA,
        "w",
        encoding="utf-8"
    ) as archivo_salida:

        escribir(
            archivo_salida,
            "=" * 110
        )

        escribir(
            archivo_salida,
            "ANALISIS BBOX CEP BANAMEX"
        )

        escribir(
            archivo_salida,
            "=" * 110
        )

        escribir(
            archivo_salida
        )

        escribir(
            archivo_salida,
            f"Carpeta: {CARPETA_RESULTADOS}"
        )

        escribir(
            archivo_salida
        )

        for numero, archivo in enumerate(
            ARCHIVOS,
            start=1
        ):

            print(
                f"[{numero}/{len(ARCHIVOS)}] "
                f"Analizando {archivo}..."
            )

            analizar_archivo(
                archivo,
                archivo_salida
            )

        escribir(
            archivo_salida
        )

        escribir(
            archivo_salida,
            "=" * 110
        )

        escribir(
            archivo_salida,
            "ANALISIS TERMINADO"
        )

        escribir(
            archivo_salida,
            "=" * 110
        )

    print()
    print(
        "ANALISIS TERMINADO."
    )

    print()
    print(
        "Archivo generado:"
    )

    print(
        ARCHIVO_SALIDA
    )

    print()


if __name__ == "__main__":

    main()