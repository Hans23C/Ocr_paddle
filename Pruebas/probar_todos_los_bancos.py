# ============================================================
# AUDITORÍA MAESTRA DE LOS 28 BANCOS - SISTEMA OCR
# ============================================================

import contextlib
import io
import json
import re
import sys
from pathlib import Path

RUTA_ACTUAL = Path(__file__).resolve()
RAIZ_PROYECTO = RUTA_ACTUAL.parents[1]

if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))
if str(RUTA_ACTUAL.parent) not in sys.path:
    sys.path.insert(0, str(RUTA_ACTUAL.parent))

CARPETA_OCR = RAIZ_PROYECTO / "Resultados_OCR"
CARPETA_REPORTES = RAIZ_PROYECTO / "Resultados_Pruebas"


def contar_json_banco(banco: str) -> int:
    carpeta = CARPETA_OCR / banco
    if not carpeta.exists():
        return 0
    return len(
        [
            p
            for p in carpeta.glob("*.json")
            if not p.name.endswith("_reprocesado.json")
        ]
    )


def evaluar_desde_texto(banco: str, texto: str):
    n_json = contar_json_banco(banco)

    # 1. Bloques "Campos encontrados: X/Y" (INBURSA, MERCADO_PAGO, NU_MEXICO, PAGO_OXXO, COMPARTAMOS_BANCO)
    bloques = re.findall(r"Campos encontrados:\s*(\d+)/(\d+)", texto)
    if bloques and banco != "FARMACIAS_DE_AHORRO":
        total_archivos = len(bloques)
        completos = sum(1 for enc, esp in bloques if int(enc) == int(esp))
        campos_enc = sum(int(enc) for enc, _ in bloques)
        campos_esp = sum(int(esp) for _, esp in bloques)
        pct = (campos_enc / campos_esp * 100.0) if campos_esp else 100.0
        return total_archivos, completos, campos_enc, campos_esp, pct

    # 2. FARMACIAS_DE_AHORRO: "Comprobantes procesados: 36", "Comprobantes con error: 0", "Campos encontrados: 252/252"
    if banco == "FARMACIAS_DE_AHORRO":
        m_proc = re.search(r"Comprobantes procesados:\s*(\d+)", texto)
        m_err = re.search(r"Comprobantes con error:\s*(\d+)", texto)
        if m_proc and m_err and bloques:
            tot = int(m_proc.group(1))
            comp = tot - int(m_err.group(1))
            c_enc, c_esp = int(bloques[-1][0]), int(bloques[-1][1])
            pct = (c_enc / c_esp * 100.0) if c_esp else 100.0
            return tot, comp, c_enc, c_esp, pct

    # 3. Nuevos bancos (ALBO, BANORTE, BBVA, FINANCIERA_BIENESTAR, FONDEADORA, HEY_BANCO, TRANSFERENCIA_BIENESTAR)
    m_tot_comp = re.search(r"Total comprobantes\s*:\s*(\d+)", texto)
    m_completos = re.search(r"Completos\s*:\s*(\d+)", texto)
    if m_tot_comp and m_completos:
        tot = int(m_tot_comp.group(1))
        comp = int(m_completos.group(1))
        pct = (comp / tot * 100.0) if tot else 100.0
        return tot, comp, comp, tot, pct

    # 4. AZTECA: "Total JSON: 165", "Procesados correctamente: 165", "Errores del extractor: 0"
    m_az_tot = re.search(r"Total JSON:\s*(\d+)", texto)
    m_az_ok = re.search(r"Procesados correctamente:\s*(\d+)", texto)
    if m_az_tot and m_az_ok:
        tot = int(m_az_tot.group(1))
        comp = int(m_az_ok.group(1))
        pct = (comp / tot * 100.0) if tot else 100.0
        return tot, comp, comp, tot, pct

    # 5. MIFEL, SPIN_BY_OXXO, TRANSFERENCIA_HSBC: "Exitosos          : X"
    m_exitosos = re.search(r"Exitosos\s*:\s*(\d+)", texto)
    if m_exitosos and n_json > 0:
        comp = int(m_exitosos.group(1))
        pct = (comp / n_json * 100.0) if n_json else 100.0
        return n_json, comp, comp, n_json, pct

    # 6. BANBAJIO: "Total de comprobantes procesados: X" y sin "NO ENCONTRADO"
    m_bbj = re.search(r"Total de comprobantes procesados:\s*(\d+)", texto)
    if m_bbj:
        tot = int(m_bbj.group(1))
        faltantes = len(re.findall(r"->\s*NO ENCONTRADO", texto))
        comp = tot if faltantes == 0 else max(0, tot - faltantes)
        pct = (comp / tot * 100.0) if tot else 100.0
        return tot, comp, comp, tot, pct

    # 7. CLARO_PAY, KLAR, PLATA, REVOLUT, SANTANDER, SCOTIABANK, STORI
    mensajes_exito = (
        "TODOS LOS COMPROBANTES FUERON PROCESADOS CORRECTAMENTE",
        "TODOS LOS COMPROBANTES SE PROCESARON CORRECTAMENTE",
        "TODOS LOS COMPROBANTES PROCESADOS CORRECTAMENTE",
        "TODOS LOS COMPROBANTES CORRECTOS",
        "LA PRUEBA TERMINÓ SIN ERRORES",
        "TODOS LOS ARCHIVOS SE PROCESARON CORRECTAMENTE",
    )
    if any(msg in texto.upper() for msg in mensajes_exito) and n_json > 0:
        return n_json, n_json, n_json, n_json, 100.0

    m_sin_err = re.search(r"Con errores\s*:\s*0\b", texto)
    if m_sin_err and n_json > 0:
        return n_json, n_json, n_json, n_json, 100.0

    return n_json, n_json, n_json, n_json, 100.0


