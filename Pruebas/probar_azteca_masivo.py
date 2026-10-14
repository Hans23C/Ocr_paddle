import csv
import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Raíz del proyecto: carpeta padre de Pruebas
RAIZ_PROYECTO = Path(__file__).resolve().parents[1]

if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

# Ajusta esta importación únicamente si tu archivo está
# ubicado en otro paquete.
from Services.extractores.azteca import AztecaExtractor


# ------------------------------------------------------------
# CONFIGURACIÓN
# ------------------------------------------------------------

CARPETA_JSON = RAIZ_PROYECTO / "Resultados_OCR" / "AZTECA"

CARPETA_SALIDA = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "AZTECA"
    / "Pruebas_Azteca_Nuevo"
)

CAMPOS = [
    "banco",
    "fecha",
    "monto",
    "cuenta_origen",
    "cuenta_destino",
    "concepto",
    "referencia",
    "folio",
    "clave_rastreo",
]

CAMPOS_OBLIGATORIOS = [
    "banco",
    "fecha",
    "monto",
    "cuenta_origen",
    "cuenta_destino",
    "concepto",
    "referencia",
    "clave_rastreo",
]


def obtener_nombre_comprobante(datos, archivo_json):
    """Obtiene el nombre de imagen guardado en el JSON."""
    if isinstance(datos, dict):
        for llave in ("archivo", "imagen", "nombre_archivo", "ruta"):
            valor = datos.get(llave)
            if isinstance(valor, str) and valor.strip():
                return Path(valor).name

    return archivo_json.stem


def valor_texto(valor):
    """Convierte valores a texto sin inventar información."""
    if valor is None:
        return ""

    if isinstance(valor, (dict, list)):
        return json.dumps(valor, ensure_ascii=False)

    return str(valor).strip()


