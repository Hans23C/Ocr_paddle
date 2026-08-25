from pathlib import Path
from collections import defaultdict
import json
import re
import statistics


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_RESULTADOS = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "BANAMEX"
)


# ============================================================
# CAMPOS BANCANET
# ============================================================

CAMPOS_BANCANET = {

    "numero_autorizacion": {
        "etiquetas": [
            "numero de autorizacion",
            "número de autorización",
        ],
        "tipo": "AUTORIZACION",
    },

    "cuenta_retiro": {
        "etiquetas": [
            "cuenta de retiro",
        ],
        "tipo": "CUENTA",
    },

    "clabe_asociada": {
        "etiquetas": [
            "clabe asociada",
        ],
        "tipo": "CUENTA",
    },

    "cuenta_deposito": {
        "etiquetas": [
            "cuenta de deposito",
            "cuenta de depósito",
        ],
        "tipo": "CUENTA",
    },

    "importe": {
        "etiquetas": [
            "importe",
        ],
        "tipo": "MONTO",
    },

    "clave_rastreo": {
        "etiquetas": [
            "clave de rastreo",
        ],
        "tipo": "CLAVE_RASTREO",
    },

    "tipo_cuenta": {
        "etiquetas": [
            "tipo de cuenta",
        ],
        "tipo": "TIPO_CUENTA",
    },

    "tipo_persona": {
        "etiquetas": [
            "tipo de persona",
        ],
        "tipo": "TIPO_PERSONA",
    },

    "referencia_numerica": {
        "etiquetas": [
            "referencia numerica",
            "referencia numérica",
        ],
        "tipo": "REFERENCIA",
    },

    "concepto": {
        "etiquetas": [
            "concepto de pago",
        ],
        "tipo": "CONCEPTO",
    },

    "fecha": {
        "etiquetas": [
            "fecha",
        ],
        "tipo": "FECHA",
    },

    "hora": {
        "etiquetas": [
            "hora",
        ],
        "tipo": "HORA",
    },
}


# ============================================================
# NORMALIZAR TEXTO
# ============================================================

def normalizar(texto):

    texto = str(texto).lower()

    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
    }

    for original, nuevo in reemplazos.items():

        texto = texto.replace(
            original,
            nuevo
        )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


# ============================================================
# DETECTAR BANCANET
# ============================================================

def es_bancanet(datos):

    texto = normalizar(
        datos.get(
            "texto_completo",
            ""
        )
    )

    indicadores = 0

    if "pago interbancario" in texto:
        indicadores += 1

    if "cuenta de retiro" in texto:
        indicadores += 1

    if "cuenta de deposito" in texto:
        indicadores += 1

    if "clave de rastreo" in texto:
        indicadores += 1

    return indicadores >= 2


# ============================================================
# OBTENER DETECCIONES
# ============================================================

def obtener_detecciones(datos):

    detecciones = []

    for deteccion in datos.get(
        "detecciones",
        []
    ):

        texto = str(
            deteccion.get(
                "texto",
                ""
            )
        ).strip()

        if texto:

            detecciones.append(
                deteccion
            )

    return detecciones


# ============================================================
# ENCONTRAR ETIQUETA
# ============================================================

def encontrar_etiqueta(
    detecciones,
    variantes
):

    variantes_normalizadas = {
        normalizar(v)
        for v in variantes
    }

    resultados = []

    for indice, deteccion in enumerate(
        detecciones
    ):

        texto_original = deteccion.get(
            "texto",
            ""
        )

        texto = normalizar(
            texto_original
        )

        texto = texto.rstrip(":")

        if texto in variantes_normalizadas:

            resultados.append({

                "indice":
                    indice,

                "texto":
                    texto_original,

                "x_rel": float(
                    deteccion.get(
                        "x_rel",
                        0
                    )
                ),

                "y_rel": float(
                    deteccion.get(
                        "y_rel",
                        0
                    )
                ),

                "ancho_rel": float(
                    deteccion.get(
                        "ancho_rel",
                        0
                    )
                ),

                "alto_rel": float(
                    deteccion.get(
                        "alto_rel",
                        0
                    )
                ),

                "confianza": float(
                    deteccion.get(
                        "confianza",
                        0
                    )
                ),

            })

    return resultados


