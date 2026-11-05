from pathlib import Path
import importlib.util
import sys

RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))


def _cargar_modulo_hibrido():
    ruta_hibrido = RAIZ_PROYECTO / "Pruebas" / "probar_hibrido_bancoopel.py"
    nombre_mod = "_hibrido_bancoopel_interno"
    if nombre_mod in sys.modules:
        return sys.modules[nombre_mod]

    spec = importlib.util.spec_from_file_location(nombre_mod, str(ruta_hibrido))
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar el módulo híbrido BanCoppel: {ruta_hibrido}")

    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre_mod] = modulo
    spec.loader.exec_module(modulo)
    return modulo


class BancoppelExtractor:
    """Extractor formal para comprobantes BANCOPPEL."""

    def __init__(self):
        self.nombre_banco = "BANCOPPEL"
        self._modulo = _cargar_modulo_hibrido()

    def extraer(self, datos):
        return self._modulo.extraer(datos)

    def combinar_variantes(self, variantes_extraidas, nombre_archivo=""):
        return self._modulo.combinar_variantes(variantes_extraidas, nombre_archivo)


def extraer(datos):
    return BancoppelExtractor().extraer(datos)


def crear_extractor():
    return BancoppelExtractor()
