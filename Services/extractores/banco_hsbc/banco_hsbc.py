from pathlib import Path
import importlib.util
import sys

RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))


def _cargar_modulo_hibrido():
    ruta_hibrido = RAIZ_PROYECTO / "Pruebas" / "probar_hibrido_banco_hsbc.py"
    nombre_mod = "_hibrido_banco_hsbc_interno"
    if nombre_mod in sys.modules:
        return sys.modules[nombre_mod]

    spec = importlib.util.spec_from_file_location(nombre_mod, str(ruta_hibrido))
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar el módulo híbrido HSBC: {ruta_hibrido}")

    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre_mod] = modulo
    spec.loader.exec_module(modulo)
    return modulo


class BancoHSBCExtractor:
    """Extractor formal para comprobantes de depósito BANCO_HSBC."""

    def __init__(self):
        self.nombre_banco = "BANCO_HSBC"
        self._modulo = _cargar_modulo_hibrido()

    def extraer(self, datos):
        return self._modulo.extraer(datos)


def extraer(datos):
    return BancoHSBCExtractor().extraer(datos)


def crear_extractor():
    return BancoHSBCExtractor()