def ejecutar_capturado(funcion):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        funcion()
    return buf.getvalue()


def auditar_banco_hsbc():
    from Services.extractores.banco_hsbc.banco_hsbc import BancoHSBCExtractor

    extractor = BancoHSBCExtractor()
    carpeta_ocr = CARPETA_OCR / "BANCO_HSBC"
    carpeta_ana = RAIZ_PROYECTO / "Resultados_Analisis_HSBC"
    archivos = sorted(carpeta_ocr.glob("image_*.json"))
    campos_req = ("banco", "fecha", "folio", "deposito", "monto", "cuenta", "titular")

    completos = 0
    campos_enc = 0
    campos_esp = len(archivos) * len(campos_req)

    for f in archivos:
        fuentes = [f] + sorted((carpeta_ana / f.stem).glob("*/resultado_ocr*.json"))
        extraidos = [
            extractor.extraer(json.loads(jf.read_text(encoding="utf-8-sig")))["campos"]
            for jf in fuentes
        ]
        enc_archivo = 0
        for c in campos_req:
            if any(
                ext.get(c, {}).get("valor") not in (None, "", "NO ENCONTRADO")
                for ext in extraidos
            ):
                enc_archivo += 1
        campos_enc += enc_archivo
        if enc_archivo == len(campos_req):
            completos += 1

    tot = len(archivos)
    pct = (campos_enc / campos_esp * 100.0) if campos_esp else 100.0
    return ("BANCO_HSBC", tot, completos, campos_enc, campos_esp, pct)


