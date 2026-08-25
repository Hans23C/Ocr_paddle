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
# ETIQUETAS QUE QUEREMOS ESTUDIAR
# ============================================================

ETIQUETAS_TRANSFERENCIA = {

    "fecha_hora": [
        "fecha y hora",
        "fecha/hora",
    ],

    "importe": [
        "importe",
    ],

    "cuenta_origen": [
        "cuenta origen",
        "origen",
    ],

    "cuenta_destino": [
        "cuenta destino",
        "destino",
    ],

    "numero_autorizacion": [
        "numero de autorizacion",
        "número de autorización",
        "autorizacion",
        "autorización",
    ],

    "clave_rastreo": [
        "clave de rastreo",
        "clave rastreo",
        "rastreo",
    ],

    "tipo_cuenta": [
        "tipo de cuenta",
    ],

    "tipo_beneficiario": [
        "tipo de beneficiario",
    ],

    "concepto": [
        "concepto",
    ],

    "referencia_numerica": [
        "referencia numerica",
        "referencia numérica",
        "ref numerica",
        "ref numérica",
    ],
}


ETIQUETAS_BANCANET = {

    "numero_autorizacion": [
        "numero de autorizacion",
        "número de autorización",
    ],

    "cuenta_retiro": [
        "cuenta de retiro",
    ],

    "clabe_asociada": [
        "clabe asociada",
    ],

    "cuenta_deposito": [
        "cuenta de deposito",
        "cuenta de depósito",
    ],

    "importe": [
        "importe",
    ],

    "clave_rastreo": [
        "clave de rastreo",
    ],

    "tipo_cuenta": [
        "tipo de cuenta",
    ],

    "tipo_persona": [
        "tipo de persona",
    ],

    "referencia_numerica": [
        "referencia numerica",
        "referencia numérica",
    ],

    "concepto": [
        "concepto de pago",
    ],

    "fecha": [
        "fecha",
    ],

    "hora": [
        "hora",
    ],
}