# ============================================================
# VALIDAR MONTO
# ============================================================

def validar_monto(texto):

    texto = str(
        texto
    ).strip()

    return bool(
        re.fullmatch(
            r"\$?\s*[\d,]+(?:\.\d{1,2})?(?:\s*(?:MXN|USD|EUR))?",
            texto,
            re.IGNORECASE
        )
    )


# ============================================================
# VALIDAR CLAVE DE RASTREO
# ============================================================

def validar_clave_rastreo(texto):

    numeros = re.sub(
        r"\D",
        "",
        str(texto)
    )

    return bool(
        re.fullmatch(
            r"\d{18}",
            numeros
        )
    )


# ============================================================
# VALIDAR AUTORIZACIÓN
# ============================================================

def validar_autorizacion(texto):

    numeros = re.sub(
        r"\D",
        "",
        str(texto)
    )

    return bool(
        re.fullmatch(
            r"\d{4,8}",
            numeros
        )
    )


# ============================================================
# VALIDAR REFERENCIA
# ============================================================

def validar_referencia(texto):

    numeros = re.sub(
        r"\D",
        "",
        str(texto)
    )

    return bool(
        re.fullmatch(
            r"\d{4,10}",
            numeros
        )
    )


# ============================================================
# VALIDAR HORA
# ============================================================

def validar_hora(texto):

    return bool(
        re.fullmatch(
            r"\d{1,2}:\d{2}(?::\d{2})?",
            str(texto).strip()
        )
    )


# ============================================================
# VALIDAR FECHA
# ============================================================

def validar_fecha(texto):

    texto = str(
        texto
    ).strip()

    patrones = [

        r"\d{1,2}/\d{1,2}/\d{2,4}",

        r"\d{1,2}\s+[A-Za-z]{3,}\s+\d{4}",

        r"\d{1,2}\s+de\s+[A-Za-z]+\s+de\s+\d{4}",

    ]

    return any(
        re.search(
            patron,
            texto,
            re.IGNORECASE
        )
        for patron in patrones
    )


# ============================================================
# VALIDAR CUENTA
# ============================================================

def validar_cuenta(texto):

    texto = str(
        texto
    ).strip()

    if len(texto) < 3:

        return False

    texto_norm = normalizar(
        texto
    )

    etiquetas = {

        "cuenta de retiro",

        "cuenta de deposito",

        "clabe asociada",

        "importe",

        "clave de rastreo",

        "tipo de cuenta",

        "tipo de persona",

        "referencia numerica",

        "concepto de pago",

        "fecha",

        "hora",
    }

    if texto_norm in etiquetas:

        return False

    frases_invalidas = [

        "importante:",

        "no genera",

        "algún costo",

        "algun costo",

        "alguna comisión",

        "alguna comision",

        "comision",

    ]

    for frase in frases_invalidas:

        if normalizar(frase) in texto_norm:

            return False

    return True


# ============================================================
# VALIDAR TIPO DE CUENTA
# ============================================================

def validar_tipo_cuenta(texto):

    texto = normalizar(
        texto
    )

    valores_validos = [

        "clabe",

        "cuenta",

        "tarjeta",

    ]

    return any(
        valor in texto
        for valor in valores_validos
    )


# ============================================================
# VALIDAR TIPO DE PERSONA
# ============================================================

def validar_tipo_persona(texto):

    texto = normalizar(
        texto
    )

    return (

        "persona fisica"
        in texto

        or

        "persona moral"
        in texto

    )


# ============================================================
# VALIDAR CONCEPTO
# ============================================================

def validar_concepto(texto):

    texto = str(
        texto
    ).strip()

    if len(texto) < 3:

        return False

    # No aceptar solamente números

    if re.fullmatch(
        r"\d+",
        texto
    ):

        return False

    # No aceptar importes

    if validar_monto(texto):

        return False

    # No aceptar fechas

    if validar_fecha(texto):

        return False

    # No aceptar horas

    if validar_hora(texto):

        return False

    return True