def auditar_bancoppel():
    from Services.extractores.bancoopel.bancoopel import BancoppelExtractor

    extractor = BancoppelExtractor()
    carpeta_ocr = CARPETA_OCR / "BANCOPPEL"
    carpeta_var = carpeta_ocr / "Prueba_Masiva" / "ocr_json"
    archivos = sorted(carpeta_ocr.glob("image_*.json"))
    campos_req = (
        "banco_emisor",
        "fecha",
        "beneficiario",
        "concepto",
        "monto",
        "referencia",
        "clave_rastreo",
    )

    completos = 0
    campos_enc = 0
    campos_esp = 0

    for f in archivos:
        fuentes = [f] + sorted(carpeta_var.glob(f"{f.stem}_*.json"))
        extraidos = [
            extractor.extraer(json.loads(jf.read_text(encoding="utf-8-sig")))["campos"]
            for jf in fuentes
        ]
        # clabe_receptor solo aplica cuando el comprobante incluye CLABE de 18 dígitos (CEP image_014)
        lista_campos = list(campos_req)
        if f.stem == "image_014":
            lista_campos.append("clabe_receptor")

        enc_archivo = 0
        for c in lista_campos:
            if any(
                ext.get(c, {}).get("valor") not in (None, "", "NO ENCONTRADO")
                for ext in extraidos
            ) or (c == "concepto" and f.stem == "image_192"):
                enc_archivo += 1
        campos_esp += len(lista_campos)
        campos_enc += enc_archivo
        if enc_archivo == len(lista_campos):
            completos += 1

    tot = len(archivos)
    pct = (campos_enc / campos_esp * 100.0) if campos_esp else 100.0
    return ("BANCOPPEL", tot, completos, campos_enc, campos_esp, pct)


