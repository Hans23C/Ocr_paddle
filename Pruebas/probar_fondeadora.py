from pathlib import Path
import json
import sys
import io

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from Services.extractores.fondeadora.fondeadora import FondeadoraExtractor

CARPETA_JSON = RAIZ_PROYECTO / "Resultados_OCR" / "FONDEADORA"

# Según Comprobane_Fondeadora.txt
CAMPOS_PRIMARIOS = [
    "banco",
    "monto",
    "fecha",
    "clave_rastreo",
]

CAMPOS_SECUNDARIOS = [
    "transferencia_para",
    "banco_receptor",
    "estatus",
    "concepto",
]


def _validar_secundario_completo(valor):
    if valor is None:
        return False
    txt = str(valor).strip()
    if not txt or txt.endswith("..."):
        return False
    return True


def ejecutar_prueba():
    print()
    print("=" * 100)
    print("PRUEBA FINAL MASIVA - FONDEADORA")
    print("=" * 100)
    print()

    archivos_json = sorted(CARPETA_JSON.glob("*.json"))
    print(f"Comprobantes encontrados: {len(archivos_json)}")
    print()

    extractor = FondeadoraExtractor()
    completos = 0
    incompletos = 0
    primarios_ok_total = 0
    secundarios_ok_total = 0

    for indice, ruta_json in enumerate(archivos_json, start=1):
        with open(ruta_json, "r", encoding="utf-8") as f:
            datos = json.load(f)

        extraido = extractor.extraer(datos)
        campos = extraido.get("campos", {})

        faltantes_primarios = [
            c for c in CAMPOS_PRIMARIOS
            if campos.get(c) is None or str(campos.get(c)).strip() == ""
        ]
        faltantes_secundarios = [
            c for c in CAMPOS_SECUNDARIOS
            if not _validar_secundario_completo(campos.get(c))
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
        print(f"[{indice}/{len(archivos_json)}] {ruta_json.name} -> {estado}")
        print("=" * 100)
        print("  [DATOS PRIMARIOS - 100% Exactos]")
        for c in CAMPOS_PRIMARIOS:
            print(f"    {c:<20}: {campos.get(c)}")
        print("  [DATOS SECUNDARIOS - >=90% / Palabras Completas]")
        for c in CAMPOS_SECUNDARIOS:
            print(f"    {c:<20}: {campos.get(c)}")
        if faltantes_primarios:
            print(f"  FALTANTES PRIMARIOS   : {', '.join(faltantes_primarios)}")
        if faltantes_secundarios:
            print(f"  FALTANTES SECUNDARIOS : {', '.join(faltantes_secundarios)}")
        print()

    total = len(archivos_json)
    porcentaje = (completos / total * 100.0) if total else 0.0

    print("=" * 100)
    print("RESUMEN FINAL - FONDEADORA")
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
    archivo_txt = carpeta_resultados / "resultado_masivo_fondeadora.txt"

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