# ============================================================
# VALIDADORES
# ============================================================

VALIDADORES = {

    "MONTO":
        validar_monto,

    "CLAVE_RASTREO":
        validar_clave_rastreo,

    "AUTORIZACION":
        validar_autorizacion,

    "REFERENCIA":
        validar_referencia,

    "HORA":
        validar_hora,

    "FECHA":
        validar_fecha,

    "CUENTA":
        validar_cuenta,

    "TIPO_CUENTA":
        validar_tipo_cuenta,

    "TIPO_PERSONA":
        validar_tipo_persona,

    "CONCEPTO":
        validar_concepto,
}


# ============================================================
# ANALIZAR RELACIÓN ENTRE BBOX
# ============================================================

def analizar_relacion(
    etiqueta,
    valor
):

    etiqueta_x2 = (

        etiqueta["x_rel"]
        +
        etiqueta["ancho_rel"]

    )

    etiqueta_y2 = (

        etiqueta["y_rel"]
        +
        etiqueta["alto_rel"]

    )

    delta_x = (

        valor["x_rel"]
        -
        etiqueta_x2

    )

    delta_y = (

        valor["y_rel"]
        -
        etiqueta["y_rel"]

    )

    misma_linea = (

        abs(delta_y)

        <=

        max(
            etiqueta["alto_rel"] * 1.5,
            0.015
        )

    )

    a_la_derecha = (

        valor["x_rel"]

        >=

        etiqueta_x2 - 0.02

    )

    debajo = (

        valor["y_rel"]

        >=

        etiqueta_y2 - 0.02

    )

    if (

        misma_linea

        and

        a_la_derecha

    ):

        relacion = "DERECHA"

    elif debajo:

        relacion = "DEBAJO"

    else:

        relacion = "OTRA"

    return {

        "delta_x":
            delta_x,

        "delta_y":
            delta_y,

        "misma_linea":
            misma_linea,

        "a_la_derecha":
            a_la_derecha,

        "debajo":
            debajo,

        "relacion":
            relacion,

    }


# ============================================================
# BUSCAR VALOR
# ============================================================

def buscar_valor(
    etiqueta,
    tipo_campo,
    detecciones
):

    candidatos = []

    validador = VALIDADORES.get(
        tipo_campo
    )

    for indice, deteccion in enumerate(
        detecciones
    ):

        # No usar la propia etiqueta

        if indice == etiqueta["indice"]:

            continue

        texto = str(
            deteccion.get(
                "texto",
                ""
            )
        ).strip()

        if not texto:

            continue

        # ----------------------------------------------------
        # VALIDAR TIPO DE DATO
        # ----------------------------------------------------

        if validador is not None:

            try:

                valido = validador(
                    texto
                )

            except Exception:

                valido = False

            if not valido:

                continue

        valor = {

            "indice":
                indice,

            "texto":
                texto,

            "x_rel": float(
                deteccion.get(
                    "x_rel",
                    0
                )
            ),

            "y_rel": float(
                deteccion.get(
                    "y_rel",
                    0
                )
            ),

            "ancho_rel": float(
                deteccion.get(
                    "ancho_rel",
                    0
                )
            ),

            "alto_rel": float(
                deteccion.get(
                    "alto_rel",
                    0
                )
            ),

            "confianza": float(
                deteccion.get(
                    "confianza",
                    0
                )
            ),

        }

        relacion = analizar_relacion(
            etiqueta,
            valor
        )

        # ----------------------------------------------------
        # PARA BANCANET EXIGIMOS MISMA LÍNEA + DERECHA
        # ----------------------------------------------------

        if relacion["relacion"] != "DERECHA":

            continue

        # ----------------------------------------------------
        # SCORE
        # ----------------------------------------------------

        score = 100

        if relacion["misma_linea"]:

            score += 40

        score += (
            valor["confianza"]
            * 20
        )

        score -= (
            abs(
                relacion["delta_x"]
            )
            * 30
        )

        valor["relacion"] = relacion

        valor["score"] = score

        candidatos.append(
            valor
        )

    # --------------------------------------------------------
    # NO HAY CANDIDATOS
    # --------------------------------------------------------

    if not candidatos:

        return None

    # --------------------------------------------------------
    # ORDENAR POR SCORE
    # --------------------------------------------------------

    candidatos.sort(
        key=lambda x:
        x["score"],
        reverse=True
    )

    return candidatos[0]


