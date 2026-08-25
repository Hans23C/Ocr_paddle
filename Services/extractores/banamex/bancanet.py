from dataclasses import dataclass, asdict
from typing import Optional
import re

from .reglas import (
    normalizar,
    es_bancanet,
    extraer_autorizacion,
    es_monto,
    es_clave_rastreo,
    es_fecha,
    es_hora,
    es_referencia,
    es_tipo_cuenta,
    es_tipo_persona,
    es_concepto,
)


# ============================================================
# RESULTADO DE CAMPO
# ============================================================

@dataclass
class CampoExtraido:

    nombre: str

    valor: Optional[str] = None

    confianza: float = 0.0

    encontrado: bool = False

    metodo: Optional[str] = None

    etiqueta: Optional[str] = None

    relacion: Optional[str] = None

    delta_x: Optional[float] = None

    delta_y: Optional[float] = None


# ============================================================
# RESULTADO BANCANET
# ============================================================

@dataclass
class ResultadoBancaNet:

    banco: str = "BANAMEX"

    tipo_comprobante: str = "BANCANET"

    numero_autorizacion: Optional[str] = None

    cuenta_retiro: Optional[str] = None

    clabe_asociada: Optional[str] = None

    cuenta_deposito: Optional[str] = None

    importe: Optional[str] = None

    clave_rastreo: Optional[str] = None

    tipo_cuenta: Optional[str] = None

    tipo_persona: Optional[str] = None

    referencia_numerica: Optional[str] = None

    concepto: Optional[str] = None

    fecha: Optional[str] = None

    hora: Optional[str] = None

    confianza_global: float = 0.0

    campos_encontrados: int = 0

    total_campos: int = 12

    detalles: dict = None

    def to_dict(self):

        return asdict(self)


# ============================================================
# CONFIGURACIÓN DE CAMPOS
# ============================================================

CAMPOS = {

    "cuenta_retiro": {

        "etiquetas": [
            "cuenta de retiro"
        ],

        "validador": lambda texto: True,

    },

    "clabe_asociada": {

        "etiquetas": [
            "clabe asociada"
        ],

        "validador": lambda texto: (
            len(
                re.sub(
                    r"\D",
                    "",
                    texto
                )
            ) >= 3
        ),

    },

    "cuenta_deposito": {

        "etiquetas": [
            "cuenta de deposito"
        ],

        "validador": lambda texto: True,

    },

    "importe": {

        "etiquetas": [
            "importe"
        ],

        "validador": es_monto,

    },

    "clave_rastreo": {

        "etiquetas": [
            "clave de rastreo"
        ],

        "validador": es_clave_rastreo,

    },

    "tipo_cuenta": {

        "etiquetas": [
            "tipo de cuenta"
        ],

        "validador": es_tipo_cuenta,

    },

    "tipo_persona": {

        "etiquetas": [
            "tipo de persona"
        ],

        "validador": es_tipo_persona,

    },

    "referencia_numerica": {

        "etiquetas": [
            "referencia numerica"
        ],

        "validador": es_referencia,

    },

    "concepto": {

        "etiquetas": [
            "concepto de pago"
        ],

        "validador": es_concepto,

    },

    "fecha": {

        "etiquetas": [
            "fecha"
        ],

        "validador": es_fecha,

    },

    "hora": {

        "etiquetas": [
            "hora"
        ],

        "validador": es_hora,

    },

}


# ============================================================
# NORMALIZACIÓN FINAL
# ============================================================

def limpiar_valor(texto):

    if texto is None:

        return None

    texto = str(
        texto
    ).strip()

    # Eliminar espacios repetidos
    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    # Eliminar espacios alrededor de guiones
    texto = re.sub(
        r"\s*-\s*",
        "-",
        texto
    )

    return texto.strip()


# ============================================================
# OBTENER DATOS DEL BBOX
# ============================================================

def datos_deteccion(deteccion):

    return {

        "texto": str(
            getattr(
                deteccion,
                "texto",
                ""
            )
        ).strip(),

        "confianza": float(
            getattr(
                deteccion,
                "confianza",
                0.0
            )
        ),

        "x_rel": float(
            getattr(
                deteccion,
                "x_rel",
                0.0
            )
        ),

        "y_rel": float(
            getattr(
                deteccion,
                "y_rel",
                0.0
            )
        ),

        "ancho_rel": float(
            getattr(
                deteccion,
                "ancho_rel",
                0.0
            )
        ),

        "alto_rel": float(
            getattr(
                deteccion,
                "alto_rel",
                0.0
            )
        ),

    }


# ============================================================
# ENCONTRAR ETIQUETA
# ============================================================