ETIQUETAS_CEP = {

    "numero_referencia": [
        "numero de referencia",
        "número de referencia",
    ],

    "clave_rastreo": [
        "clave de rastreo",
    ],

    "institucion_emisora": [
        "institucion emisora del pago",
        "institución emisora del pago",
    ],

    "institucion_receptora": [
        "institucion receptora del pago",
        "institución receptora del pago",
    ],

    "estado_pago": [
        "estado del pago en banxico",
    ],

    "fecha_operacion": [
        "fecha de operacion",
        "fecha de operación",
    ],

    "fecha_abono": [
        "fecha de abono",
    ],

    "monto": [
        "monto",
    ],

    "iva": [
        "iva",
    ],

    "ordenante": [
        "ordenante",
    ],

    "beneficiario": [
        "beneficiario",
    ],

    "titular_cuenta": [
        "titular de la cuenta",
    ],

    "clabe": [
        "clabe",
    ],

    "rfc_curp": [
        "rfc/curp",
        "rfc curp",
    ],
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
# CLASIFICAR COMPROBANTE
# ============================================================

def detectar_tipo(datos):

    texto = normalizar(
        datos.get(
            "texto_completo",
            ""
        )
    )

    if (
        "comprobante electronico de pago (cep) consulta"
        in texto
    ):
        return "CEP_CONSULTA"

    if (
        "comprobante electronico de pago"
        in texto
        or "comprobante electronico de pago (cep)"
        in texto
    ):
        return "CEP"

    if (
        "banamex bancanet"
        in texto
        or "pago interbancario"
        in texto
    ):
        return "BANCANET"

    if (
        "comprobante de transferencia"
        in texto
        or "transferencia exitosa"
        in texto
    ):
        return "TRANSFERENCIA"

    return "OTRO"


# ============================================================
# OBTENER DETECCIONES
# ============================================================

def obtener_detecciones(datos):

    detecciones = []

    for d in datos.get(
        "detecciones",
        []
    ):

        texto = str(
            d.get("texto", "")
        ).strip()

        if not texto:
            continue

        detecciones.append(d)

    return detecciones


# ============================================================
# BUSCAR ETIQUETAS
# ============================================================

def buscar_etiquetas(
    detecciones,
    etiquetas
):

    encontrados = []

    for indice, deteccion in enumerate(
        detecciones
    ):

        texto = normalizar(
            deteccion.get(
                "texto",
                ""
            )
        )

        for nombre_campo, variantes in etiquetas.items():

            for variante in variantes:

                variante_norm = normalizar(
                    variante
                )

                if (
                    texto == variante_norm
                    or variante_norm in texto
                ):

                    encontrados.append({

                        "campo":
                            nombre_campo,

                        "indice":
                            indice,

                        "texto":
                            deteccion.get(
                                "texto",
                                ""
                            ),

                        "x":
                            deteccion.get(
                                "x",
                                0
                            ),

                        "y":
                            deteccion.get(
                                "y",
                                0
                            ),

                        "x_rel":
                            deteccion.get(
                                "x_rel",
                                0
                            ),

                        "y_rel":
                            deteccion.get(
                                "y_rel",
                                0
                            ),

                        "ancho_rel":
                            deteccion.get(
                                "ancho_rel",
                                0
                            ),

                        "alto_rel":
                            deteccion.get(
                                "alto_rel",
                                0
                            ),

                        "confianza":
                            deteccion.get(
                                "confianza",
                                0
                            ),

                    })

                    break

    return encontrados


# ============================================================
# DISTANCIA ENTRE DOS BBOX
# ============================================================

def distancia_horizontal(
    etiqueta,
    valor
):

    etiqueta_x2 = (
        etiqueta["x_rel"]
        + etiqueta["ancho_rel"]
    )

    valor_x = valor["x_rel"]

    return valor_x - etiqueta_x2


def distancia_vertical(
    etiqueta,
    valor
):

    etiqueta_y2 = (
        etiqueta["y_rel"]
        + etiqueta["alto_rel"]
    )

    valor_y = valor["y_rel"]

    return valor_y - etiqueta_y2


# ============================================================
# DETERMINAR SI UN TEXTO PUEDE SER VALOR
# ============================================================

def parece_valor(
    texto
):

    texto_norm = normalizar(
        texto
    )

    if not texto_norm:
        return False

    # Evitar etiquetas conocidas
    etiquetas_comunes = [
        "cuenta",
        "importe",
        "fecha",
        "hora",
        "concepto",
        "referencia",
        "clave",
        "tipo",
        "datos",
        "numero",
        "número",
        "institucion",
        "institución",
        "beneficiario",
        "ordenante",
    ]

    if texto_norm in etiquetas_comunes:
        return False

    return True


# ============================================================
# BUSCAR VALOR ASOCIADO A UNA ETIQUETA
# ============================================================

def buscar_valor_cercano(
    etiqueta,
    detecciones
):

    candidatos = []

    for indice, deteccion in enumerate(
        detecciones
    ):

        if (
            deteccion.get(
                "texto",
                ""
            )
            == etiqueta["texto"]
        ):
            continue

        texto = deteccion.get(
            "texto",
            ""
        )

        if not parece_valor(texto):
            continue

        x = deteccion.get(
            "x_rel",
            0
        )

        y = deteccion.get(
            "y_rel",
            0
        )

        # ----------------------------------------------------
        # Preferencia 1:
        # mismo renglón y a la derecha
        # ----------------------------------------------------

        misma_linea = abs(
            y - etiqueta["y_rel"]
        ) <= max(
            etiqueta["alto_rel"] * 1.5,
            0.015
        )

        a_la_derecha = (
            x >=
            etiqueta["x_rel"]
        )

        if misma_linea and a_la_derecha:

            distancia = distancia_horizontal(
                etiqueta,
                deteccion
            )

            if distancia >= -0.02:

                candidatos.append({

                    "deteccion":
                        deteccion,

                    "tipo":
                        "DERECHA",

                    "distancia":
                        abs(distancia),

                })

    # --------------------------------------------------------
    # Si no encontramos a la derecha:
    # buscar debajo
    # --------------------------------------------------------

    if not candidatos:

        for deteccion in detecciones:

            texto = deteccion.get(
                "texto",
                ""
            )

            if not parece_valor(texto):
                continue

            y = deteccion.get(
                "y_rel",
                0
            )

            x = deteccion.get(
                "x_rel",
                0
            )

            debajo = (
                y >= etiqueta["y_rel"]
            )

            x_similar = abs(
                x - etiqueta["x_rel"]
            ) <= 0.25

            if debajo and x_similar:

                distancia = distancia_vertical(
                    etiqueta,
                    deteccion
                )

                if distancia >= -0.02:

                    candidatos.append({

                        "deteccion":
                            deteccion,

                        "tipo":
                            "DEBAJO",

                        "distancia":
                            abs(distancia),

                    })

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda c: c["distancia"]
    )

    return candidatos[0]


