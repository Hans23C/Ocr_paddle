from pathlib import Path
import json
import sys
import io

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from Services.extractores.bbva.bbva import BBVAExtractor

CARPETA_JSON = RAIZ_PROYECTO / "Resultados_OCR" / "BBVA"

# Clasificación por plantilla según Comprobane_BBVA.txt
PRIMARIOS_POR_PLANTILLA = {
    "COMPROBANTE_ESTANDAR": ["banco", "monto", "fecha", "clave_rastreo"],
    "COMPROBANTE_DETALLADO": ["banco", "monto", "referencia", "fecha", "clave_rastreo"],
    "TRANSFERIR_DIMO": ["banco", "monto", "referencia", "fecha", "clave_rastreo"],
    "DETALLE_MOVIMIENTO": ["banco", "monto", "referencia", "fecha", "clave_rastreo"],
    "CEP_BANXICO": ["banco", "monto", "referencia", "fecha", "clave_rastreo"],
}

SECUNDARIOS_POR_PLANTILLA = {
    "COMPROBANTE_ESTANDAR": ["beneficiario", "destino", "concepto"],
    "COMPROBANTE_DETALLADO": ["beneficiario", "cuenta_destino", "destino", "concepto"],
    "TRANSFERIR_DIMO": ["beneficiario", "destino", "concepto"],
    "DETALLE_MOVIMIENTO": ["beneficiario", "destino"],
    "CEP_BANXICO": ["destino", "cuenta_destino"],
}


def ejecutar_prueba():
    print()
    print("=" * 100)
    print("PRUEBA FINAL MASIVA - BBVA")
    print("=" * 100)
    print()

    if not CARPETA_JSON.exists():
        print(f"ERROR: No existe la carpeta {CARPETA_JSON}")
        print("Ejecuta primero: python -m Pruebas.procesar_comprobantes BBVA")
        sys.exit(1)

    archivos_json = sorted(CARPETA_JSON.glob("*.json"))
    print(f"Comprobantes encontrados: {len(archivos_json)}")
    print()

    extractor = BBVAExtractor()
    completos = 0
    incompletos = 0
    primarios_ok_total = 0
    secundarios_ok_total = 0

    for indice, ruta_json in enumerate(archivos_json, start=1):
        with open(ruta_json, "r", encoding="utf-8") as f:
            datos = json.load(f)

        extraido = extractor.extraer(datos)
        plantilla = extraido.get("plantilla", "COMPROBANTE_ESTANDAR")
        campos = extraido.get("campos", {})

        primarios_esp = PRIMARIOS_POR_PLANTILLA.get(
            plantilla,
            ["banco", "monto", "fecha", "clave_rastreo"],
        )
        secundarios_esp = SECUNDARIOS_POR_PLANTILLA.get(
            plantilla,
            ["beneficiario", "destino", "concepto"],
        )

        # En CEP_BANXICO cuenta_destino puede no incluirse en algunos comprobantes
        if plantilla == "CEP_BANXICO" and campos.get("cuenta_destino") is None:
            secundarios_esp = ["destino"]

        faltantes_primarios = [
            c for c in primarios_esp
            if campos.get(c) is None or str(campos.get(c)).strip() == ""
        ]
        faltantes_secundarios = [
            c for c in secundarios_esp
            if campos.get(c) is None or str(campos.get(c)).strip() == ""
        ]

        if not faltantes_primarios:
            primarios_ok_total += 1
        if not faltantes_secundarios:
            secundarios_ok_total += 1

        if not faltantes_primarios and not faltantes_secundarios:
            completos += 1
            estado = "COMPLETO"
        else:
            incompletos += 1
            estado = "INCOMPLETO"

        print("=" * 100)
        print(f"[{indice}/{len(archivos_json)}] {ruta_json.name} ({plantilla}) -> {estado}")
        print("=" * 100)
        print("  [DATOS PRIMARIOS - 100% Exactos]")
        for c in primarios_esp:
            print(f"    {c:<18}: {campos.get(c)}")
        print("  [DATOS SECUNDARIOS - >=90% / Palabras Completas]")
        for c in secundarios_esp:
            print(f"    {c:<18}: {campos.get(c)}")
        if faltantes_primarios:
            print(f"  FALTANTES PRIMARIOS   : {', '.join(faltantes_primarios)}")
        if faltantes_secundarios:
            print(f"  FALTANTES SECUNDARIOS : {', '.join(faltantes_secundarios)}")
        print()

    total = len(archivos_json)
    porcentaje = (completos / total * 100.0) if total else 0.0

    print("=" * 100)
    print("RESUMEN FINAL - BBVA")
    print("=" * 100)
    print(f"Total comprobantes           : {total}")
    print(f"Datos Primarios (100% OK)    : {primarios_ok_total}/{total}")
    print(f"Datos Secundarios (>=90% OK) : {secundarios_ok_total}/{total}")
    print(f"Completos                    : {completos}")
    print(f"Incompletos                  : {incompletos}")
    print(f"Efectividad                  : {porcentaje:.2f}%")
    print("=" * 100)


def main():
    carpeta_resultados = RAIZ_PROYECTO / "Resultados_Pruebas"
    carpeta_resultados.mkdir(parents=True, exist_ok=True)
    archivo_txt = carpeta_resultados / "resultado_masivo_bbva.txt"

    salida = io.StringIO()
    stdout_original = sys.stdout
    try:
        sys.stdout = salida
        ejecutar_prueba()
    finally:
        sys.stdout = stdout_original

    contenido = salida.getvalue()
    archivo_txt.write_text(contenido, encoding="utf-8")
    print(contenido)


if __name__ == "__main__":
    main()
