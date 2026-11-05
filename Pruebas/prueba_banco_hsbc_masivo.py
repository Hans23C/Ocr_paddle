from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import shutil
import sys
from pathlib import Path

EXTENSIONES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
VARIANTES = ("original", "escalada_2x", "brillo_contraste", "contraste_clahe", "nitidez_suave", "reduccion_ruido_clahe", "umbral_adaptativo")
CAMPOS = ("banco", "fecha", "folio", "deposito", "monto", "cuenta", "titular")


def cargar_modulo(nombre, ruta):
    if not ruta.is_file():
        raise FileNotFoundError(f"No se encontró el archivo: {ruta}")
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar: {ruta}")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def encontrar_json_anterior(raiz, nombre, variante):
    carpetas = [
        raiz / "Pruebas_HSBC_Reprocesamiento" / nombre / "json" / variante,
        raiz / "Pruebas_HSBC_Reprocesamiento" / nombre / nombre / "json" / variante,
    ]
    for carpeta in carpetas:
        if carpeta.is_dir():
            preferido = carpeta / f"{nombre}.json"
            if preferido.is_file():
                return preferido
            encontrados = sorted(carpeta.glob("*.json"))
            if len(encontrados) == 1:
                return encontrados[0]
    return None


def leer_json(ruta):
    with ruta.open("r", encoding="utf-8-sig") as archivo:
        datos = json.load(archivo)
    if not isinstance(datos, dict) or not isinstance(datos.get("detecciones", []), list):
        raise ValueError("El JSON no tiene la estructura esperada (objeto con lista 'detecciones').")
    return datos