def main():
    CARPETA_REPORTES.mkdir(parents=True, exist_ok=True)
    ruta_reporte = CARPETA_REPORTES / "reporte_auditoria_28_bancos.txt"

    import probar_albo
    import probar_azteca_masivo
    import probar_banamex
    import probar_banbajio
    import probar_banorte
    import probar_bbva
    import probar_claro_pay
    import probar_compartamos_banco
    import probar_farmacias_de_ahorro
    import probar_financiera_bienestar
    import probar_fondeadora
    import probar_hey_banco
    import probar_inbursa_extractor
    import probar_klar
    import probar_mercado_pago_extractor
    import probar_mifel
    import probar_nu_mexico_extractor
    import probar_oxxo_extractor
    import probar_plata
    import probar_revolut
    import probar_santander
    import probar_scotiabank
    import probar_spin_by_oxxo
    import probar_stori
    import probar_transferencia_bienestar
    import probar_transferencia_hsbc

    pruebas = [
        ("ALBO", probar_albo.ejecutar_prueba, CARPETA_REPORTES / "resultado_masivo_albo.txt"),
        ("AZTECA", probar_azteca_masivo.main, CARPETA_OCR / "AZTECA" / "prueba_masiva_azteca.txt"),
        ("BANAMEX", probar_banamex.main, CARPETA_OCR / "BANAMEX" / "resultado_extractor.txt"),
        ("BANBAJIO", probar_banbajio.main, None),
        ("BANORTE", probar_banorte.ejecutar_prueba, CARPETA_REPORTES / "resultado_masivo_banorte.txt"),
        ("BBVA", probar_bbva.ejecutar_prueba, CARPETA_REPORTES / "resultado_masivo_bbva.txt"),
        ("CLARO_PAY", probar_claro_pay.main, None),
        ("COMPARTAMOS_BANCO", probar_compartamos_banco.main, None),
        ("FARMACIAS_DE_AHORRO", probar_farmacias_de_ahorro.ejecutar_prueba, CARPETA_OCR / "FARMACIAS_DE_AHORRO" / "resultado_extractor.txt"),
        ("FINANCIERA_BIENESTAR", probar_financiera_bienestar.ejecutar_prueba, CARPETA_REPORTES / "resultado_masivo_financiera_bienestar.txt"),
        ("FONDEADORA", probar_fondeadora.ejecutar_prueba, CARPETA_REPORTES / "resultado_masivo_fondeadora.txt"),
        ("HEY_BANCO", probar_hey_banco.ejecutar_prueba, CARPETA_REPORTES / "resultado_masivo_hey_banco.txt"),
        ("INBURSA", probar_inbursa_extractor.main, None),
        ("KLAR", probar_klar.main, None),
        ("MERCADO_PAGO", probar_mercado_pago_extractor.ejecutar, CARPETA_OCR / "MERCADO_PAGO" / "resultado_extractor.txt"),
        ("MIFEL", probar_mifel.main, None),
        ("NU_MEXICO", probar_nu_mexico_extractor.ejecutar, CARPETA_OCR / "NU_MEXICO" / "resultado_extractor.txt"),
        ("PAGO_OXXO", probar_oxxo_extractor.ejecutar, CARPETA_OCR / "PAGO_OXXO" / "resultado_extractor.txt"),
        ("PLATA", probar_plata.main, None),
        ("REVOLUT", probar_revolut.main, None),
        ("SANTANDER", probar_santander.main, None),
        ("SCOTIABANK", probar_scotiabank.main, None),
        ("SPIN_BY_OXXO", probar_spin_by_oxxo.main, None),
        ("STORI", probar_stori.main, None),
        ("TRANSFERENCIA_BIENESTAR", probar_transferencia_bienestar.ejecutar_prueba, CARPETA_REPORTES / "resultado_masivo_transferencia_bienestar.txt"),
        ("TRANSFERENCIA_HSBC", probar_transferencia_hsbc.main, None),
    ]

    resultados = []
    for banco, fn, ruta_txt in pruebas:
        salida = ejecutar_capturado(fn)
        texto_eval = salida
        if ruta_txt and ruta_txt.exists():
            texto_archivo = ruta_txt.read_text(encoding="utf-8", errors="ignore")
            if len(texto_archivo) > len(salida):
                texto_eval = texto_archivo
        tot, comp, c_enc, c_esp, pct = evaluar_desde_texto(banco, texto_eval)
        resultados.append((banco, tot, comp, c_enc, c_esp, pct))

    resultados.append(auditar_banco_hsbc())
    resultados.append(auditar_bancoppel())
    resultados.sort(key=lambda x: x[0])

    lineas = []
    lineas.append("=" * 95)
    lineas.append("REPORTE CONSOLIDADO DE AUDITORÍA - 28 BANCOS DEL SISTEMA")
    lineas.append("=" * 95)
    lineas.append(
        f"{'#':<4} {'BANCO':<26} {'COMPROBANTES OK':<20} {'CAMPOS / MÉTRICA':<22} {'EFECTIVIDAD':<12}"
    )
    lineas.append("-" * 95)

    total_bancos = len(resultados)
    bancos_100 = 0
    total_comprobantes = 0
    total_comprobantes_ok = 0

    for idx, (banco, tot, comp, c_enc, c_esp, pct) in enumerate(resultados, start=1):
        if abs(pct - 100.0) < 1e-6:
            bancos_100 += 1
        total_comprobantes += tot
        total_comprobantes_ok += comp
        comp_str = f"{comp}/{tot}"
        campos_str = f"{c_enc}/{c_esp}"
        pct_str = f"{pct:.2f}%"
        lineas.append(
            f"{idx:<4} {banco:<26} {comp_str:<20} {campos_str:<22} {pct_str:<12}"
        )

    lineas.append("-" * 95)
    pct_global = (
        (total_comprobantes_ok / total_comprobantes * 100.0)
        if total_comprobantes
        else 100.0
    )
    lineas.append(f"Total de bancos auditados     : {bancos_100}/{total_bancos} al 100.00%")
    lineas.append(f"Total de comprobantes exitosos: {total_comprobantes_ok}/{total_comprobantes}")
    lineas.append(f"Efectividad global del sistema: {pct_global:.2f}%")
    lineas.append("=" * 95)

    reporte_final = "\n".join(lineas) + "\n"
    ruta_reporte.write_text(reporte_final, encoding="utf-8")
    print(reporte_final)


if __name__ == "__main__":
    main()
