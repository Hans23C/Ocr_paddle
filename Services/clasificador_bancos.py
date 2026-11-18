# ============================================================
# CLASIFICADOR INTELIGENTE DE LOS 28 BANCOS
# ============================================================

import re
from typing import Any, Dict, List, Optional


class ClasificadorBancos:
    """Clasifica comprobantes de pago según detecciones OCR a uno de los 28 bancos soportados."""

    def __init__(self):
        pass

    def clasificar(self, datos_ocr: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza las detecciones OCR y determina el banco emisor.
        Retorna un diccionario con:
          - banco: ID del banco (ej. 'BBVA', 'AZTECA')
          - confianza: flotante entre 0.0 y 1.0
          - metodo: estrategia que detectó el banco
          - regla: nombre de la regla aplicada
        """
        detecciones = datos_ocr.get("detecciones", []) if isinstance(datos_ocr, dict) else []
        textos = [d.get("texto", "") for d in detecciones if isinstance(d, dict)]
        texto_completo = " ".join(textos)
        texto_upper = texto_completo.upper()

        # 1. FARMACIAS DEL AHORRO
        if (
            "FARMACIAS DEL AHORRO" in texto_upper
            or "FARMACIAS DE AHORRO" in texto_upper
            or "COMERCIALIZADORA FARMACEUTICA DE CHIAPAS" in texto_upper
        ):
            return {
                "banco": "FARMACIAS_DE_AHORRO",
                "confianza": 0.98,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_FARMACIAS_DEL_AHORRO",
            }

        # 2. SPIN BY OXXO
        if (
            "SPIN BY OXXO" in texto_upper
            or "SPIN BYOXXO" in texto_upper
            or ("SPIN" in texto_upper and "BYOXXO" in texto_upper)
            or ("SPIN" in texto_upper and "OXXO" in texto_upper and "ENVIASTE" in texto_upper)
        ):
            return {
                "banco": "SPIN_BY_OXXO",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_SPIN_BY_OXXO",
            }

        # 3. PAGO EN OXXO
        if (
            "CADENA COMERCIAL OXXO" in texto_upper
            or "OXXO PAY" in texto_upper
            or ("OXXO" in texto_upper and "C.V." in texto_upper)
            or ("OXXO" in texto_upper and "MONTERREY" in texto_upper)
        ):
            return {
                "banco": "PAGO_OXXO",
                "confianza": 0.98,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_PAGO_OXXO",
            }

        # 4. MERCADO PAGO
        if (
            "MERCADO PAGO" in texto_upper
            or "MERCADOPAGO" in texto_upper
            or ("MERCADO" in texto_upper and "PAGO" in texto_upper and "WALLET" in texto_upper)
        ):
            return {
                "banco": "MERCADO_PAGO",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_MERCADO_PAGO",
            }

        # 5. BANCOPPEL
        if (
            "BANCOPPEL" in texto_upper
            or "BANCOOPEL" in texto_upper
            or ("HORA DE CONSULTA" in texto_upper and ("FECHA DE CONSULTA" in texto_upper or "PEPES MALS" in texto_upper or "LURIO" in texto_upper))
            or ("COMPROBANTE DE PAGO SPEI" in texto_upper and "BANCOPPEL" in texto_upper)
        ):
            return {
                "banco": "BANCOPPEL",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_BANCOPPEL",
            }

        # 6. BANCO AZTECA
        if (
            "BANCO AZTECA" in texto_upper
            or "GUARDADITO" in texto_upper
            or "APP BAZ" in texto_upper
            or "ENVIASTE A UNA CUENTA" in texto_upper
            or ("AZTECA" in texto_upper and "MÉX., ESTADO DE" in texto_upper)
        ):
            return {
                "banco": "AZTECA",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_BANCO_AZTECA",
            }

        # 7. STORI (Verificar antes de transferencias para no confundir con concepto 'Transferencia HSBC')
        if (
            "STORICARD" in texto_upper
            or "STORI" in texto_upper
            or any(re.search(r"\bstori\b", t.lower()) for t in textos)
        ):
            return {
                "banco": "STORI",
                "confianza": 0.98,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_STORI",
            }

        # 8. TRANSFERENCIA HSBC (Digital / App)
        if (
            "TRANSFERENCIA A TERCERO HSBC" in texto_upper
            or "TRANSFERENCIA A OTROS BANCOS HSBC" in texto_upper
            or ("TRANSFERENCIA HSBC" in texto_upper and "STORI" not in texto_upper and "CONCEPTO" not in texto_upper)
            or ("RESUMEN DE OPERACIÓN" in texto_upper and "HSBC" in texto_upper)
        ):
            return {
                "banco": "TRANSFERENCIA_HSBC",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_TRANSFERENCIA_HSBC",
            }

        # 9. BANCO HSBC (Practicaja / Ventanilla / General)
        if (
            "HSBC MEXICO" in texto_upper
            or "SUC SANTIAGO" in texto_upper
            or "SUC." in texto_upper and "HSBC" in texto_upper
            or "DEPOSITO A CUENTA HSBC" in texto_upper
        ):
            return {
                "banco": "BANCO_HSBC",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_BANCO_HSBC",
            }

        # 9. BBVA
        if (
            "BBVA" in texto_upper
            or "TRANSFERIR & DIMO" in texto_upper
            or "LÍNEA BBVA" in texto_upper
            or "CUENTA•" in texto_upper and "MONTO TRANSFERIDO" in texto_upper
        ):
            return {
                "banco": "BBVA",
                "confianza": 0.98,
                "metodo": "PALABRA_CLAVE",
                "regla": "DETECTADO_POR_FIRMA_BBVA",
            }

        # 10. BANAMEX
        if (
            "BANAMEX" in texto_upper
            or "CITIBANAMEX" in texto_upper
            or "BANCANET" in texto_upper
        ):
            return {
                "banco": "BANAMEX",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_BANAMEX",
            }

        # 11. BANBAJIO
        if (
            "BANBAJIO" in texto_upper
            or "BANCO DEL BAJÍO" in texto_upper
            or "BANCO DEL BAJIO" in texto_upper
            or "BAJIONET" in texto_upper
        ):
            return {
                "banco": "BANBAJIO",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_BANBAJIO",
            }

        # 12. BANORTE
        if "BANORTE" in texto_upper:
            return {
                "banco": "BANORTE",
                "confianza": 0.98,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_BANORTE",
            }

        # 13. CLARO PAY
        if "CLARO PAY" in texto_upper or "CLARO-PAY" in texto_upper or "CLAROPAY" in texto_upper:
            return {
                "banco": "CLARO_PAY",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_CLARO_PAY",
            }

        # 14. COMPARTAMOS BANCO
        if "COMPARTAMOS" in texto_upper:
            return {
                "banco": "COMPARTAMOS_BANCO",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_COMPARTAMOS_BANCO",
            }

        # 15. FINANCIERA PARA EL BIENESTAR (FINABIEN)
        if (
            "FINANCIERA PARA EL BIENESTAR" in texto_upper
            or "FINABIEN" in texto_upper
            or "TELECOMM" in texto_upper
        ):
            return {
                "banco": "FINANCIERA_BIENESTAR",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_FINANCIERA_BIENESTAR",
            }

        # 16. TRANSFERENCIA BANCO DEL BIENESTAR
        if (
            "BANCO DEL BIENESTAR" in texto_upper
            or ("OPERACIÓN EXITOSA" in texto_upper and "ENVIAR DINERO" in texto_upper and "RECIBE:" in texto_upper)
            or ("BIENESTAR" in texto_upper and "FINANCIERA" not in texto_upper)
        ):
            return {
                "banco": "TRANSFERENCIA_BIENESTAR",
                "confianza": 0.90,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_TRANSFERENCIA_BIENESTAR",
            }

        # 17. ALBO
        if any(re.search(r"\balbo\b", t.lower()) for t in textos):
            return {
                "banco": "ALBO",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_ALBO",
            }

        # 18. HEY BANCO
        if (
            "HEY BANCO" in texto_upper
            or "HEYBANCO" in texto_upper
            or "NEBANCO" in texto_upper
        ):
            return {
                "banco": "HEY_BANCO",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_HEY_BANCO",
            }

        # 19. INBURSA
        if "INBURSA" in texto_upper:
            return {
                "banco": "INBURSA",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_INBURSA",
            }

        # 20. KLAR
        if any(re.search(r"\bklar\b", t.lower()) for t in textos):
            return {
                "banco": "KLAR",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_KLAR",
            }

        # 21. MIFEL
        if "MIFEL" in texto_upper:
            return {
                "banco": "MIFEL",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_MIFEL",
            }

        # 22. NU MEXICO
        if (
            "NU MEXICO" in texto_upper
            or "NU MÉXICO" in texto_upper
            or "PROPICIANTE" in texto_upper
            or "PROPANTE DE TRANSFERECIA" in texto_upper
            or "COMPROBANTE DE TRANSFERENCIA" in texto_upper and "HORA DE CDMX" in texto_upper
            or any(re.search(r"\bnu\b", t.lower()) for t in textos[:6])
        ):
            return {
                "banco": "NU_MEXICO",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_NU_MEXICO",
            }

        # 23. PLATA
        if any(re.search(r"\bplata\b", t.lower()) for t in textos):
            return {
                "banco": "PLATA",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_PLATA",
            }

        # 24. REVOLUT
        if "REVOLUT" in texto_upper:
            return {
                "banco": "REVOLUT",
                "confianza": 0.98,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_REVOLUT",
            }

        # 25. SANTANDER
        if "SANTANDER" in texto_upper or "SUPERMÓVIL" in texto_upper or "SUPERMOVIL" in texto_upper:
            return {
                "banco": "SANTANDER",
                "confianza": 0.98,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_SANTANDER",
            }

        # 26. SCOTIABANK
        if "SCOTIABANK" in texto_upper or "SCOTIA" in texto_upper:
            return {
                "banco": "SCOTIABANK",
                "confianza": 0.98,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_SCOTIABANK",
            }

        # 27. STORI
        if "STORI" in texto_upper or any(re.search(r"\bstori\b", t.lower()) for t in textos):
            return {
                "banco": "STORI",
                "confianza": 0.95,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_STORI",
            }

        # 28. FONDEADORA
        if (
            "FONDEADORA" in texto_upper
            or ("TRANSFERENCIA PARA" in texto_upper and "DE JULIO" in texto_upper)
            or ("TRANSFERENCIA PARA" in texto_upper and "ESTATUS" in texto_upper)
        ):
            return {
                "banco": "FONDEADORA",
                "confianza": 0.90,
                "metodo": "PALABRA_CLAVE",
                "regla": "FIRMA_FONDEADORA",
            }

        # Fallback genérico si contiene HSBC en algún lugar
        if "HSBC" in texto_upper:
            return {
                "banco": "BANCO_HSBC",
                "confianza": 0.70,
                "metodo": "HEURISTICA",
                "regla": "FALLBACK_HSBC",
            }

        return {
            "banco": "DESCONOCIDO",
            "confianza": 0.0,
            "metodo": "SIN_COINCIDENCIA",
            "regla": "NINGUNA",
        }