def escribir_csv(ruta, filas):
    columnas = [
        "comprobante", "variante", "estado_proceso", "json",
        "total_detecciones", "total_etiquetas",
        *CAMPOS,
        *(f"estado_{c}" for c in CAMPOS),
        *(f"confianza_{c}" for c in CAMPOS),
        "error",
    ]
    with ruta.open("w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(filas)


def main():
    parser = argparse.ArgumentParser(
        description="Ejecuta las cuatro variantes OCR y el extractor híbrido existente para HSBC."
    )
    parser.add_argument("--entrada", type=Path, help="Carpeta de imágenes HSBC.")
    parser.add_argument("--salida", type=Path, help="Carpeta de resultados.")
    parser.add_argument(
        "--regenerar-json", action="store_true",
        help="Ignora JSON existentes y vuelve a ejecutar OCR para las cuatro variantes."
    )
    parser.add_argument(
        "--solo-json-existentes", action="store_true",
        help="No ejecuta OCR; procesa JSON existentes y registra los que falten."
    )
    args = parser.parse_args()

    raiz = Path(__file__).resolve().parent.parent
    if str(raiz) not in sys.path:
        sys.path.insert(0, str(raiz))

    entrada = (args.entrada or raiz / "Comprobantes" / "BANCO_HSBC").expanduser().resolve()
    salida = (args.salida or raiz / "Resultados_Analisis_HSBC").expanduser().resolve()
    ruta_extractor = Path(__file__).resolve().parent / "probar_hibrido_banco_hsbc.py"

    if not entrada.is_dir():
        raise SystemExit(f"ERROR: no existe la carpeta de entrada:\n{entrada}")

    imagenes = sorted(
        (p for p in entrada.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSIONES),
        key=lambda p: (p.stem.lower(), str(p).lower()),
    )
    if not imagenes:
        raise SystemExit(f"ERROR: no se encontraron imágenes en:\n{entrada}")

    extractor = cargar_modulo("extractor_hibrido_hsbc_masivo", ruta_extractor)
    from Services.extractores.banco_hsbc.preprocesamiento import generar_variantes
    from Services.extractores.banco_hsbc.reprocesar_hsbc import guardar_resultado_json
    from Services.ocr.paddle_ocr import PaddleOCRServicio

    salida.mkdir(parents=True, exist_ok=True)
    carpeta_variantes = salida / "_variantes_generadas"
    consolidado = salida / "ANALISIS_COMPLETO_HSBC.txt"
    csv_salida = salida / "RESUMEN_COMPARATIVO_HSBC.csv"
    errores_salida = salida / "ERRORES_PROCESAMIENTO.txt"
    filas, errores = [], []
    reutilizados = generados = 0
    servicio = None

    consolidado.write_text(
        "ANÁLISIS MASIVO HSBC - OCR Y EXTRACTOR HÍBRIDO\n"
        + "=" * 100 + "\n"
        + f"Entrada: {entrada}\nComprobantes encontrados: {len(imagenes)}\n"
        + f"Variantes: {', '.join(VARIANTES)}\nPrincipio: EXTRAER, NO INVENTAR.\n"
        + "=" * 100 + "\n",
        encoding="utf-8",
    )

    print("=" * 80)
    print("PRUEBA MASIVA HSBC")
    print(f"Imágenes encontradas: {len(imagenes)}")
    print(f"Entrada: {entrada}")
    print(f"Salida: {salida}")
    print("=" * 80)

    for numero, imagen in enumerate(imagenes, 1):
        nombre = imagen.stem
        carpeta_comp = salida / nombre
        carpeta_comp.mkdir(parents=True, exist_ok=True)
        print(f"\n[{numero}/{len(imagenes)}] {imagen.name}")

        rutas_json, fuentes = {}, {}
        necesita_ocr = False
        for variante in VARIANTES:
            destino = carpeta_comp / variante / "resultado_ocr.json"
            anterior = encontrar_json_anterior(raiz, nombre, variante)
            if not args.regenerar_json and destino.is_file():
                fuentes[variante] = "salida"
            elif not args.regenerar_json and anterior:
                fuentes[variante] = anterior
            else:
                fuentes[variante] = None
                necesita_ocr = True
            rutas_json[variante] = destino

        if args.solo_json_existentes:
            necesita_ocr = False

        variantes_generadas = None
        if necesita_ocr:
            try:
                variantes_generadas = generar_variantes(imagen, carpeta_variantes / nombre)
            except Exception as exc:
                errores.append(f"{imagen.name}: error generando variantes: {type(exc).__name__}: {exc}")
                print(f"  ERROR generando variantes: {exc}")

            if variantes_generadas and servicio is None:
                try:
                    print("  Inicializando PaddleOCRServicio...")
                    servicio = PaddleOCRServicio(idioma="es")
                except Exception as exc:
                    errores.append(f"Inicialización de PaddleOCR: {type(exc).__name__}: {exc}")
                    print(f"  ERROR inicializando PaddleOCR: {exc}")

        for variante in VARIANTES:
            destino_json = rutas_json[variante]
            carpeta_var = destino_json.parent
            carpeta_var.mkdir(parents=True, exist_ok=True)
            try:
                fuente = fuentes[variante]
                if fuente == "salida":
                    datos = leer_json(destino_json)
                    reutilizados += 1
                elif fuente is not None:
                    shutil.copy2(fuente, destino_json)
                    datos = leer_json(destino_json)
                    reutilizados += 1
                else:
                    if args.solo_json_existentes:
                        raise FileNotFoundError("No existe JSON y se indicó --solo-json-existentes.")
                    if variantes_generadas is None:
                        raise RuntimeError("No se pudieron generar las imágenes variantes.")
                    if servicio is None:
                        raise RuntimeError("PaddleOCRServicio no está disponible.")
                    resultado_ocr = servicio.procesar_imagen(str(variantes_generadas[variante]))
                    guardar_resultado_json(
                        resultado=resultado_ocr,
                        ruta_json=destino_json,
                        nombre_imagen=imagen.name,
                        variante=variante,
                    )
                    datos = leer_json(destino_json)
                    generados += 1

                resultado = extractor.extraer(datos)
                resultado["archivo"] = imagen.name
                ruta_txt = carpeta_var / "resultado.txt"
                extractor.escribir_txt([resultado], ruta_txt, 1)
                texto_txt = (
                    f"COMPROBANTE: {imagen.name}\nVARIANTE OCR: {variante}\nJSON: {destino_json}\n\n"
                    + ruta_txt.read_text(encoding="utf-8")
                )
                ruta_txt.write_text(texto_txt, encoding="utf-8")

                campos = resultado.get("campos", {})
                fila = {
                    "comprobante": imagen.name,
                    "variante": variante,
                    "estado_proceso": "OK",
                    "json": str(destino_json),
                    "total_detecciones": resultado.get("total_detecciones", 0),
                    "total_etiquetas": resultado.get("total_etiquetas", 0),
                    "error": "",
                }
                for campo in CAMPOS:
                    info = campos.get(campo, {})
                    fila[campo] = info.get("valor", "")
                    fila[f"estado_{campo}"] = info.get("estado", "")
                    fila[f"confianza_{campo}"] = info.get("confianza", 0.0)
                filas.append(fila)

                with consolidado.open("a", encoding="utf-8") as archivo:
                    archivo.write("\n" + "#" * 100 + "\n")
                    archivo.write(f"COMPROBANTE: {imagen.name}\nVARIANTE: {variante}\n")
                    archivo.write("#" * 100 + "\n" + texto_txt + "\n")

                print(f"  {variante}: OK | detecciones={resultado.get('total_detecciones', 0)}")

            except Exception as exc:
                mensaje = f"{imagen.name} [{variante}]: {type(exc).__name__}: {exc}"
                errores.append(mensaje)
                print(f"  {variante}: ERROR: {type(exc).__name__}: {exc}")
                fila = {
                    "comprobante": imagen.name, "variante": variante,
                    "estado_proceso": "ERROR", "json": str(destino_json),
                    "error": f"{type(exc).__name__}: {exc}",
                }
                for campo in CAMPOS:
                    fila[campo] = ""
                    fila[f"estado_{campo}"] = ""
                    fila[f"confianza_{campo}"] = ""
                filas.append(fila)
                with consolidado.open("a", encoding="utf-8") as archivo:
                    archivo.write(
                        f"\n{'#' * 100}\nCOMPROBANTE: {imagen.name}\n"
                        f"VARIANTE: {variante}\nERROR: {type(exc).__name__}: {exc}\n"
                    )

    escribir_csv(csv_salida, filas)
    errores_salida.write_text(
        "ERRORES DEL PROCESAMIENTO MASIVO HSBC\n" + "=" * 90 + "\n"
        + ("\n".join(errores) + "\n" if errores else "No se registraron errores.\n"),
        encoding="utf-8",
    )

    esperados = len(imagenes) * len(VARIANTES)
    correctos = sum(f.get("estado_proceso") == "OK" for f in filas)
    with consolidado.open("a", encoding="utf-8") as archivo:
        archivo.write("\n" + "=" * 100 + "\nRESUMEN FINAL\n")
        archivo.write(f"Comprobantes encontrados: {len(imagenes)}\n")
        archivo.write(f"Resultados esperados: {esperados}\nResultados correctos: {correctos}\n")
        archivo.write(f"Resultados con error: {len(filas) - correctos}\n")
        archivo.write(f"JSON reutilizados: {reutilizados}\nJSON generados: {generados}\n")
        archivo.write(f"CSV: {csv_salida}\nErrores: {errores_salida}\n")

    print("\n" + "=" * 80)
    print("PROCESO TERMINADO")
    print(f"Resultados correctos: {correctos}/{esperados}")
    print(f"JSON reutilizados: {reutilizados} | JSON generados: {generados}")
    print(f"Análisis completo: {consolidado}")
    print(f"CSV comparativo: {csv_salida}")
    print(f"Errores: {errores_salida}")
    print("=" * 80)


if __name__ == "__main__":
    main()
