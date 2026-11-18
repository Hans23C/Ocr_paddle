import json
import os
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
if str(RAIZ / "Pruebas") not in sys.path:
    sys.path.insert(0, str(RAIZ / "Pruebas"))

from Services.clasificador_bancos import ClasificadorBancos

# Importación de los 28 extractores
from Services.extractores.albo.albo import AlboExtractor
import Services.extractores.azteca.azteca as _az_mod
_az_mod._obtener_ocr_recuperacion = lambda: None
from Services.extractores.azteca.azteca import AztecaExtractor
from Services.extractores.banamex.banamex import BanamexExtractor
from Services.extractores.banbajio.banbajio import BanBajioExtractor
from Services.extractores.banco_hsbc.banco_hsbc import BancoHSBCExtractor
from Services.extractores.bancoopel.bancoopel import BancoppelExtractor
from Services.extractores.banorte.banorte import BanorteExtractor
from Services.extractores.bbva.bbva import BBVAExtractor
from Services.extractores.claro_pay.claro_pay import ClaroPayExtractor
from Services.extractores.compartamos_banco.compartamos_banco import CompartamosBancoExtractor
from Services.extractores.farmacias_de_ahorro.farmacias_de_ahorro import FarmaciasDeAhorroExtractor
from Services.extractores.financiera_bienestar.financiera_bienestar import FinancieraBienestarExtractor
from Services.extractores.fondeadora.fondeadora import FondeadoraExtractor
from Services.extractores.hey_banco.hey_banco import HeyBancoExtractor
from Services.extractores.inbursa.inbursa import extraer as extraer_inbursa
from Services.extractores.klar.klar import KlarExtractor
from Services.extractores.mercado_pago.mercado_pago import extraer as extraer_mercado_pago
from Services.extractores.mifel.mifel import MifelExtractor
from Services.extractores.nu_mexico.nu_mexico import extraer as extraer_nu_mexico
from Services.extractores.oxxo.oxxo import extraer as extraer_oxxo
from Services.extractores.plata.plata import PlataExtractor
from Services.extractores.revolut.revolut import RevolutExtractor
from Services.extractores.santander.santander import SantanderExtractor
from Services.extractores.scotiabank.scotiabank import ScotiabankExtractor
from Services.extractores.spin_by_oxxo.spin_by_oxxo import SpinByOxxoExtractor
from Services.extractores.stori.stori import StoriExtractor
from Services.extractores.transferencia_bienestar.transferencia_bienestar import TransferenciaBienestarExtractor
from Services.extractores.transferencia_hsbc.transferencia_hsbc import TransferenciaHSBCExtractor

import probar_hibrido_banco_hsbc as hsbc_hib
import probar_mifel


# Lista de Bancos 
BANCOS_SOPORTADOS = [
    {"id": "ALBO", "nombre": "Albo"},
    {"id": "AZTECA", "nombre": "Banco Azteca"},
    {"id": "BANAMEX", "nombre": "Citibanamex"},
    {"id": "BANBAJIO", "nombre": "BanBajío"},
    {"id": "BANCOPPEL", "nombre": "Bancoppel"},
    {"id": "BANCO_HSBC", "nombre": "Banco HSBC (Practicaja / Ventanilla)"},
    {"id": "BANORTE", "nombre": "Banorte"},
    {"id": "BBVA", "nombre": "BBVA México"},
    {"id": "CLARO_PAY", "nombre": "Claro Pay"},
    {"id": "COMPARTAMOS_BANCO", "nombre": "Compartamos Banco"},
    {"id": "FARMACIAS_DE_AHORRO", "nombre": "Farmacias del Ahorro"},
    {"id": "FINANCIERA_BIENESTAR", "nombre": "Financiera para el Bienestar (FINABIEN)"},
    {"id": "FONDEADORA", "nombre": "Fondeadora"},
    {"id": "HEY_BANCO", "nombre": "Hey Banco"},
    {"id": "INBURSA", "nombre": "Inbursa"},
    {"id": "KLAR", "nombre": "Klar"},
    {"id": "MERCADO_PAGO", "nombre": "Mercado Pago"},
    {"id": "MIFEL", "nombre": "Banca Mifel"},
    {"id": "NU_MEXICO", "nombre": "Nu México"},
    {"id": "PAGO_OXXO", "nombre": "Pago en OXXO"},
    {"id": "PLATA", "nombre": "Plata Card"},
    {"id": "REVOLUT", "nombre": "Revolut"},
    {"id": "SANTANDER", "nombre": "Santander SuperMóvil"},
    {"id": "SCOTIABANK", "nombre": "Scotiabank"},
    {"id": "SPIN_BY_OXXO", "nombre": "Spin by OXXO"},
    {"id": "STORI", "nombre": "Stori"},
    {"id": "TRANSFERENCIA_BIENESTAR", "nombre": "Transferencia Banco del Bienestar"},
    {"id": "TRANSFERENCIA_HSBC", "nombre": "Transferencia HSBC Digital"},
]


