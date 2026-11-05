from pathlib import Path
import json
import sys
import io

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from Services.extractores.banorte.banorte import BanorteExtractor


# ============================================================
# RUTAS
# ============================================================

CARPETA_JSON = (
    RAIZ_PROYECTO
    / "Resultados_OCR"
    / "BANORTE"
)


# ============================================================
# CLASIFICACIÓN PRIMARIOS (100%) VS SECUNDARIOS (>=90%)
# ============================================================

CONJUNTO_PRIMARIOS = {
    "banco",
    "fecha",
    "monto",
    "clave_rastreo",
    "referencia",
}

CONJUNTO_SECUNDARIOS = {
    "destinatario",
    "cuenta_destino",
    "banco_destino",
    "concepto",
}

CAMPOS_COMUNES_COMPLETOS = [
    "banco",
    "fecha",
    "monto",
    "destinatario",
    "cuenta_destino",
    "banco_destino",
    "clave_rastreo",
    "concepto",
    "referencia",
]

CAMPOS_SIN_DESTINATARIO = [
    "banco",
    "fecha",
    "monto",
    "cuenta_destino",
    "banco_destino",
    "clave_rastreo",
    "concepto",
    "referencia",
]

CAMPOS_ESPERADOS = {
    "image_020.json": CAMPOS_COMUNES_COMPLETOS,
    "image_035.json": CAMPOS_COMUNES_COMPLETOS,
    "image_064.json": CAMPOS_COMUNES_COMPLETOS,
    "image_074.json": CAMPOS_COMUNES_COMPLETOS,
    "image_086.json": CAMPOS_COMUNES_COMPLETOS,
    "image_087.json": [
        "banco",
        "fecha",
        "monto",
        "destinatario",
        "cuenta_destino",
        "banco_destino",
        "clave_rastreo",
        "concepto",
    ],
    "image_094.json": CAMPOS_COMUNES_COMPLETOS,
    "image_098.json": CAMPOS_COMUNES_COMPLETOS,
    "image_109.json": CAMPOS_COMUNES_COMPLETOS,
    "image_152.json": CAMPOS_COMUNES_COMPLETOS,
    "image_164.json": CAMPOS_SIN_DESTINATARIO,
    "image_167.json": CAMPOS_COMUNES_COMPLETOS,
    "image_183.json": CAMPOS_SIN_DESTINATARIO,
    "image_189.json": CAMPOS_COMUNES_COMPLETOS,
    "image_197.json": CAMPOS_COMUNES_COMPLETOS,
    "image_247.json": CAMPOS_COMUNES_COMPLETOS,
    "image_295.json": CAMPOS_SIN_DESTINATARIO,
    "image_300.json": CAMPOS_COMUNES_COMPLETOS,
    "image_343.json": CAMPOS_SIN_DESTINATARIO,
    "image_346.json": CAMPOS_COMUNES_COMPLETOS,
    "image_361.json": CAMPOS_COMUNES_COMPLETOS,
    "image_398.json": CAMPOS_SIN_DESTINATARIO,
    "image_408.json": [
        "banco",
        "fecha",
        "monto",
        "cuenta_destino",
        "banco_destino",
        "clave_rastreo",
        "referencia",
    ],
    "image_417.json": CAMPOS_COMUNES_COMPLETOS,
    "image_426.json": CAMPOS_SIN_DESTINATARIO,
    "image_429.json": CAMPOS_COMUNES_COMPLETOS,
    "image_438.json": CAMPOS_COMUNES_COMPLETOS,
    "image_484.json": CAMPOS_COMUNES_COMPLETOS,
    "image_487.json": CAMPOS_COMUNES_COMPLETOS,
    "image_492.json": CAMPOS_COMUNES_COMPLETOS,
    "image_508.json": CAMPOS_SIN_DESTINATARIO,
    "image_546.json": CAMPOS_COMUNES_COMPLETOS,
    "image_551.json": [
        "banco",
        "fecha",
        "monto",
        "destinatario",
        "cuenta_destino",
        "banco_destino",
        "clave_rastreo",
    ],
    "image_576.json": CAMPOS_COMUNES_COMPLETOS,
}


# ============================================================
# EJECUTAR PRUEBA MASIVA
# ============================================================

def ejecutar_prueba():
    print()
    print("=" * 100)
    print("PRUEBA FINAL MASIVA - BANORTE")
    print("=" * 100)
    print()

    if not CARPETA_JSON.exists():
        print("ERROR: No existe la carpeta de resultados OCR.")
        sys.exit(1)

    archivos_json = sorted(CARPETA_JSON.glob("*.json"))
    print(f"Comprobantes encontrados: {len(archivos_json)}")
    print()

    extractor = BanorteExtractor()
    completos = 0
    incompletos = 0
    primarios_ok_total = 0
    secundarios_ok_total = 0

    for indice, ruta_json in enumerate(archivos_json, start=1):
        with open(ruta_json, "r", encoding="utf-8") as f:
            datos = json.load(f)

        extraido = extractor.extraer(datos)
        campos = extraido.get("campos", {})

        esperados = CAMPOS_ESPERADOS.get(
            ruta_json.name,
            CAMPOS_COMUNES_COMPLETOS,
        )
        primarios_esp = [c for c in esperados if c in CONJUNTO_PRIMARIOS]
        secundarios_esp = [c for c in esperados if c in CONJUNTO_SECUNDARIOS]

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
        print(f"[{indice}/{len(archivos_json)}] {ruta_json.name} -> {estado}")
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
    print("RESUMEN FINAL - BANORTE")
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
    archivo_txt = carpeta_resultados / "resultado_masivo_banorte.txt"

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