def encontrar_etiqueta(
    detecciones,
    etiquetas
):

    etiquetas_norm = [

        normalizar(
            etiqueta
        )

        for etiqueta
        in etiquetas

    ]

    candidatos = []

    for indice, deteccion in enumerate(
        detecciones
    ):

        datos = datos_deteccion(
            deteccion
        )

        texto = normalizar(
            datos["texto"]
        )

        texto_limpio = texto.rstrip(
            ":"
        )

        for etiqueta in etiquetas_norm:

            # ------------------------------------------------
            # ETIQUETA SOLA
            # ------------------------------------------------

            if texto_limpio == etiqueta:

                candidatos.append({

                    "indice":
                        indice,

                    **datos,

                    "tipo":
                        "ETIQUETA_SEPARADA",

                })

            # ------------------------------------------------
            # ETIQUETA + VALOR
            # ------------------------------------------------

            elif texto.startswith(
                etiqueta
            ):

                candidatos.append({

                    "indice":
                        indice,

                    **datos,

                    "tipo":
                        "ETIQUETA_CON_VALOR",

                })

    if not candidatos:

        return None

    candidatos.sort(
        key=lambda x: (
            x["tipo"]
            !=
            "ETIQUETA_SEPARADA",

            -x["confianza"]

        )
    )

    return candidatos[0]


# ============================================================
# EXTRAER VALOR DE LA MISMA DETECCIÓN
# ============================================================

def extraer_valor_misma_deteccion(
    etiqueta,
    etiquetas
):

    texto = normalizar(
        etiqueta["texto"]
    )

    for nombre in etiquetas:

        nombre_norm = normalizar(
            nombre
        )

        if texto.startswith(
            nombre_norm
        ):

            valor = texto[
                len(nombre_norm):
            ]

            valor = valor.lstrip(
                " :-"
            )

            valor = limpiar_valor(
                valor
            )

            if valor:

                return valor

    return None


# ============================================================
# CALCULAR RELACIÓN ESPACIAL
# ============================================================

def calcular_relacion(
    etiqueta,
    valor
):

    etiqueta_x2 = (

        etiqueta["x_rel"]
        +
        etiqueta["ancho_rel"]

    )

    valor_x1 = valor[
        "x_rel"
    ]

    delta_x = (
        valor_x1
        -
        etiqueta_x2
    )

    delta_y = (
        valor["y_rel"]
        -
        etiqueta["y_rel"]
    )

    diferencia_y_abs = abs(
        delta_y
    )

    tolerancia_y = max(
        etiqueta["alto_rel"] * 0.75,
        0.012
    )

    misma_linea = (
        diferencia_y_abs
        <=
        tolerancia_y
    )

    a_la_derecha = (
        valor_x1
        >=
        etiqueta_x2 - 0.02
    )

    if (
        misma_linea
        and
        a_la_derecha
    ):

        relacion = "DERECHA"

    else:

        relacion = "NO_VALIDA"

    return {

        "relacion":
            relacion,

        "delta_x":
            delta_x,

        "delta_y":
            delta_y,

        "misma_linea":
            misma_linea,

        "a_la_derecha":
            a_la_derecha,

    }


# ============================================================
# BUSCAR VALOR A LA DERECHA
# ============================================================

def buscar_valor_derecha(
    detecciones,
    etiqueta,
    validador
):

    candidatos = []

    for indice, deteccion in enumerate(
        detecciones
    ):

        if indice == etiqueta[
            "indice"
        ]:

            continue

        valor = datos_deteccion(
            deteccion
        )

        texto = valor[
            "texto"
        ]

        if not texto:

            continue

        try:

            valido = validador(
                texto
            )

        except Exception:

            valido = False

        if not valido:

            continue

        relacion = calcular_relacion(
            etiqueta,
            valor
        )

        if relacion[
            "relacion"
        ] != "DERECHA":

            continue

        score = 100.0

        score += (
            valor["confianza"]
            * 20
        )

        score -= (
            abs(
                relacion["delta_x"]
            )
            * 25
        )

        score -= (
            abs(
                relacion["delta_y"]
            )
            * 100
        )

        candidatos.append({

            "indice":
                indice,

            "texto":
                texto,

            "confianza":
                valor["confianza"],

            "relacion":
                relacion,

            "score":
                score,

        })

    if not candidatos:

        return None

    candidatos.sort(
        key=lambda x:
        x["score"],
        reverse=True
    )

    return candidatos[0]


# ============================================================
# BUSCAR CUENTA DE DEPÓSITO
# ============================================================