class GestorExtraccion:
    """Orquestador central para clasificar y extraer comprobantes."""

    def __init__(self):
        self.clasificador = ClasificadorBancos()
        self.instancias = {
            "ALBO": AlboExtractor(),
            "AZTECA": AztecaExtractor(),
            "BANAMEX": BanamexExtractor(),
            "BANBAJIO": BanBajioExtractor(),
            "BANCO_HSBC": BancoHSBCExtractor(),
            "BANCOPPEL": BancoppelExtractor(),
            "BANORTE": BanorteExtractor(),
            "BBVA": BBVAExtractor(),
            "CLARO_PAY": ClaroPayExtractor(),
            "COMPARTAMOS_BANCO": CompartamosBancoExtractor(),
            "FARMACIAS_DE_AHORRO": FarmaciasDeAhorroExtractor(),
            "FINANCIERA_BIENESTAR": FinancieraBienestarExtractor(),
            "FONDEADORA": FondeadoraExtractor(),
            "HEY_BANCO": HeyBancoExtractor(),
            "KLAR": KlarExtractor(),
            "MIFEL": MifelExtractor(),
            "PLATA": PlataExtractor(),
            "REVOLUT": RevolutExtractor(),
            "SANTANDER": SantanderExtractor(),
            "SCOTIABANK": ScotiabankExtractor(),
            "SPIN_BY_OXXO": SpinByOxxoExtractor(),
            "STORI": StoriExtractor(),
            "TRANSFERENCIA_BIENESTAR": TransferenciaBienestarExtractor(),
            "TRANSFERENCIA_HSBC": TransferenciaHSBCExtractor(),
        }
        self._ocr_servicio = None

    def obtener_ocr_servicio(self):
        """Inicializa bajo demanda el servicio PaddleOCR."""
        if self._ocr_servicio is None:
            from Services.ocr.paddle_ocr import PaddleOCRServicio
            self._ocr_servicio = PaddleOCRServicio(idioma="es")
        return self._ocr_servicio

    def procesar_imagen_a_detecciones(self, ruta_imagen: str) -> dict:
        """Aplica OCR sobre una imagen física y devuelve la estructura de detecciones."""
        ocr = self.obtener_ocr_servicio()
        resultado = ocr.procesar_imagen(ruta_imagen)
        detecciones_dict = []
        for d in resultado.detecciones:
            detecciones_dict.append({
                "texto": d.texto,
                "confianza": float(d.confianza),
                "x": float(d.x),
                "y": float(d.y),
                "ancho": float(d.ancho),
                "alto": float(d.alto),
                "bbox": d.bbox,
            })
        return {
            "archivo": os.path.basename(ruta_imagen),
            "ruta_imagen": ruta_imagen,
            "detecciones": detecciones_dict,
            "total_detecciones": len(detecciones_dict),
            "ancho_imagen": resultado.ancho_imagen,
            "alto_imagen": resultado.alto_imagen,
        }

    def _reprocesar_mercado_pago_si_necesario(self, datos_ocr: dict) -> dict:
        """
        Reprocesa únicamente la región 'Origen y destino' en comprobantes de
        Mercado Pago sin formato 'Transferencia enviada' cuando faltan datos
        del beneficiario o existen lecturas OCR de baja confianza.
        """
        ruta_imagen = datos_ocr.get("ruta_imagen")
        if not ruta_imagen or not os.path.isfile(ruta_imagen):
            return datos_ocr

        detecciones = datos_ocr.get("detecciones", [])
        if not isinstance(detecciones, list) or not detecciones:
            return datos_ocr

        textos = [str(d.get("texto", "")).lower() for d in detecciones if isinstance(d, dict)]
        unido = " ".join(textos)
        if "origen y destino" not in unido or "transferencia enviada" in unido:
            return datos_ocr

        y_origen = None
        y_fin = None
        for d in detecciones:
            if not isinstance(d, dict):
                continue
            t = str(d.get("texto", "")).lower()
            if y_origen is None and "origen y destino" in t:
                y_origen = float(d.get("y", 0.0))
            elif y_origen is not None and (
                "protegemos tu dinero" in t or "seguridad de mercado pago" in t
            ):
                y_fin = float(d.get("y", 0.0))
                break

        if y_origen is None:
            return datos_ocr

        cuentas_en_region = 0
        baja_confianza = False
        for d in detecciones:
            if not isinstance(d, dict):
                continue
            y_d = float(d.get("y", 0.0))
            if y_d <= y_origen:
                continue
            if y_fin is not None and y_d >= y_fin:
                continue
            t = str(d.get("texto", "")).lower()
            if "clabe" in t or "tarjeta" in t:
                cuentas_en_region += 1
            if float(d.get("confianza", 1.0)) < 0.92:
                baja_confianza = True

        if cuentas_en_region >= 2 and not baja_confianza:
            return datos_ocr

        import cv2

        imagen = cv2.imread(ruta_imagen, cv2.IMREAD_COLOR)
        if imagen is None:
            return datos_ocr

        altura, ancho = imagen.shape[:2]
        y_inicio_px = max(0, int(y_origen - 25))
        if y_fin is not None and y_fin > y_inicio_px + 50:
            y_fin_px = min(altura, int(y_fin - 15))
        else:
            y_fin_px = min(altura, int(min(altura * 0.85, y_origen + altura * 0.45)))

        if y_fin_px <= y_inicio_px:
            return datos_ocr

        ocr = self.obtener_ocr_servicio()
        nuevas = ocr._reprocesar_region_selectiva(
            ruta_imagen=ruta_imagen,
            ancho_imagen=datos_ocr.get("ancho_imagen") or ancho,
            alto_imagen=datos_ocr.get("alto_imagen") or altura,
            y_inicio_rel=y_inicio_px / float(altura),
            y_fin_rel=y_fin_px / float(altura),
            factor_escala=2.0,
            usar_clahe=False,
            sufijo="mp_origen_destino",
        )

        nuevas_en_rango = []
        for d in nuevas:
            texto_limpio = str(d.texto or "").strip()
            if len(texto_limpio) <= 1 and float(d.ancho) <= 35.0:
                continue
            cy = float(d.y) + float(d.alto) / 2.0
            if y_inicio_px <= cy <= y_fin_px:
                nuevas_en_rango.append({
                    "texto": d.texto,
                    "confianza": float(d.confianza),
                    "x": float(d.x),
                    "y": float(d.y),
                    "ancho": float(d.ancho),
                    "alto": float(d.alto),
                    "bbox": d.bbox,
                })

        if not nuevas_en_rango:
            return datos_ocr

        combinadas = []
        for d in detecciones:
            if not isinstance(d, dict):
                continue
            cy = float(d.get("y", 0.0)) + float(d.get("alto", 0.0)) / 2.0
            if cy < y_inicio_px or cy > y_fin_px:
                combinadas.append(d)

        combinadas.extend(nuevas_en_rango)
        combinadas.sort(key=lambda item: (float(item.get("y", 0.0)), float(item.get("x", 0.0))))

        actualizado = dict(datos_ocr)
        actualizado["detecciones"] = combinadas
        actualizado["total_detecciones"] = len(combinadas)
        return actualizado

    def procesar_comprobante(
        self,
        datos_ocr: dict,
        banco_solicitado: Optional[str] = None,
        modo: str = "AUTO",
    ) -> Dict[str, Any]:
        """
        Ejecuta la extracción de datos sobre detecciones OCR.
        - modo = "AUTO" -> Auto-detecta el banco con ClasificadorBancos.
        - modo = "MANUAL" -> Utiliza el banco seleccionado por el usuario.
        """
        info_clasificacion = None
        if not banco_solicitado or banco_solicitado.upper() in ("AUTO", "INTELIGENTE", ""):
            info_clasificacion = self.clasificador.clasificar(datos_ocr)
            banco_final = info_clasificacion["banco"]
            modo_aplicado = "INTELIGENTE"
        else:
            banco_final = banco_solicitado.upper()
            modo_aplicado = "MANUAL"

        if banco_final == "MERCADO_PAGO" and isinstance(datos_ocr, dict) and datos_ocr.get("ruta_imagen"):
            datos_ocr = self._reprocesar_mercado_pago_si_necesario(datos_ocr)

        # Extraer usando de caurdo al Banco seleccionado 
        campos_extraidos = self._ejecutar_extractor(banco_final, datos_ocr)
        campos_extraidos = self._agregar_fecha_normalizada(campos_extraidos)

        # Separar los datos los Primarios y Secundarios
        datos_primarios, datos_secundarios = self._separar_primarios_y_secundarios(
            banco_final, campos_extraidos
        )

        nombre_banco_legible = next(
            (b["nombre"] for b in BANCOS_SOPORTADOS if b["id"] == banco_final),
            banco_final,
        )

        return {
            "exito": True,
            "banco": banco_final,
            "banco_nombre": nombre_banco_legible,
            "modo": modo_aplicado,
            "clasificacion": info_clasificacion,
            "datos_primarios": datos_primarios,
            "datos_secundarios": datos_secundarios,
            "todos_los_campos": campos_extraidos,
            "total_detecciones": len(datos_ocr.get("detecciones", [])),
        }

    def procesar_archivo(
        self,
        ruta_archivo: str,
        banco_solicitado: Optional[str] = None,
        modo: str = "AUTO",
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """Procesa un único comprobante desde un archivo JSON o imagen física."""
        ruta = Path(ruta_archivo)
        if not ruta.is_file():
            raise FileNotFoundError(f"No existe el archivo: {ruta}")

        ext = ruta.suffix.lower()
        if ext == ".json":
            if verbose:
                print(f"\n[+] Cargando archivo JSON: {ruta}")
            with open(ruta, "r", encoding="utf-8-sig") as f:
                datos_ocr = json.load(f)
        else:
            if verbose:
                print(f"\n[+] Ejecutando OCR sobre imagen: {ruta}")
            datos_ocr = self.procesar_imagen_a_detecciones(str(ruta))
            if verbose:
                print(f"[+] Detecciones encontradas por OCR: {datos_ocr.get('total_detecciones', 0)}")

        if verbose:
            print(f"[+] Procesando comprobante (Modo: {modo}, Banco solicitado: {banco_solicitado or 'AUTO'})...")

        resultado = self.procesar_comprobante(
            datos_ocr=datos_ocr,
            banco_solicitado=banco_solicitado,
            modo=modo,
        )
        resultado["archivo"] = str(ruta)
        resultado["nombre_archivo"] = ruta.name
        return resultado

    @staticmethod
    def listar_comprobantes_en_carpeta(
        ruta_carpeta: str,
        recursivo: bool = False,
        limite: Optional[int] = None,
    ) -> List[Path]:
        """
        Obtiene los comprobantes (imágenes o JSON OCR) dentro de una carpeta.
        Prioriza imágenes; si no hay imágenes, busca archivos JSON de OCR.
        """
        carpeta = Path(ruta_carpeta)
        if not carpeta.is_dir():
            raise NotADirectoryError(f"No existe la carpeta: {carpeta}")

        ext_imagenes = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
        iterador = carpeta.rglob("*") if recursivo else carpeta.iterdir()
        archivos = sorted(p for p in iterador if p.is_file())

        imagenes = [p for p in archivos if p.suffix.lower() in ext_imagenes]
        if imagenes:
            seleccion = imagenes
        else:
            seleccion = [
                p for p in archivos
                if p.suffix.lower() == ".json" and not p.name.lower().startswith("resultado_")
            ]

        if limite is not None and limite > 0:
            seleccion = seleccion[:limite]
        return seleccion

    def _procesar_lista_archivos(
        self,
        archivos: List[Path],
        banco_solicitado: Optional[str] = None,
        modo: str = "AUTO",
        al_procesar=None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int], int, int]:
        """Procesa una lista de rutas de comprobantes y acumula métricas."""
        resultados: List[Dict[str, Any]] = []
        resumen_bancos: Dict[str, int] = {}
        exitosos = 0
        errores = 0
        total = len(archivos)

        for idx, ruta in enumerate(archivos, 1):
            try:
                res = self.procesar_archivo(
                    str(ruta),
                    banco_solicitado=banco_solicitado,
                    modo=modo,
                    verbose=False,
                )
                exitosos += 1
                banco_det = res.get("banco", "DESCONOCIDO")
                resumen_bancos[banco_det] = resumen_bancos.get(banco_det, 0) + 1
            except Exception as err:
                errores += 1
                res = {
                    "exito": False,
                    "archivo": str(ruta),
                    "nombre_archivo": ruta.name,
                    "error": f"{type(err).__name__}: {err}",
                }

            resultados.append(res)
            if al_procesar is not None:
                al_procesar(idx, total, ruta, res)

        return resultados, resumen_bancos, exitosos, errores

    def procesar_carpeta(
        self,
        ruta_carpeta: str,
        banco_solicitado: Optional[str] = None,
        modo: str = "AUTO",
        recursivo: bool = False,
        limite: Optional[int] = None,
        al_procesar=None,
    ) -> Dict[str, Any]:
        """Procesa de forma masiva todos los comprobantes de una carpeta."""
        archivos = self.listar_comprobantes_en_carpeta(
            ruta_carpeta=ruta_carpeta,
            recursivo=recursivo,
            limite=limite,
        )
        resultados, resumen_bancos, exitosos, errores = self._procesar_lista_archivos(
            archivos=archivos,
            banco_solicitado=banco_solicitado,
            modo=modo,
            al_procesar=al_procesar,
        )
        return {
            "exito": errores == 0,
            "carpeta": str(Path(ruta_carpeta)),
            "modo": modo,
            "recursivo": recursivo,
            "total": len(archivos),
            "exitosos": exitosos,
            "errores": errores,
            "resumen_bancos": dict(sorted(resumen_bancos.items())),
            "resultados": resultados,
        }

    def procesar_carpeta_por_bloques(
        self,
        ruta_carpeta: str,
        tamano_bloque: int = 10,
        numero_bloque: Optional[int] = None,
        banco_solicitado: Optional[str] = None,
        modo: str = "AUTO",
        recursivo: bool = False,
        limite: Optional[int] = None,
        al_iniciar_bloque=None,
        al_procesar=None,
        al_terminar_bloque=None,
    ) -> Dict[str, Any]:
        """Procesa los comprobantes de una carpeta divididos en bloques (por defecto de 10)."""
        if tamano_bloque < 1:
            raise ValueError("El tamaño de bloque debe ser al menos 1.")

        archivos = self.listar_comprobantes_en_carpeta(
            ruta_carpeta=ruta_carpeta,
            recursivo=recursivo,
            limite=limite,
        )
        total_archivos = len(archivos)
        grupos = [
            archivos[i : i + tamano_bloque]
            for i in range(0, total_archivos, tamano_bloque)
        ]
        total_bloques = len(grupos)

        if numero_bloque is not None:
            if numero_bloque < 1 or numero_bloque > total_bloques:
                raise ValueError(
                    f"El bloque {numero_bloque} no existe. Bloques disponibles: 1..{total_bloques} ({total_archivos} archivos)."
                )
            pares_bloques = [(numero_bloque, grupos[numero_bloque - 1])]
        else:
            pares_bloques = list(enumerate(grupos, 1))

        bloques_info: List[Dict[str, Any]] = []
        todos_resultados: List[Dict[str, Any]] = []
        resumen_global_bancos: Dict[str, int] = {}
        total_exitosos = 0
        total_errores = 0
        procesados_global = 0

        for num_bloque, lote in pares_bloques:
            inicio_global = (num_bloque - 1) * tamano_bloque + 1
            fin_global = inicio_global + len(lote) - 1
            if al_iniciar_bloque is not None:
                al_iniciar_bloque(num_bloque, total_bloques, inicio_global, fin_global, len(lote))

            def _cb_item(idx_lote: int, tot_lote: int, ruta: Path, res: Dict[str, Any]) -> None:
                if al_procesar is not None:
                    al_procesar(num_bloque, total_bloques, idx_lote, tot_lote, ruta, res)

            res_lote, bancos_lote, ok_lote, err_lote = self._procesar_lista_archivos(
                archivos=lote,
                banco_solicitado=banco_solicitado,
                modo=modo,
                al_procesar=_cb_item,
            )

            info_bloque = {
                "numero_bloque": num_bloque,
                "total_bloques": total_bloques,
                "rango": f"{inicio_global}-{fin_global}",
                "total": len(lote),
                "exitosos": ok_lote,
                "errores": err_lote,
                "resumen_bancos": dict(sorted(bancos_lote.items())),
                "resultados": res_lote,
            }
            bloques_info.append(info_bloque)
            todos_resultados.extend(res_lote)
            total_exitosos += ok_lote
            total_errores += err_lote
            procesados_global += len(lote)
            for b_id, cant in bancos_lote.items():
                resumen_global_bancos[b_id] = resumen_global_bancos.get(b_id, 0) + cant

            if al_terminar_bloque is not None:
                al_terminar_bloque(info_bloque)

        return {
            "exito": total_errores == 0,
            "carpeta": str(Path(ruta_carpeta)),
            "modo": modo,
            "recursivo": recursivo,
            "tamano_bloque": tamano_bloque,
            "bloque_solicitado": numero_bloque,
            "total_bloques": total_bloques,
            "bloques_procesados": len(bloques_info),
            "total": procesados_global,
            "exitosos": total_exitosos,
            "errores": total_errores,
            "resumen_bancos": dict(sorted(resumen_global_bancos.items())),
            "bloques": bloques_info,
            "resultados": todos_resultados,
        }

    _MESES_FECHA = {
        "ene": 1, "enero": 1, "jan": 1, "january": 1,
        "feb": 2, "febrero": 2, "february": 2,
        "mar": 3, "marzo": 3, "march": 3,
        "abr": 4, "abril": 4, "apr": 4, "april": 4,
        "may": 5, "mayo": 5,
        "jun": 6, "junio": 6, "june": 6, "lunio": 6, "junlo": 6,
        "0un": 6, "lun": 6, "8un": 6, "un": 6,
        "jul": 7, "julio": 7, "july": 7, "jullo": 7,
        "0ul": 7, "0u1": 7, "lul": 7, "ju1": 7, "ju7": 7,
        "ago": 8, "agosto": 8, "aug": 8, "august": 8,
        "sep": 9, "sept": 9, "septiembre": 9, "setiembre": 9, "september": 9,
        "oct": 10, "octubre": 10, "october": 10,
        "nov": 11, "noviembre": 11, "november": 11,
        "dic": 12, "diciembre": 12, "dec": 12, "december": 12,
    }

    @classmethod
    def _mes_a_numero(cls, token: str) -> Optional[int]:
        limpio = unicodedata.normalize("NFD", str(token or "").lower().strip())
        limpio = "".join(c for c in limpio if unicodedata.category(c) != "Mn")
        return cls._MESES_FECHA.get(limpio)

    @staticmethod
    def _validar_fecha_componentes(dia: int, mes: int, anio: Optional[int] = None) -> Optional[str]:
        try:
            if anio is None:
                date(2024, mes, dia)
                return f"{dia:02d}/{mes:02d}"
            if anio < 100:
                anio += 2000
            if not (1990 <= anio <= 2099):
                return None
            date(anio, mes, dia)
            return f"{dia:02d}/{mes:02d}/{anio:04d}"
        except ValueError:
            return None

    @classmethod
    def normalizar_fecha(cls, texto_fecha: Any) -> Optional[str]:
        """Convierte cualquier fecha extraída al formato unificado DD/MM/YYYY (o DD/MM sin año)."""
        if not texto_fecha:
            return None
        s = str(texto_fecha).strip()
        if not s or s.upper() == "NO ENCONTRADO":
            return None

        # 1. YYYY/MM/DD o YYYY-MM-DD
        m = re.search(r"\b(20\d{2})[/\-\.](\d{1,2})[/\-\.](\d{1,2})\b", s)
        if m:
            res = cls._validar_fecha_componentes(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            if res:
                return res

        # 2. Mes DD, YYYY (ej. Jul 03, 2026 / Ju1 10, 2026)
        m = re.search(r"\b([A-Za-zÁÉÍÓÚáéíóúÑñ0-9]{3,12})\s+(\d{1,2})\s*,\s*(20\d{2}|\d{2})\b", s)
        if m:
            mes = cls._mes_a_numero(m.group(1))
            if mes:
                res = cls._validar_fecha_componentes(int(m.group(2)), mes, int(m.group(3)))
                if res:
                    return res

        # 3. DD [de] Mes [de] YYYY (incluye variantes OCR como 040ul/2026 o 03/0ul/2026)
        m = re.search(
            r"\b(\d{1,2})\s*(?:de\s+|[/\-\.\s]+)\s*([A-Za-zÁÉÍÓÚáéíóúÑñ0-9]{2,12})\s*(?:,?\s*(?:de|del)\s+|[/\-\.,\s]+)\s*(20\d{2}|(?<=[/\-\.])\d{2})(?!\s*:)\b",
            s,
            re.IGNORECASE,
        )
        if m:
            mes = cls._mes_a_numero(m.group(2))
            if mes:
                res = cls._validar_fecha_componentes(int(m.group(1)), mes, int(m.group(3)))
                if res:
                    return res

        m = re.search(r"\b(\d{2})([A-Za-z0-9]{2,4})[/\-\.](20\d{2})\b", s)
        if m:
            mes = cls._mes_a_numero(m.group(2))
            if mes:
                res = cls._validar_fecha_componentes(int(m.group(1)), mes, int(m.group(3)))
                if res:
                    return res

        # 4. DD/MM/YYYY, DD-MM-YYYY o DD/MM/YY
        m = re.search(r"\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](20\d{2}|\d{2})(?!\s*:)\b", s)
        if m:
            d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if mo > 12 and d <= 12:
                d, mo = mo, d
            res = cls._validar_fecha_componentes(d, mo, y)
            if res:
                return res

        # 5. DD [de] Mes (cuando el comprobante no trae año)
        m = re.search(r"\b(\d{1,2})\s*(?:de\s+|[/\-\.\s]+)\s*([A-Za-zÁÉÍÓÚáéíóúÑñ]{3,12})\b", s, re.IGNORECASE)
        if m:
            mes = cls._mes_a_numero(m.group(2))
            if mes:
                res = cls._validar_fecha_componentes(int(m.group(1)), mes, None)
                if res:
                    return res

        return None

    def _agregar_fecha_normalizada(self, campos: Dict[str, str]) -> Dict[str, str]:
        """Conserva todos los campos originales e inserta 'fecha_normalizada' junto a la fecha."""
        if not isinstance(campos, dict) or not campos:
            return campos

        prioridad = (
            "fecha",
            "fecha_operacion",
            "fecha_hora",
            "fecha_hora_operacion",
            "fecha_hora_recepcion",
            "fecha_hora_procesamiento",
        )
        claves_fecha = [k for k in prioridad if k in campos]
        for k in campos:
            if "fecha" in k.lower() and k != "fecha_normalizada" and k not in claves_fecha:
                claves_fecha.append(k)

        clave_ancla = claves_fecha[0] if claves_fecha else None
        fecha_norm = None
        for k in claves_fecha:
            candidato = self.normalizar_fecha(campos.get(k))
            if candidato:
                fecha_norm = candidato
                clave_ancla = k
                break

        if clave_ancla is None:
            return campos

        nuevo: Dict[str, str] = {}
        insertada = False
        for k, v in campos.items():
            if k == "fecha_normalizada":
                continue
            nuevo[k] = v
            if k == clave_ancla and not insertada:
                nuevo["fecha_normalizada"] = fecha_norm or "NO ENCONTRADO"
                insertada = True
        if not insertada:
            nuevo["fecha_normalizada"] = fecha_norm or "NO ENCONTRADO"
        return nuevo

    def _ejecutar_extractor(self, banco: str, datos_ocr: dict) -> dict:
        """Invoca el extractor específico del banco."""
        if banco == "INBURSA":
            return self._aplanar(extraer_inbursa(datos_ocr))
        if banco == "MERCADO_PAGO":
            return self._aplanar(extraer_mercado_pago(datos_ocr))
        if banco == "NU_MEXICO":
            return self._aplanar(extraer_nu_mexico(datos_ocr))
        if banco == "PAGO_OXXO":
            return self._aplanar(extraer_oxxo(datos_ocr))
        if banco == "BANCO_HSBC":
            res = hsbc_hib.extraer(datos_ocr)
            return self._aplanar(res)
        if banco in ("MIFEL", "SPIN_BY_OXXO", "TRANSFERENCIA_HSBC"):
            datos_prep = probar_mifel.preparar_datos(datos_ocr)
            inst = self.instancias.get(banco)
            if inst:
                return self._aplanar(inst.extraer(datos_prep))
        if banco in self.instancias:
            return self._aplanar(self.instancias[banco].extraer(datos_ocr))

        
        return {"aviso": "Banco no soportado directamente"}

    def _aplanar(self, res: dict) -> dict:
        """Normaliza la salida del extractor a diccionario plano."""
        campos = res.get("campos", res) if isinstance(res, dict) else {}
        plano = {}
        if isinstance(res, dict):
            for k_top in ("banco", "entidad", "tipo"):
                if k_top in res and not isinstance(res[k_top], dict):
                    plano[k_top] = str(res[k_top])
        for k, v in campos.items():
            if isinstance(v, dict):
                plano[k] = str(v.get("valor") or "")
            else:
                plano[k] = str(v or "")
        return plano

    def _separar_primarios_y_secundarios(self, banco: str, campos: dict) -> Tuple[dict, dict]:
        """Clasifica los campos en datos primarios (críticos) y secundarios."""
        primarios = {}
        secundarios = {}

        claves_primarias = {
            "clave_rastreo", "numero_rastreo", "monto", "importe_deposito", "monto_deposito",
            "fecha", "fecha_hora", "fecha_operacion", "fecha_hora_operacion",
            "referencia", "numero_referencia", "referencia_numerica", "ref_supermovil",
            "folio", "numero_folio", "folio_venta", "autorizacion", "transaccion", "numero_operacion",
            "referencia_finabien", "banco", "banco_emisor",
        }

        claves_secundarias = {
            "beneficiario", "nombre_beneficiario", "destinatario", "nombre",
            "titular", "titular_origen", "titular_destino", "titular_cuenta_beneficiario",
            "concepto", "mensaje", "descripcion",
            "cuenta_destino", "cuenta_beneficiario", "clabe", "clabe_receptor", "cuenta_clabe_destino",
            "cuenta_origen", "cuenta_tarjeta", "recibe", "banco_receptor", "banco_destino", "entidad",
            "deposito", "tipo_operacion", "tipo_transferencia", "categoria",
        }

        for k, v in campos.items():
            k_low = k.lower().strip()
            if k_low in claves_primarias:
                primarios[k] = v
            elif k_low in claves_secundarias:
                secundarios[k] = v
            else:
                # Si contiene palabras primarias
                if any(x in k_low for x in ("monto", "fecha", "rastreo", "folio", "autori", "ref")):
                    primarios[k] = v
                else:
                    secundarios[k] = v

        return primarios, secundarios


def _formatear_resultado_texto(resultado: Dict[str, Any], titulo_archivo: Optional[str] = None) -> str:
    """Genera el bloque legible de extracción para consola o archivo de reporte."""
    lineas = ["", "=" * 70]
    if titulo_archivo:
        lineas.append(f" RESULTADO DE LA EXTRACCIÓN - {titulo_archivo}")
    else:
        lineas.append(" RESULTADO DE LA EXTRACCIÓN")
    lineas.append("=" * 70)

    if not resultado.get("exito", True):
        lineas.append(f" [ERROR] {resultado.get('error', 'Error desconocido')}")
        lineas.append("=" * 70 + "\n")
        return "\n".join(lineas)

    lineas.append(f" Banco Detectado : {resultado['banco']} ({resultado['banco_nombre']})")
    lineas.append(f" Modo Aplicado   : {resultado['modo']}")
    if resultado.get("clasificacion"):
        c = resultado["clasificacion"]
        lineas.append(f" Regla / Método  : {c.get('regla')} | Confianza: {c.get('confianza', 0)*100:.0f}%")
    lineas.append(f" Total Detecciones OCR: {resultado.get('total_detecciones', 0)}")

    lineas.append("\n--- DATOS PRIMARIOS (CRÍTICOS) ---")
    if resultado.get("datos_primarios"):
        for k, v in resultado["datos_primarios"].items():
            lineas.append(f"  * {k:<25}: {v}")
    else:
        lineas.append("  (Sin datos primarios detectados)")

    lineas.append("\n--- DATOS SECUNDARIOS ---")
    if resultado.get("datos_secundarios"):
        for k, v in resultado["datos_secundarios"].items():
            lineas.append(f"  * {k:<25}: {v}")
    else:
        lineas.append("  (Sin datos secundarios detectados)")

    lineas.append("=" * 70 + "\n")
    return "\n".join(lineas)


def _formatear_resumen_masivo(reporte: Dict[str, Any]) -> str:
    """Genera el resumen final de una ejecución masiva o por bloques."""
    titulo = " RESUMEN DEL PROCESO POR BLOQUES" if "bloques" in reporte else " RESUMEN DEL PROCESO MASIVO"
    lineas = [
        "",
        "=" * 70,
        titulo,
        "=" * 70,
        f" Carpeta          : {reporte['carpeta']}",
        f" Modo             : {reporte['modo']}",
    ]
    if "bloques" in reporte:
        lineas.append(
            f" Bloques          : {reporte['bloques_procesados']} de {reporte['total_bloques']} (tamaño {reporte['tamano_bloque']})"
        )
    lineas.extend([
        f" Total archivos   : {reporte['total']}",
        f" Procesados éxito : {reporte['exitosos']}",
        f" Errores          : {reporte['errores']}",
        "\n Desglose por banco:",
    ])
    if reporte.get("resumen_bancos"):
        for banco_id, cantidad in reporte["resumen_bancos"].items():
            lineas.append(f"  * {banco_id:<25}: {cantidad}")
    else:
        lineas.append("  (Sin comprobantes procesados)")
    lineas.append("=" * 70 + "\n")
    return "\n".join(lineas)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Gestor y Orquestador Central de Extracción de Comprobantes (28 Bancos)"
    )
    parser.add_argument(
        "--lista-bancos", "-l",
        action="store_true",
        help="Muestra la lista de los 28 bancos soportados.",
    )
    parser.add_argument(
        "--json", "-j",
        type=str,
        help="Ruta a un archivo JSON existente con detecciones OCR.",
    )
    parser.add_argument(
        "--imagen", "-i",
        type=str,
        help="Ruta a una imagen física (JPG, PNG, etc.) para procesar con PaddleOCR y extraer datos.",
    )
    parser.add_argument(
        "--carpeta", "-c",
        type=str,
        help="Ruta a una carpeta (nueva o del sistema) para procesar comprobantes de forma masiva.",
    )
    parser.add_argument(
        "--bloques",
        type=str,
        default=None,
        help="Ruta a una carpeta para procesar comprobantes en bloques de 10 (equivale a --carpeta --por-bloques).",
    )
    parser.add_argument(
        "--por-bloques",
        action="store_true",
        help="Procesa la carpeta indicada con --carpeta dividida en bloques de 10 comprobantes.",
    )
    parser.add_argument(
        "--bloque",
        type=int,
        default=None,
        help="Número de bloque (1, 2, 3...) a ejecutar al usar --carpeta o --bloques.",
    )
    parser.add_argument(
        "--tamano-bloque",
        type=int,
        default=10,
        help="Cantidad de comprobantes por bloque (por defecto: 10).",
    )
    parser.add_argument(
        "--recursivo", "-r",
        action="store_true",
        help="Incluye subcarpetas al procesar con --carpeta.",
    )
    parser.add_argument(
        "--limite", "-n",
        type=int,
        default=None,
        help="Número máximo de archivos a procesar en modo --carpeta.",
    )
    parser.add_argument(
        "--guardar", "-o",
        type=str,
        default=None,
        help="Ruta opcional (.json o .txt) donde guardar el reporte completo del proceso masivo.",
    )
    parser.add_argument(
        "--banco", "-b",
        type=str,
        default=None,
        help="ID del banco para forzar modo manual (ej. BBVA, AZTECA). Por defecto es AUTO.",
    )
    parser.add_argument(
        "--salida-json",
        action="store_true",
        help="Imprime el resultado completo en formato JSON plano.",
    )

    args = parser.parse_args()

    if args.lista_bancos:
        print("\n" + "=" * 70)
        print(f" LISTA DE BANCOS SOPORTADOS ({len(BANCOS_SOPORTADOS)})")
        print("=" * 70)
        for i, b in enumerate(BANCOS_SOPORTADOS, 1):
            print(f" {i:2d}. [{b['id']:<24}] -> {b['nombre']}")
        print("=" * 70 + "\n")
        sys.exit(0)

    carpeta_objetivo = args.bloques or args.carpeta
    usar_bloques = bool(args.bloques or args.por_bloques or args.bloque is not None)

    if carpeta_objetivo:
        ruta_dir = Path(carpeta_objetivo)
        if not ruta_dir.is_dir():
            print(f"[ERROR] No existe la carpeta: {ruta_dir}")
            sys.exit(1)

        gestor = GestorExtraccion()
        modo = "MANUAL" if args.banco else "AUTO"
        archivos_previos = gestor.listar_comprobantes_en_carpeta(
            str(ruta_dir),
            recursivo=args.recursivo,
            limite=args.limite,
        )

        if not archivos_previos:
            print(f"[AVISO] No se encontraron imágenes ni archivos JSON en: {ruta_dir}")
            if not args.recursivo and any(p.is_dir() for p in ruta_dir.iterdir()):
                print("[TIP] La carpeta contiene subcarpetas; agrega --recursivo para incluirlas.")
            sys.exit(0)

        bloques_txt: List[str] = []

        if usar_bloques:
            if args.tamano_bloque < 1:
                print("[ERROR] --tamano-bloque debe ser mayor o igual a 1.")
                sys.exit(1)
            total_bloques = (len(archivos_previos) + args.tamano_bloque - 1) // args.tamano_bloque
            if args.bloque is not None and (args.bloque < 1 or args.bloque > total_bloques):
                print(
                    f"[ERROR] El bloque {args.bloque} no existe. Bloques disponibles (de {args.tamano_bloque}): 1..{total_bloques} ({len(archivos_previos)} archivos)."
                )
                sys.exit(1)

            if not args.salida_json:
                desc_bloque = f"bloque {args.bloque}/{total_bloques}" if args.bloque else f"{total_bloques} bloques"
                print(f"\n[+] Iniciando extracción por bloques de {args.tamano_bloque} en: {ruta_dir}")
                print(f"[+] Archivos totales: {len(archivos_previos)} | A ejecutar: {desc_bloque} | Modo: {modo} | Banco: {args.banco or 'AUTO'}")

            def _al_iniciar_bloque(num_b: int, tot_b: int, ini: int, fin: int, cant: int) -> None:
                enc = f"\n{'#' * 70}\n BLOQUE {num_b}/{tot_b} | Comprobantes {ini} al {fin} ({cant} archivos)\n{'#' * 70}"
                bloques_txt.append(enc)
                if not args.salida_json:
                    print(enc)

            def _al_procesar_bloque(num_b: int, tot_b: int, idx_l: int, tot_l: int, ruta: Path, res: Dict[str, Any]) -> None:
                bloque = _formatear_resultado_texto(res, titulo_archivo=f"[B{num_b}/{tot_b} - {idx_l}/{tot_l}] {ruta.name}")
                bloques_txt.append(bloque)
                if not args.salida_json:
                    print(bloque)

            def _al_terminar_bloque(info_b: Dict[str, Any]) -> None:
                pie = (
                    f"[+] Fin Bloque {info_b['numero_bloque']}/{info_b['total_bloques']} "
                    f"(rango {info_b['rango']}): {info_b['exitosos']}/{info_b['total']} exitosos, "
                    f"{info_b['errores']} errores"
                )
                bloques_txt.append(pie)
                if not args.salida_json:
                    print(pie)

            reporte = gestor.procesar_carpeta_por_bloques(
                ruta_carpeta=str(ruta_dir),
                tamano_bloque=args.tamano_bloque,
                numero_bloque=args.bloque,
                banco_solicitado=args.banco,
                modo=modo,
                recursivo=args.recursivo,
                limite=args.limite,
                al_iniciar_bloque=_al_iniciar_bloque,
                al_procesar=_al_procesar_bloque,
                al_terminar_bloque=_al_terminar_bloque,
            )
        else:
            if not args.salida_json:
                print(f"\n[+] Iniciando proceso masivo en: {ruta_dir}")
                print(f"[+] Archivos a procesar: {len(archivos_previos)} | Modo: {modo} | Banco: {args.banco or 'AUTO'}")

            def _mostrar_progreso(idx: int, total: int, ruta: Path, res: Dict[str, Any]) -> None:
                bloque = _formatear_resultado_texto(res, titulo_archivo=f"[{idx}/{total}] {ruta.name}")
                bloques_txt.append(bloque)
                if not args.salida_json:
                    print(bloque)

            reporte = gestor.procesar_carpeta(
                ruta_carpeta=str(ruta_dir),
                banco_solicitado=args.banco,
                modo=modo,
                recursivo=args.recursivo,
                limite=args.limite,
                al_procesar=_mostrar_progreso,
            )

        resumen_txt = _formatear_resumen_masivo(reporte)
        if args.salida_json:
            print(json.dumps(reporte, indent=2, ensure_ascii=False))
        else:
            print(resumen_txt)

        if args.guardar:
            ruta_salida = Path(args.guardar)
            ruta_salida.parent.mkdir(parents=True, exist_ok=True)
            if ruta_salida.suffix.lower() == ".json":
                with open(ruta_salida, "w", encoding="utf-8") as f:
                    json.dump(reporte, f, indent=2, ensure_ascii=False)
            else:
                with open(ruta_salida, "w", encoding="utf-8") as f:
                    f.write("\n".join(bloques_txt) + "\n" + resumen_txt)
            if not args.salida_json:
                print(f"[+] Reporte guardado en: {ruta_salida}")

        sys.exit(0 if reporte["errores"] == 0 else 1)

    if args.json or args.imagen:
        gestor = GestorExtraccion()
        modo = "MANUAL" if args.banco else "AUTO"
        ruta_entrada = Path(args.json if args.json else args.imagen)
        if not ruta_entrada.exists():
            tipo_msg = "el archivo JSON" if args.json else "la imagen"
            print(f"[ERROR] No existe {tipo_msg}: {ruta_entrada}")
            sys.exit(1)

        resultado = gestor.procesar_archivo(
            str(ruta_entrada),
            banco_solicitado=args.banco,
            modo=modo,
            verbose=not args.salida_json,
        )

        if args.salida_json:
            print(json.dumps(resultado, indent=2, ensure_ascii=False))
            sys.exit(0)

        print(_formatear_resultado_texto(resultado))
        sys.exit(0)

    parser.print_help()