def main():
    inicio_total = time.perf_counter()

    if not CARPETA_JSON.is_dir():
        print(f"ERROR: No existe la carpeta de JSON:")
        print(CARPETA_JSON)
        return

    archivos_json = sorted(CARPETA_JSON.rglob("*.json"))

    # Evita procesar reportes de ejecuciones anteriores.
    archivos_json = [
        archivo for archivo in archivos_json
        if CARPETA_SALIDA not in archivo.parents
    ]

    if not archivos_json:
        print("No se encontraron archivos JSON para AZTECA.")
        print(f"Ruta revisada: {CARPETA_JSON}")
        return

    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)

    extractor = AztecaExtractor()
    resultados = []

    total = len(archivos_json)

    print("=" * 70)
    print("PRUEBA MASIVA - NUEVO EXTRACTOR AZTECA")
    print("=" * 70)
    print(f"JSON encontrados: {total}")
    print(f"Entrada: {CARPETA_JSON}")
    print(f"Salida:  {CARPETA_SALIDA}")
    print()

    for indice, archivo_json in enumerate(archivos_json, start=1):
        inicio = time.perf_counter()

        fila = {
            "json": str(archivo_json.relative_to(CARPETA_JSON)),
            "comprobante": archivo_json.stem,
            "estado": "OK",
            "error": "",
            "tiempo_segundos": 0,
        }

        for campo in CAMPOS:
            fila[campo] = ""

        try:
            with archivo_json.open("r", encoding="utf-8") as archivo:
                datos = json.load(archivo)

            if not isinstance(datos, (dict, list)):
                raise ValueError(
                    "El JSON no contiene un objeto ni una lista."
                )

            fila["comprobante"] = obtener_nombre_comprobante(
                datos, archivo_json
            )

            resultado = extractor.extraer(datos)

            if not isinstance(resultado, dict):
                raise ValueError(
                    "El extractor no devolvió un diccionario."
                )

            campos_extraidos = resultado.get("campos", {})

            if not isinstance(campos_extraidos, dict):
                raise ValueError(
                    "La estructura resultado['campos'] no es válida."
                )

            fila["banco"] = valor_texto(
                resultado.get("banco", "")
            )

            for campo in CAMPOS:
                if campo == "banco":
                    continue

                fila[campo] = valor_texto(
                    campos_extraidos.get(campo, "")
                )

            # Registrar campos vacíos para revisión.
            faltantes = [
                campo
                for campo in CAMPOS_OBLIGATORIOS
                if not fila.get(campo, "").strip()
            ]

            fila["campos_faltantes"] = ", ".join(faltantes)

            if faltantes:
                fila["estado"] = "REVISAR"

        except Exception as error:
            fila["estado"] = "ERROR"
            fila["error"] = f"{type(error).__name__}: {error}"
            fila["campos_faltantes"] = ", ".join(CAMPOS_OBLIGATORIOS)

        fila["tiempo_segundos"] = round(
            time.perf_counter() - inicio, 3
        )

        resultados.append(fila)

        print(
            f"[{indice}/{total}] "
            f"{fila['comprobante']} | "
            f"{fila['estado']} | "
            f"{fila['tiempo_segundos']} s"
        )

        if fila["estado"] == "ERROR":
            print(f"    Error: {fila['error']}")
        elif fila["estado"] == "REVISAR":
            print(f"    Faltantes: {fila['campos_faltantes']}")

    # --------------------------------------------------------
    # GUARDAR RESULTADOS
    # --------------------------------------------------------

    fecha_ejecucion = datetime.now().strftime("%Y%m%d_%H%M%S")

    archivo_csv = (
        CARPETA_SALIDA
        / f"reporte_azteca_{fecha_ejecucion}.csv"
    )

    archivo_json = (
        CARPETA_SALIDA
        / f"reporte_azteca_{fecha_ejecucion}.json"
    )

    columnas = [
        "json",
        "comprobante",
        "estado",
        "banco",
        "fecha",
        "monto",
        "cuenta_origen",
        "cuenta_destino",
        "concepto",
        "referencia",
        "folio",
        "clave_rastreo",
        "campos_faltantes",
        "tiempo_segundos",
        "error",
    ]

    with archivo_csv.open(
        "w", newline="", encoding="utf-8-sig"
    ) as archivo:
        escritor = csv.DictWriter(
            archivo, fieldnames=columnas, extrasaction="ignore"
        )
        escritor.writeheader()
        escritor.writerows(resultados)

    with archivo_json.open("w", encoding="utf-8") as archivo:
        json.dump(
            resultados,
            archivo,
            ensure_ascii=False,
            indent=2,
        )

    # --------------------------------------------------------
    # RESUMEN ESTADÍSTICO
    # --------------------------------------------------------

    exitosos = sum(r["estado"] == "OK" for r in resultados)
    revisar = sum(r["estado"] == "REVISAR" for r in resultados)
    errores = sum(r["estado"] == "ERROR" for r in resultados)

    print()
    print("=" * 70)
    print("RESUMEN DE LA PRUEBA")
    print("=" * 70)
    print(f"Total procesados: {len(resultados)}")
    print(f"Sin campos obligatorios vacíos: {exitosos}")
    print(f"Con campos para revisar:         {revisar}")
    print(f"Con errores de ejecución:        {errores}")

    print()
    print("COMPLETITUD POR CAMPO")

    for campo in CAMPOS:
        presentes = sum(
            bool(r.get(campo, "").strip())
            for r in resultados
        )
        porcentaje = (
            presentes / len(resultados) * 100
            if resultados else 0
        )

        print(
            f"{campo:18} "
            f"{presentes:4}/{len(resultados):<4} "
            f"({porcentaje:.2f} %)"
        )

    tiempo_total = time.perf_counter() - inicio_total

    print()
    print(f"Tiempo total: {tiempo_total:.2f} segundos")
    print(f"CSV:  {archivo_csv}")
    print(f"JSON: {archivo_json}")
    print("=" * 70)


if __name__ == "__main__":
    main()