def buscar_cuenta_deposito(
    detecciones,
    etiqueta
):

    datos_etiqueta = datos_deteccion(
        detecciones[
            etiqueta["indice"]
        ]
    )

    etiqueta_x2 = (
        datos_etiqueta["x_rel"]
        +
        datos_etiqueta["ancho_rel"]
    )

    etiqueta_y = (
        datos_etiqueta["y_rel"]
    )

    # ========================================================
    # BUSCAR PRIMERA LÍNEA
    # ========================================================

    candidatos = []

    for indice, deteccion in enumerate(
        detecciones
    ):

        if indice == etiqueta[
            "indice"
        ]:

            continue

        datos = datos_deteccion(
            deteccion
        )

        texto = datos[
            "texto"
        ]

        if not texto:

            continue

        # Debe estar a la derecha
        if (
            datos["x_rel"]
            <
            etiqueta_x2 - 0.03
        ):

            continue

        diferencia_y = abs(
            datos["y_rel"]
            -
            etiqueta_y
        )

        if diferencia_y > 0.012:

            continue

        texto_norm = normalizar(
            texto
        )

        # No tomar "Dato no verificado"
        if (
            "dato no verificado"
            in texto_norm
        ):

            continue

        candidatos.append({

            "indice":
                indice,

            **datos,

        })

    if not candidatos:

        return None

    candidatos.sort(
        key=lambda x: (
            abs(
                x["y_rel"]
                -
                etiqueta_y
            ),

            x["x_rel"]

        )
    )

    primero = candidatos[0]

    partes = [
        primero["texto"]
    ]

    confianzas = [
        primero["confianza"]
    ]

    # ========================================================
    # CONTINUAR CON LÍNEAS SIGUIENTES
    # ========================================================

    x_valor = primero[
        "x_rel"
    ]

    ultimo_y = primero[
        "y_rel"
    ]

    ultimo_indice = primero[
        "indice"
    ]

    for indice in range(
        ultimo_indice + 1,
        len(detecciones)
    ):

        datos = datos_deteccion(
            detecciones[indice]
        )

        texto = datos[
            "texto"
        ]

        if not texto:

            continue

        texto_norm = normalizar(
            texto
        )

        # ====================================================
        # DATO NO VERIFICADO
        # ====================================================

        if (
            "dato no verificado"
            in texto_norm
        ):

            # ------------------------------------------------
            # IMPORTANTE:
            #
            # En BancaNet este texto aparece en la columna
            # izquierda, mientras que la cuenta continúa
            # en la columna derecha.
            #
            # Ejemplo:
            #
            # x=0.07 → (Dato no verificado...)
            # x=0.43 → DE CV
            #
            # Si está en la columna izquierda lo ignoramos
            # y seguimos buscando.
            # ------------------------------------------------

            if datos["x_rel"] < 0.30:

                continue

            break

        # ====================================================
        # ETIQUETAS QUE TERMINAN EL BLOQUE
        # ====================================================

        etiquetas_fin = [

            "detalle del pago",

            "importe",

            "plazo",

            "clave de rastreo",

            "tipo de cuenta",

            "tipo de persona",

            "referencia numerica",

            "referencia numérica",

            "concepto de pago",

            "fecha",

            "hora",

        ]

        if any(
            normalizar(
                etiqueta_fin
            )
            in texto_norm
            for etiqueta_fin
            in etiquetas_fin
        ):

            break

        # ====================================================
        # SOLO HACIA ABAJO
        # ====================================================

        diferencia_y = (
            datos["y_rel"]
            -
            ultimo_y
        )

        if diferencia_y <= 0:

            continue

        # ====================================================
        # TOLERANCIA MULTILÍNEA
        # ====================================================

        if diferencia_y > 0.035:

            break

        # ====================================================
        # MISMA COLUMNA
        # ====================================================

        diferencia_x = abs(
            datos["x_rel"]
            -
            x_valor
        )

        if diferencia_x > 0.08:

            continue

        # ====================================================
        # EVITAR COLUMNA IZQUIERDA
        # ====================================================

        if (
            datos["x_rel"]
            <
            0.30
        ):

            continue

        # ====================================================
        # AGREGAR LÍNEA
        # ====================================================

        partes.append(
            texto
        )

        confianzas.append(
            datos["confianza"]
        )

        ultimo_y = (
            datos["y_rel"]
        )

        ultimo_indice = (
            indice
        )

    # ========================================================
    # UNIR TEXTO
    # ========================================================

    valor_final = limpiar_valor(
        " ".join(
            partes
        )
    )

    return {

        "texto":
            valor_final,

        "confianza":
            (
                sum(confianzas)
                /
                len(confianzas)
            ),

        "indice":
            primero["indice"],

    }


# ============================================================
# EXTRAER CAMPO
# ============================================================

