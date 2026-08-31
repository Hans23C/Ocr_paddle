from pathlib import Path
import json
import sys

from Services.extractores.santander.santander import SantanderExtractor


# ============================================================
# RUTAS
# ============================================================

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

CARPETA_JSON = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "SANTANDER"
)


# ============================================================
# COMPROBANTE A PROBAR
# ============================================================

NOMBRE_ARCHIVO = "image_511.json"

RUTA_JSON = CARPETA_JSON / NOMBRE_ARCHIVO


# ============================================================
# CAMPOS POR TIPO DE COMPROBANTE
# ============================================================

CAMPOS_REF_SUPERMOVIL = [

    "banco_emisor",
    "monto",
    "fecha_hora_operacion",
    "cuenta_origen",
    "banco_destino",
    "estatus",
    "ref_supermovil",
    "tipo_operacion",
    "concepto",

]


CAMPOS_REFERENCIA = [

    "banco_emisor",
    "monto",
    "fecha",
    "concepto",
    "banco_destino",
    "cuenta_destino",
    "cuenta",
    "sucursal",
    "referencia",
    "saldo_posterior",
    "hora",
    "numero_referencia",
    "clave_rastreo",

]


CAMPOS_CEP = [

    "institucion_emisora",
    "fecha_operacion",
    "concepto",
    "monto",
    "referencia_numerica",
    "clave_rastreo",
    "institucion_receptora",
    "titular_cuenta_beneficiario",
    "clabe_beneficiario",

]


# ============================================================
# MOSTRAR CAMPO
# ============================================================

def mostrar_campo(nombre, datos):

    print()

    print(nombre)

    print(
        "-" * 70
    )

    if not datos:

        print(
            "NO ENCONTRADO"
        )

        return False

    valor = datos.get(
        "valor"
    )

    if valor is None:

        print(
            "NO ENCONTRADO"
        )

        return False

    print(
        f"Valor:      {valor}"
    )

    print(
        f"Método:     {datos.get('metodo', 'N/A')}"
    )

    print(
        f"Confianza:  "
        f"{datos.get('confianza', 0):.4f}"
    )

    return True


# ============================================================
# CAMPOS SEGÚN TIPO
# ============================================================

def obtener_campos_por_tipo(tipo):

    if tipo == "REF_SUPERMOVIL_SANTANDER":

        return CAMPOS_REF_SUPERMOVIL

    if tipo == "TRANSFERENCIA_SANTANDER_REFERENCIA":

        return CAMPOS_REFERENCIA

    if tipo == "CEP_SANTANDER":

        return CAMPOS_CEP

    return []


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print("=" * 90)
    print("PRUEBA INDIVIDUAL - SANTANDER")
    print("=" * 90)

    print()

    print("JSON:")

    print(
        RUTA_JSON
    )

    print()

    # --------------------------------------------------------
    # VALIDAR JSON
    # --------------------------------------------------------

    if not RUTA_JSON.exists():

        print(
            "ERROR: No existe el JSON."
        )

        print()

        print(
            RUTA_JSON
        )

        sys.exit(1)

    # --------------------------------------------------------
    # CARGAR JSON
    # --------------------------------------------------------

    print(
        "Cargando JSON..."
    )

    try:

        with open(
            RUTA_JSON,
            "r",
            encoding="utf-8"
        ) as archivo:

            datos = json.load(
                archivo
            )

    except Exception as error:

        print()

        print(
            "ERROR LEYENDO JSON:"
        )

        print(
            type(error).__name__
        )

        print(
            error
        )

        sys.exit(1)

    print(
        "JSON cargado correctamente."
    )

    # --------------------------------------------------------
    # OCR
    # --------------------------------------------------------

    detecciones = datos.get(
        "detecciones",
        []
    )

    print()

    print(
        f"Detecciones OCR: "
        f"{len(detecciones)}"
    )

    # --------------------------------------------------------
    # MOSTRAR DETECCIONES
    # --------------------------------------------------------

    print()

    print("=" * 90)
    print("DETECCIONES OCR")
    print("=" * 90)

    for indice, deteccion in enumerate(
        detecciones
    ):

        print(
            f"{indice:03d} | "
            f"x={deteccion.get('x', 0):.2f} "
            f"y={deteccion.get('y', 0):.2f} "
            f"conf={deteccion.get('confianza', 0):.4f} | "
            f"{deteccion.get('texto', '')}"
        )

    # --------------------------------------------------------
    # EXTRACTOR
    # --------------------------------------------------------

    print()

    print("=" * 90)
    print("EJECUTANDO EXTRACTOR SANTANDER")
    print("=" * 90)

    try:

        extractor = SantanderExtractor()

        resultado = extractor.extraer(
            datos
        )

    except Exception as error:

        print()

        print(
            "ERROR EJECUTANDO EXTRACTOR:"
        )

        print(
            type(error).__name__
        )

        print(
            error
        )

        sys.exit(1)

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    print()

    print("=" * 90)
    print("RESULTADO DEL EXTRACTOR")
    print("=" * 90)

    print()

    banco = resultado.get(
        "banco"
    )

    tipo = resultado.get(
        "tipo"
    )

    print(
        "Banco:"
    )

    print(
        banco
    )

    print()

    print(
        "Tipo:"
    )

    print(
        tipo
    )

    # --------------------------------------------------------
    # CAMPOS
    # --------------------------------------------------------

    campos = resultado.get(
        "campos",
        {}
    )

    campos_a_mostrar = obtener_campos_por_tipo(
        tipo
    )

    print()

    print("=" * 90)
    print("CAMPOS EXTRAÍDOS")
    print("=" * 90)

    # --------------------------------------------------------
    # TIPO DESCONOCIDO
    # --------------------------------------------------------

    if not campos_a_mostrar:

        print()

        print(
            "ADVERTENCIA:"
        )

        print(
            "El extractor devolvió un tipo de comprobante"
        )

        print(
            "que todavía no tiene una estructura definida"
        )

        print()

        print(
            f"Tipo recibido: {tipo}"
        )

        print()

        print(
            "Campos devueltos por el extractor:"
        )

        print()

        for nombre, datos_campo in campos.items():

            mostrar_campo(
                nombre,
                datos_campo
            )

        print()

        print("=" * 90)
        print("FIN DE PRUEBA")
        print("=" * 90)

        print()

        return

    # --------------------------------------------------------
    # MOSTRAR CAMPOS DEL TIPO
    # --------------------------------------------------------

    encontrados = 0

    total = len(
        campos_a_mostrar
    )

    for nombre in campos_a_mostrar:

        datos_campo = campos.get(
            nombre
        )

        if mostrar_campo(
            nombre,
            datos_campo
        ):

            encontrados += 1

    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------

    print()

    print("=" * 90)
    print("RESUMEN")
    print("=" * 90)

    print()

    print(
        f"Campos encontrados: "
        f"{encontrados}/{total}"
    )

    porcentaje = (
        encontrados
        / total
        * 100
    )

    print(
        f"Porcentaje: "
        f"{porcentaje:.2f}%"
    )

    print()

    print("=" * 90)
    print("FIN DE PRUEBA")
    print("=" * 90)

    print()


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    main()