# ============================================================
# ANALIZAR UN ARCHIVO
# ============================================================

def analizar_archivo(
    ruta_json
):

    with open(
        ruta_json,
        "r",
        encoding="utf-8"
    ) as archivo:

        datos = json.load(
            archivo
        )

    # --------------------------------------------------------
    # VERIFICAR QUE SEA BANCANET
    # --------------------------------------------------------

    if not es_bancanet(
        datos
    ):

        return None

    detecciones = obtener_detecciones(
        datos
    )

    resultado = {

        "archivo":
            datos.get(
                "archivo",
                ruta_json.name
            ),

        "tipo":
            "BANCANET",

        "campos":
            {},

    }

    # --------------------------------------------------------
    # PROCESAR CAMPOS
    # --------------------------------------------------------

    for (
        nombre_campo,
        configuracion
    ) in CAMPOS_BANCANET.items():

        etiquetas = encontrar_etiqueta(
            detecciones,
            configuracion["etiquetas"]
        )

        # ----------------------------------------------------
        # ETIQUETA NO ENCONTRADA
        # ----------------------------------------------------

        if not etiquetas:

            resultado[
                "campos"
            ][
                nombre_campo
            ] = {

                "encontrado":
                    False,

            }

            continue

        etiqueta = etiquetas[0]

        # ----------------------------------------------------
        # BUSCAR VALOR
        # ----------------------------------------------------

        valor = buscar_valor(
            etiqueta,
            configuracion["tipo"],
            detecciones
        )

        resultado[
            "campos"
        ][
            nombre_campo
        ] = {

            "encontrado":
                True,

            "etiqueta":
                etiqueta,

            "valor":
                valor,

        }

    return resultado


# ============================================================
# ANALIZAR TODOS LOS JSON
# ============================================================