def extraer_campo(
    nombre,
    configuracion,
    detecciones
):

    etiqueta = encontrar_etiqueta(
        detecciones,
        configuracion[
            "etiquetas"
        ]
    )

    if etiqueta is None:

        return CampoExtraido(
            nombre=nombre
        )

    # ========================================================
    # ETIQUETA + VALOR EN MISMO BBOX
    # ========================================================

    if (
        etiqueta["tipo"]
        ==
        "ETIQUETA_CON_VALOR"
    ):

        valor = (
            extraer_valor_misma_deteccion(
                etiqueta,
                configuracion[
                    "etiquetas"
                ]
            )
        )

        if valor:

            return CampoExtraido(

                nombre=
                    nombre,

                valor=
                    valor,

                confianza=
                    etiqueta[
                        "confianza"
                    ],

                encontrado=True,

                metodo=
                    "MISMA_DETECCION",

                etiqueta=
                    etiqueta["texto"],

            )

    # ========================================================
    # CUENTA DE DEPÓSITO
    # ========================================================

    if nombre == "cuenta_deposito":

        candidato = (
            buscar_cuenta_deposito(
                detecciones,
                etiqueta
            )
        )

        if candidato is None:

            return CampoExtraido(

                nombre=
                    nombre,

                etiqueta=
                    etiqueta["texto"]

            )

        return CampoExtraido(

            nombre=
                nombre,

            valor=
                candidato["texto"],

            confianza=
                candidato["confianza"],

            encontrado=True,

            metodo=
                "BBOX_DERECHA_MULTILINEA",

            etiqueta=
                etiqueta["texto"],

        )

    # ========================================================
    # CAMPOS NORMALES
    # ========================================================

    candidato = buscar_valor_derecha(

        detecciones,

        etiqueta,

        configuracion[
            "validador"
        ]

    )

    if candidato is None:

        return CampoExtraido(

            nombre=
                nombre,

            etiqueta=
                etiqueta["texto"]

        )

    relacion = candidato[
        "relacion"
    ]

    return CampoExtraido(

        nombre=
            nombre,

        valor=
            limpiar_valor(
                candidato["texto"]
            ),

        confianza=
            candidato["confianza"],

        encontrado=True,

        metodo=
            "BBOX_DERECHA",

        etiqueta=
            etiqueta["texto"],

        relacion=
            relacion["relacion"],

        delta_x=
            relacion["delta_x"],

        delta_y=
            relacion["delta_y"],

    )


# ============================================================
# EXTRAER BANCANET
# ============================================================

def extraer_bancanet(
    resultado_ocr
):

    texto_completo = str(
        getattr(
            resultado_ocr,
            "texto_completo",
            ""
        )
    )

    # ========================================================
    # VERIFICAR BANCANET
    # ========================================================

    if not es_bancanet(
        texto_completo
    ):

        return None

    detecciones = list(
        getattr(
            resultado_ocr,
            "detecciones",
            []
        )
    )

    resultado = ResultadoBancaNet()

    resultado.detalles = {}

    # ========================================================
    # NÚMERO DE AUTORIZACIÓN
    # ========================================================

    autorizacion = None

    confianza_autorizacion = 0.0

    for deteccion in detecciones:

        texto = str(
            getattr(
                deteccion,
                "texto",
                ""
            )
        )

        valor = (
            extraer_autorizacion(
                texto
            )
        )

        if valor:

            autorizacion = valor

            confianza_autorizacion = float(
                getattr(
                    deteccion,
                    "confianza",
                    0.0
                )
            )

            break

    resultado.numero_autorizacion = (
        autorizacion
    )

    resultado.detalles[
        "numero_autorizacion"
    ] = CampoExtraido(

        nombre=
            "numero_autorizacion",

        valor=
            autorizacion,

        confianza=
            confianza_autorizacion,

        encontrado=
            autorizacion is not None,

        metodo=
            "REGEX",

    )

    # ========================================================
    # EXTRAER CAMPOS
    # ========================================================

    for nombre, configuracion in (
        CAMPOS.items()
    ):

        campo = extraer_campo(

            nombre,

            configuracion,

            detecciones

        )

        resultado.detalles[
            nombre
        ] = campo

        if campo.encontrado:

            setattr(

                resultado,

                nombre,

                campo.valor

            )

    # ========================================================
    # ESTADÍSTICAS
    # ========================================================

    encontrados = 0

    confianzas = []

    for campo in (
        resultado.detalles.values()
    ):

        if campo.encontrado:

            encontrados += 1

            confianzas.append(
                campo.confianza
            )

    resultado.campos_encontrados = (
        encontrados
    )

    if confianzas:

        resultado.confianza_global = (

            sum(
                confianzas
            )
            /
            len(
                confianzas
            )

        )

    return resultado