# ============================================================
# ANALIZAR ARCHIVO
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

    tipo = detectar_tipo(
        datos
    )

    detecciones = obtener_detecciones(
        datos
    )

    if tipo == "TRANSFERENCIA":

        etiquetas = ETIQUETAS_TRANSFERENCIA

    elif tipo == "BANCANET":

        etiquetas = ETIQUETAS_BANCANET

    elif tipo == "CEP":

        etiquetas = ETIQUETAS_CEP

    else:

        etiquetas = {}

    etiquetas_encontradas = buscar_etiquetas(
        detecciones,
        etiquetas
    )

    campos = []

    for etiqueta in etiquetas_encontradas:

        valor = buscar_valor_cercano(
            etiqueta,
            detecciones
        )

        registro = {

            "campo":
                etiqueta["campo"],

            "etiqueta":
                etiqueta["texto"],

            "etiqueta_x_rel":
                etiqueta["x_rel"],

            "etiqueta_y_rel":
                etiqueta["y_rel"],

            "etiqueta_ancho_rel":
                etiqueta["ancho_rel"],

            "etiqueta_alto_rel":
                etiqueta["alto_rel"],

            "confianza_etiqueta":
                etiqueta["confianza"],

        }

        if valor:

            d = valor["deteccion"]

            registro.update({

                "valor_detectado":
                    d.get(
                        "texto",
                        ""
                    ),

                "valor_x_rel":
                    d.get(
                        "x_rel",
                        0
                    ),

                "valor_y_rel":
                    d.get(
                        "y_rel",
                        0
                    ),

                "valor_ancho_rel":
                    d.get(
                        "ancho_rel",
                        0
                    ),

                "valor_alto_rel":
                    d.get(
                        "alto_rel",
                        0
                    ),

                "confianza_valor":
                    d.get(
                        "confianza",
                        0
                    ),

                "relacion":
                    valor["tipo"],

                "distancia":
                    valor["distancia"],

            })

        else:

            registro.update({

                "valor_detectado":
                    "",

                "relacion":
                    "NO_ENCONTRADO",

            })

        campos.append(
            registro
        )

    return {

        "archivo":
            datos.get(
                "archivo",
                ruta_json.name
            ),

        "tipo":
            tipo,

        "campos":
            campos,

        "detecciones":
            len(detecciones),

    }


# ============================================================
# ANALIZAR TODOS
# ============================================================

def analizar_todos():

    archivos = sorted(
        CARPETA_RESULTADOS.glob(
            "*.json"
        )
    )

    print()
    print("=" * 80)
    print("ANÁLISIS BBOX - BANAMEX")
    print("=" * 80)

    print(
        f"\nArchivos encontrados: "
        f"{len(archivos)}"
    )

    resultados = []

    for numero, ruta in enumerate(
        archivos,
        start=1
    ):

        print()
        print("-" * 80)

        try:

            resultado = analizar_archivo(
                ruta
            )

            resultados.append(
                resultado
            )

            print(
                f"[{numero}/{len(archivos)}] "
                f"{resultado['archivo']}"
            )

            print(
                f"Tipo: {resultado['tipo']}"
            )

            for campo in resultado["campos"]:

                valor = campo.get(
                    "valor_detectado",
                    ""
                )

                print(
                    f"  {campo['campo']:<25}"
                    f"Etiqueta: "
                    f"{campo['etiqueta']:<25}"
                    f"Valor: {valor}"
                )

        except Exception as error:

            print(
                f"ERROR: {ruta.name}"
            )

            print(
                type(error).__name__,
                error
            )

    # ========================================================
    # GUARDAR RESULTADO DETALLADO
    # ========================================================

    ruta_salida = (
        CARPETA_RESULTADOS
        / "analisis_bbox_banamex.json"
    )

    with open(
        ruta_salida,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            resultados,
            archivo,
            ensure_ascii=False,
            indent=4
        )

    print()
    print("=" * 80)
    print(
        "ANÁLISIS TERMINADO"
    )

    print()
    print(
        "Resultado:"
    )

    print(
        ruta_salida
    )

    # ========================================================
    # RESUMEN ESTADÍSTICO
    # ========================================================

    generar_resumen(
        resultados
    )


# ============================================================
# RESUMEN
# ============================================================

def generar_resumen(
    resultados
):

    print()
    print("=" * 80)
    print("RESUMEN DE ESTABILIDAD BBOX")
    print("=" * 80)

    agrupados = defaultdict(list)

    for resultado in resultados:

        tipo = resultado["tipo"]

        for campo in resultado["campos"]:

            if (
                campo.get(
                    "relacion"
                )
                == "NO_ENCONTRADO"
            ):
                continue

            agrupados[
                (
                    tipo,
                    campo["campo"]
                )
            ].append(
                campo
            )

    for (
        tipo,
        campo
    ), registros in sorted(
        agrupados.items()
    ):

        xs = [
            r["etiqueta_x_rel"]
            for r in registros
        ]

        ys = [
            r["etiqueta_y_rel"]
            for r in registros
        ]

        print()
        print(
            f"\n[{tipo}] {campo}"
        )

        print(
            f"  Apariciones: "
            f"{len(registros)}"
        )

        print(
            f"  X promedio: "
            f"{statistics.mean(xs):.4f}"
        )

        print(
            f"  X mínimo: "
            f"{min(xs):.4f}"
        )

        print(
            f"  X máximo: "
            f"{max(xs):.4f}"
        )

        print(
            f"  Y promedio: "
            f"{statistics.mean(ys):.4f}"
        )

        print(
            f"  Y mínimo: "
            f"{min(ys):.4f}"
        )

        print(
            f"  Y máximo: "
            f"{max(ys):.4f}"
        )

        if len(ys) >= 2:

            desviacion = statistics.stdev(
                ys
            )

            print(
                f"  Desviación Y: "
                f"{desviacion:.4f}"
            )


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    analizar_todos()