def analizar_todos():

    # --------------------------------------------------------
    # SOLO ANALIZAR JSON DE IMÁGENES
    # --------------------------------------------------------

    archivos = sorted(

        archivo

        for archivo
        in CARPETA_RESULTADOS.glob(
            "*.json"
        )

        if archivo.name.startswith(
            "image_"
        )

    )

    print()

    print("=" * 90)

    print(
        "ANALIZADOR BBOX V2 - BANCANET"
    )

    print("=" * 90)

    print()

    print(
        "Carpeta:",
        CARPETA_RESULTADOS
    )

    print()

    print(
        "JSON de imágenes encontrados:",
        len(archivos)
    )

    resultados = []

    # ========================================================
    # PROCESAR ARCHIVOS
    # ========================================================

    for archivo in archivos:

        try:

            resultado = analizar_archivo(
                archivo
            )

            if resultado is None:

                continue

            resultados.append(
                resultado
            )

            print()

            print(
                "-" * 90
            )

            print(
                resultado["archivo"]
            )

            print(
                "-" * 90
            )

            # ------------------------------------------------
            # MOSTRAR CAMPOS
            # ------------------------------------------------

            for (
                campo,
                datos
            ) in resultado[
                "campos"
            ].items():

                # --------------------------------------------
                # ETIQUETA NO ENCONTRADA
                # --------------------------------------------

                if not datos[
                    "encontrado"
                ]:

                    print(

                        f"{campo:<25}"

                        "ETIQUETA NO ENCONTRADA"

                    )

                    continue

                etiqueta = datos[
                    "etiqueta"
                ]

                valor = datos.get(
                    "valor"
                )

                # --------------------------------------------
                # VALOR NO ENCONTRADO
                # --------------------------------------------

                if valor is None:

                    print(

                        f"{campo:<25}"

                        f"Etiqueta: "
                        f"{etiqueta['texto']:<25}"

                        "VALOR NO ENCONTRADO"

                    )

                    continue

                # --------------------------------------------
                # RELACIÓN
                # --------------------------------------------

                relacion = valor[
                    "relacion"
                ]

                print(

                    f"{campo:<25}"

                    f"→ {valor['texto']:<35}"

                    f"[{relacion['relacion']}] "

                    f"dx={relacion['delta_x']:.4f} "

                    f"dy={relacion['delta_y']:.4f} "

                    f"conf={valor['confianza']:.2f} "

                    f"score={valor['score']:.2f}"

                )

        except Exception as error:

            print()

            print(
                f"ERROR: {archivo.name}"
            )

            print(
                f"{type(error).__name__}: "
                f"{error}"
            )

    # ========================================================
    # GUARDAR RESULTADO
    # ========================================================

    salida = (

        CARPETA_RESULTADOS

        /

        "analisis_bancanet_bbox_v2.json"

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
    # RESUMEN
    # ========================================================

    print()

    print(
        "=" * 90
    )

    print(

        "ARCHIVOS BANCANET ANALIZADOS:",

        len(resultados)

    )

    print()

    print(
        "Resultado:"
    )

    print(
        salida
    )

    # ========================================================
    # ESTADÍSTICAS
    # ========================================================

    generar_estadisticas(
        resultados
    )


# ============================================================
# GENERAR ESTADÍSTICAS
# ============================================================

def generar_estadisticas(
    resultados
):

    print()

    print(
        "=" * 90
    )

    print(
        "ESTABILIDAD ETIQUETA → VALOR"
    )

    print(
        "=" * 90
    )

    agrupados = defaultdict(
        list
    )

    # --------------------------------------------------------
    # AGRUPAR RELACIONES
    # --------------------------------------------------------

    for resultado in resultados:

        for (
            campo,
            datos
        ) in resultado[
            "campos"
        ].items():

            valor = datos.get(
                "valor"
            )

            if valor is None:

                continue

            relacion = valor[
                "relacion"
            ]

            agrupados[
                (
                    campo,
                    relacion[
                        "relacion"
                    ]
                )
            ].append(
                valor
            )

    if not agrupados:

        print()

        print(
            "No se encontraron "
            "relaciones etiqueta → valor."
        )

        return

    # --------------------------------------------------------
    # MOSTRAR ESTADÍSTICAS
    # --------------------------------------------------------

    for (
        campo,
        relacion
    ), valores in sorted(
        agrupados.items()
    ):

        dx = [

            valor[
                "relacion"
            ][
                "delta_x"
            ]

            for valor
            in valores

        ]

        dy = [

            valor[
                "relacion"
            ][
                "delta_y"
            ]

            for valor
            in valores

        ]

        print()

        print(
            f"{campo} → {relacion}"
        )

        print(

            f"  Casos: "
            f"{len(valores)}"

        )

        print(

            f"  ΔX promedio: "
            f"{statistics.mean(dx):.4f}"

        )

        print(

            f"  ΔX mínimo: "
            f"{min(dx):.4f}"

        )

        print(

            f"  ΔX máximo: "
            f"{max(dx):.4f}"

        )

        print(

            f"  ΔY promedio: "
            f"{statistics.mean(dy):.4f}"

        )

        print(

            f"  ΔY mínimo: "
            f"{min(dy):.4f}"

        )

        print(

            f"  ΔY máximo: "
            f"{max(dy):.4f}"

        )

        if len(dx) >= 2:

            print(

                f"  Desv. ΔX: "
                f"{statistics.stdev(dx):.4f}"

            )

        if len(dy) >= 2:

            print(

                f"  Desv. ΔY: "
                f"{statistics.stdev(dy):.4f}"

            )


# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":

    analizar_todos()