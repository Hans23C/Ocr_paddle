from dataclasses import dataclass
from typing import List
import os
import re

from PIL import Image


@dataclass
class OCRDeteccion:
    texto: str
    confianza: float

    bbox: List[List[float]]

    x: float
    y: float
    ancho: float
    alto: float

    x_rel: float
    y_rel: float
    ancho_rel: float
    alto_rel: float


@dataclass
class ResultadoOCR:
    detecciones: List[OCRDeteccion]
    lineas: List[str]
    texto_completo: str

    ancho_imagen: int
    alto_imagen: int


class PaddleOCRServicio:

    def __init__(self, idioma="es"):

        self.idioma = idioma

        self.ocr = self._crear_ocr()

    # ========================================================
    # CREAR OCR
    # ========================================================

    def _crear_ocr(self):

        from paddleocr import PaddleOCR

        return PaddleOCR(
            lang=self.idioma,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=True,
            enable_mkldnn=False,
        )

    # ========================================================
    # PROCESAR IMAGEN
    # ========================================================

    def procesar_imagen(
       self,
       ruta_imagen: str,
       reprocesar_nu: bool = False,
       reprocesar_santander: bool = False
       ) -> ResultadoOCR:

        if not os.path.isfile(ruta_imagen):

            raise FileNotFoundError(
                f"No existe la imagen: {ruta_imagen}"
            )

        # ----------------------------------------------------
        # OCR NORMAL
        # ----------------------------------------------------

        resultado = self.ocr.predict(
            ruta_imagen
        )

        detecciones = []

        ancho_imagen = 0
        alto_imagen = 0

        for pagina in resultado:

            datos = self._obtener_datos(
                pagina
            )

            if datos is None:
                continue

            textos = datos["textos"]
            scores = datos["scores"]
            cajas = datos["cajas"]

            ancho_imagen = max(
                ancho_imagen,
                datos["ancho"]
            )

            alto_imagen = max(
                alto_imagen,
                datos["alto"]
            )

            for texto, score, bbox in zip(
                textos,
                scores,
                cajas
            ):

                texto = str(
                    texto
                ).strip()

                if not texto:
                    continue

                deteccion = self._crear_deteccion(
                    texto=texto,
                    confianza=float(score),
                    bbox=bbox,
                    ancho_imagen=ancho_imagen,
                    alto_imagen=alto_imagen,
                )

                detecciones.append(
                    deteccion
                )

        # ----------------------------------------------------
        # REPROCESAMIENTO ESPECIAL NU
        # ----------------------------------------------------

        if reprocesar_nu:

            detecciones_nu = (
                self._reprocesar_region_superior_nu(
                    ruta_imagen,
                    ancho_imagen,
                    alto_imagen
                )
            )

            detecciones.extend(
                detecciones_nu
            )

        # ----------------------------------------------------
        # REPROCESAMIENTO ESPECIAL SANTANDER
        # ----------------------------------------------------

        if reprocesar_santander:

            detecciones_santander = (
                self._reprocesar_region_santander(
                    ruta_imagen,
                    ancho_imagen,
                    alto_imagen
                )
            )

            detecciones.extend(
                detecciones_santander
            )

        # ----------------------------------------------------
        # ORDENAR
        # ----------------------------------------------------

        detecciones = (
            self._ordenar_detecciones(
                detecciones
            )
        )

        # ----------------------------------------------------
        # RECONSTRUIR LÍNEAS
        # ----------------------------------------------------

        lineas = (
            self._reconstruir_lineas(
                detecciones
            )
        )

        texto_completo = "\n".join(
            lineas
        )

        return ResultadoOCR(
            detecciones=detecciones,
            lineas=lineas,
            texto_completo=texto_completo,
            ancho_imagen=ancho_imagen,
            alto_imagen=alto_imagen,
        )

    # ========================================================
    # REPROCESAMIENTO REGIÓN SUPERIOR NU
    # ========================================================

    def _reprocesar_region_superior_nu(
        self,
        ruta_imagen,
        ancho_imagen,
        alto_imagen
    ):

        # ----------------------------------------------------
        # CONFIGURACIÓN COMPROBADA
        # ----------------------------------------------------

        Y_INICIO = 120
        Y_FIN = 250

        FACTOR_ESCALA = 4

        detecciones = []

        imagen = Image.open(
            ruta_imagen
        ).convert("RGB")

        # ----------------------------------------------------
        # VALIDAR DIMENSIONES
        # ----------------------------------------------------

        y_fin_real = min(
            Y_FIN,
            imagen.height
        )

        if Y_INICIO >= y_fin_real:

            return []

        # ----------------------------------------------------
        # RECORTE
        # ----------------------------------------------------

        recorte = imagen.crop(
            (
                0,
                Y_INICIO,
                imagen.width,
                y_fin_real
            )
        )

        # ----------------------------------------------------
        # AMPLIAR
        # ----------------------------------------------------

        recorte = recorte.resize(
            (
                recorte.width
                * FACTOR_ESCALA,

                recorte.height
                * FACTOR_ESCALA
            ),
            Image.Resampling.LANCZOS
        )

        # ----------------------------------------------------
        # GUARDAR TEMPORALMENTE
        # ----------------------------------------------------

        ruta_temporal = (
            ruta_imagen
            + ".nu_reproceso.jpg"
        )

        recorte.save(
            ruta_temporal,
            quality=100
        )

        try:

            # ------------------------------------------------
            # SEGUNDO OCR
            # ------------------------------------------------

            resultado = self.ocr.predict(
                ruta_temporal
            )

            for pagina in resultado:

                datos = self._obtener_datos(
                    pagina
                )

                if datos is None:
                    continue

                textos = datos["textos"]
                scores = datos["scores"]
                cajas = datos["cajas"]

                for texto, score, bbox in zip(
                    textos,
                    scores,
                    cajas
                ):

                    texto = str(
                        texto
                    ).strip()

                    if not texto:
                        continue

                    # ----------------------------------------
                    # CONVERTIR BBOX A COORDENADAS ORIGINALES
                    # ----------------------------------------

                    puntos_originales = []

                    for punto in bbox:

                        x = (
                            float(punto[0])
                            / FACTOR_ESCALA
                        )

                        y = (
                            float(punto[1])
                            / FACTOR_ESCALA
                            + Y_INICIO
                        )

                        puntos_originales.append(
                            [
                                x,
                                y
                            ]
                        )

                    # ----------------------------------------
                    # CREAR DETECCIÓN
                    # ----------------------------------------

                    deteccion = self._crear_deteccion(
                        texto=texto,
                        confianza=float(score),
                        bbox=puntos_originales,
                        ancho_imagen=ancho_imagen,
                        alto_imagen=alto_imagen,
                    )

                    detecciones.append(
                        deteccion
                    )

        finally:

            # ------------------------------------------------
            # ELIMINAR ARCHIVO TEMPORAL
            # ------------------------------------------------

            try:

                if os.path.exists(
                    ruta_temporal
                ):

                    os.remove(
                        ruta_temporal
                    )

            except Exception:

                pass

        return detecciones

    # ========================================================
    # REPROCESAMIENTO REGIÓN FECHA/HORA SANTANDER
    # ========================================================

    def _reprocesar_region_santander(
        self,
        ruta_imagen,
        ancho_imagen,
        alto_imagen
    ):

        # ----------------------------------------------------
        # CONFIGURACIÓN SANTANDER
        # ----------------------------------------------------

        # Región donde normalmente aparece:
        #
        # Fecha y hora de operación
        # 31/may/26 - 09:38
        #
        # En image_339 el OCR normal detectó:
        #
        # 1/  /9:38
        #
        # Por eso solamente reprocesamos esta zona.

        Y_INICIO = 580
        Y_FIN = 730

        FACTOR_ESCALA = 4

        detecciones = []

        imagen = Image.open(
            ruta_imagen
        ).convert("RGB")

        # ----------------------------------------------------
        # VALIDAR DIMENSIONES
        # ----------------------------------------------------

        y_fin_real = min(
            Y_FIN,
            imagen.height
        )

        if Y_INICIO >= y_fin_real:

            return []

        # ----------------------------------------------------
        # RECORTE
        # ----------------------------------------------------

        recorte = imagen.crop(
            (
                0,
                Y_INICIO,
                imagen.width,
                y_fin_real
            )
        )

        # ----------------------------------------------------
        # AMPLIAR
        # ----------------------------------------------------

        recorte = recorte.resize(
            (
                recorte.width
                * FACTOR_ESCALA,

                recorte.height
                * FACTOR_ESCALA
            ),
            Image.Resampling.LANCZOS
        )

        # ----------------------------------------------------
        # GUARDAR TEMPORALMENTE
        # ----------------------------------------------------

        ruta_temporal = (
            ruta_imagen
            + ".santander_reproceso.jpg"
        )

        recorte.save(
            ruta_temporal,
            quality=100
        )

        try:

            # ------------------------------------------------
            # SEGUNDO OCR
            # ------------------------------------------------

            resultado = self.ocr.predict(
                ruta_temporal
            )

            for pagina in resultado:

                datos = self._obtener_datos(
                    pagina
                )

                if datos is None:

                    continue

                textos = datos["textos"]
                scores = datos["scores"]
                cajas = datos["cajas"]

                for texto, score, bbox in zip(
                    textos,
                    scores,
                    cajas
                ):

                    texto = str(
                        texto
                    ).strip()

                    if not texto:

                        continue

                    # ----------------------------------------
                    # CONVERTIR BBOX A COORDENADAS ORIGINALES
                    # ----------------------------------------

                    puntos_originales = []

                    for punto in bbox:

                        x = (
                            float(punto[0])
                            / FACTOR_ESCALA
                        )

                        y = (
                            float(punto[1])
                            / FACTOR_ESCALA
                            + Y_INICIO
                        )

                        puntos_originales.append(
                            [
                                x,
                                y
                            ]
                        )

                    # ----------------------------------------
                    # CREAR DETECCIÓN
                    # ----------------------------------------

                    deteccion = self._crear_deteccion(
                        texto=texto,
                        confianza=float(score),
                        bbox=puntos_originales,
                        ancho_imagen=ancho_imagen,
                        alto_imagen=alto_imagen,
                    )

                    detecciones.append(
                        deteccion
                    )

        finally:

            # ------------------------------------------------
            # ELIMINAR ARCHIVO TEMPORAL
            # ------------------------------------------------

            try:

                if os.path.exists(
                    ruta_temporal
                ):

                    os.remove(
                        ruta_temporal
                    )

            except Exception:

                pass

        return detecciones

    # ========================================================
    # REPROCESAMIENTO REGIÓN SUPERIOR KLAR
    # ========================================================

    def _reprocesar_region_klar(
        self,
        ruta_imagen,
        ancho_imagen,
        alto_imagen
    ):

        # ----------------------------------------------------
        # CONFIGURACIÓN KLAR
        # ----------------------------------------------------

        PORCENTAJE_Y_INICIO = 0.25
        PORCENTAJE_Y_FIN = 0.65

        FACTOR_ESCALA = 4

        detecciones = []

        imagen = Image.open(
            ruta_imagen
        ).convert("RGB")

        # ----------------------------------------------------
        # CALCULAR REGIÓN REAL
        # ----------------------------------------------------

        y_inicio = int(
            imagen.height
            * PORCENTAJE_Y_INICIO
        )

        y_fin = int(
            imagen.height
            * PORCENTAJE_Y_FIN
        )

        # ----------------------------------------------------
        # VALIDAR DIMENSIONES
        # ----------------------------------------------------

        y_inicio = max(
            0,
            y_inicio
        )

        y_fin_real = min(
            y_fin,
            imagen.height
        )

        if y_inicio >= y_fin_real:

            return []

        # ----------------------------------------------------
        # RECORTE
        # ----------------------------------------------------

        recorte = imagen.crop(
            (
                0,
                y_inicio,
                imagen.width,
                y_fin_real
            )
        )

        # ----------------------------------------------------
        # AMPLIAR
        # ----------------------------------------------------

        recorte = recorte.resize(
            (
                recorte.width
                * FACTOR_ESCALA,

                recorte.height
                * FACTOR_ESCALA
            ),
            Image.Resampling.LANCZOS
        )

        # ----------------------------------------------------
        # GUARDAR TEMPORALMENTE
        # ----------------------------------------------------

        ruta_temporal = (
            ruta_imagen
            + ".klar_reproceso.jpg"
        )

        recorte.save(
            ruta_temporal,
            quality=100
        )

        try:

            # ------------------------------------------------
            # SEGUNDO OCR
            # ------------------------------------------------

            resultado = self.ocr.predict(
                ruta_temporal
            )

            for pagina in resultado:

                datos = self._obtener_datos(
                    pagina
                )

                if datos is None:

                    continue

                textos = datos["textos"]
                scores = datos["scores"]
                cajas = datos["cajas"]

                for texto, score, bbox in zip(
                    textos,
                    scores,
                    cajas
                ):

                    texto = str(
                        texto
                    ).strip()

                    if not texto:

                        continue

                    # ----------------------------------------
                    # CONVERTIR BBOX
                    # A COORDENADAS ORIGINALES
                    # ----------------------------------------

                    puntos_originales = []

                    for punto in bbox:

                        x = (
                            float(
                                punto[0]
                            )
                            / FACTOR_ESCALA
                        )

                        y = (
                            float(
                                punto[1]
                            )
                            / FACTOR_ESCALA
                            + y_inicio
                        )

                        puntos_originales.append(
                            [
                                x,
                                y
                            ]
                        )

                    # ----------------------------------------
                    # CREAR DETECCIÓN
                    # ----------------------------------------

                    deteccion = self._crear_deteccion(
                        texto=texto,
                        confianza=float(score),
                        bbox=puntos_originales,
                        ancho_imagen=ancho_imagen,
                        alto_imagen=alto_imagen,
                    )

                    detecciones.append(
                        deteccion
                    )

        finally:

            # ------------------------------------------------
            # ELIMINAR TEMPORAL
            # ------------------------------------------------

            try:

                if os.path.exists(
                    ruta_temporal
                ):

                    os.remove(
                        ruta_temporal
                    )

            except Exception:

                pass

        return detecciones

    # ========================================================
    # FUSIONAR DETECCIONES KLAR
    # ========================================================

    def _fusionar_detecciones_klar(
        self,
        detecciones_originales,
        detecciones_reprocesadas
    ):
        """
        Fusiona las detecciones del OCR normal con las
        detecciones obtenidas mediante el reprocesamiento
        específico de KLAR.

        El objetivo es:

        - conservar las detecciones originales;
        - conservar detecciones nuevas encontradas por
          el segundo OCR;
        - evitar duplicar textos que representan la misma
          detección;
        - no modificar el comportamiento de otros bancos.
        """

        def normalizar_texto(texto):

            if not texto:
                return ""

            return " ".join(
                str(texto)
                .strip()
                .lower()
                .split()
            )

        def obtener_bbox(deteccion):

            if deteccion is None:
                return None

            return getattr(
                deteccion,
                "bbox",
                None
            )

        def obtener_texto(deteccion):

            if deteccion is None:
                return ""

            return getattr(
                deteccion,
                "texto",
                ""
            ) or ""

        def centro_bbox(bbox):

            if not bbox:
                return None

            try:

                xs = [
                    float(punto[0])
                    for punto in bbox
                    if len(punto) >= 2
                ]

                ys = [
                    float(punto[1])
                    for punto in bbox
                    if len(punto) >= 2
                ]

                if not xs or not ys:
                    return None

                return (
                    (min(xs) + max(xs)) / 2,
                    (min(ys) + max(ys)) / 2
                )

            except Exception:

                return None

        def distancia_centros(
            bbox1,
            bbox2
        ):

            centro1 = centro_bbox(
                bbox1
            )

            centro2 = centro_bbox(
                bbox2
            )

            if (
                centro1 is None
                or centro2 is None
            ):

                return None

            dx = (
                centro1[0]
                - centro2[0]
            )

            dy = (
                centro1[1]
                - centro2[1]
            )

            return (
                (dx ** 2)
                + (dy ** 2)
            ) ** 0.5

        # ----------------------------------------------------
        # COMENZAR CON EL OCR ORIGINAL
        # ----------------------------------------------------

        resultado = list(
            detecciones_originales
        )

        # ----------------------------------------------------
        # ANALIZAR DETECCIONES DEL RE-OCR
        # ----------------------------------------------------

        for nueva in detecciones_reprocesadas:

            texto_nuevo = normalizar_texto(
                obtener_texto(nueva)
            )

            if not texto_nuevo:

                continue

            bbox_nuevo = obtener_bbox(
                nueva
            )

            duplicada = False

            # ------------------------------------------------
            # COMPARAR CONTRA LAS YA EXISTENTES
            # ------------------------------------------------

            for existente in resultado:

                texto_existente = normalizar_texto(
                    obtener_texto(existente)
                )

                if not texto_existente:

                    continue

                bbox_existente = obtener_bbox(
                    existente
                )

                distancia = distancia_centros(
                    bbox_nuevo,
                    bbox_existente
                )

                # ------------------------------------------------
                # MISMO TEXTO
                # ------------------------------------------------

                if texto_nuevo == texto_existente:

                    if (
                        distancia is None
                        or distancia <= 80
                    ):

                        duplicada = True

                        break

                # ------------------------------------------------
                # UN TEXTO CONTIENE AL OTRO
                # ------------------------------------------------

                elif (
                    texto_nuevo in texto_existente
                    or texto_existente in texto_nuevo
                ):

                    if (
                        distancia is None
                        or distancia <= 80
                    ):

                        duplicada = True

                        break

            # ------------------------------------------------
            # SOLO AGREGAR SI ES REALMENTE NUEVA
            # ------------------------------------------------

            if not duplicada:

                resultado.append(
                    nueva
                )

        return resultado

    # ========================================================
    # PROCESAR IMAGEN ESPECÍFICO KLAR
    # ========================================================

    def procesar_imagen_klar(
        self,
        ruta_imagen: str
    ) -> ResultadoOCR:

        # ----------------------------------------------------
        # OCR NORMAL
        #
        # NO modificamos procesar_imagen().
        # ----------------------------------------------------

        resultado_normal = (
            self.procesar_imagen(
                ruta_imagen
            )
        )

        detecciones_originales = list(
            resultado_normal.detecciones
        )

        ancho_imagen = (
            resultado_normal.ancho_imagen
        )

        alto_imagen = (
            resultado_normal.alto_imagen
        )

        # ----------------------------------------------------
        # REPROCESAMIENTO EXCLUSIVO KLAR
        # ----------------------------------------------------

        detecciones_klar = (
            self._reprocesar_region_klar(
                ruta_imagen,
                ancho_imagen,
                alto_imagen
            )
        )

        # ----------------------------------------------------
        # FUSIONAR SIN DUPLICAR
        # ----------------------------------------------------

        detecciones = (
            self._fusionar_detecciones_klar(
                detecciones_originales,
                detecciones_klar
            )
        )

        # ----------------------------------------------------
        # ORDENAR
        # ----------------------------------------------------

        detecciones = (
            self._ordenar_detecciones(
                detecciones
            )
        )

        # ----------------------------------------------------
        # RECONSTRUIR LÍNEAS
        # ----------------------------------------------------

        lineas = (
            self._reconstruir_lineas(
                detecciones
            )
        )

        texto_completo = "\n".join(
            lineas
        )

        return ResultadoOCR(
            detecciones=detecciones,
            lineas=lineas,
            texto_completo=texto_completo,
            ancho_imagen=ancho_imagen,
            alto_imagen=alto_imagen,
        )



    # ========================================================
    # FARMACIAS DEL AHORRO - PROCESAMIENTO ESPECIFICO
    # ========================================================

    def procesar_imagen_farmacias(
        self,
        ruta_imagen: str
    ) -> ResultadoOCR:
        """
        Procesamiento EXCLUSIVO de FARMACIAS DEL AHORRO.

        IMPORTANTE:
        - No modifica procesar_imagen().
        - No modifica las configuraciones de otros bancos.
        - El OCR normal se ejecuta una sola vez.
        - El reproceso Farmacias reutiliza self.ocr.
        - El reproceso se limita al campo que realmente falta.
        - No se inventan valores.
        """

        import time

        inicio = time.perf_counter()

        resultado_normal = self.procesar_imagen(
            ruta_imagen
        )

        detecciones_originales = list(
            resultado_normal.detecciones
        )

        print(
            "[FARMACIAS] OCR normal: "
            f"{time.perf_counter() - inicio:.3f}s"
        )

        campos_faltantes = (
            self._farmacias_campos_faltantes(
                detecciones_originales
            )
        )

        if not campos_faltantes:

            print(
                "[FARMACIAS] Reproceso: OMITIDO | "
                "campos críticos completos"
            )

            print(
                "[FARMACIAS] Tiempo total: "
                f"{time.perf_counter() - inicio:.3f}s"
            )

            return resultado_normal

        print(
            "[FARMACIAS] Campos que requieren revisión: "
            + ", ".join(campos_faltantes)
        )

        inicio_reproceso = time.perf_counter()

        try:

            detecciones_reprocesadas = (
                self._reprocesar_farmacias_ahorro(
                    ruta_imagen,
                    resultado_normal.ancho_imagen,
                    resultado_normal.alto_imagen,
                    campos_faltantes,
                    detecciones_originales
                )
            )

        except Exception as error:

            print(
                "[FARMACIAS] Reproceso fallido. "
                "Se conserva OCR normal: "
                f"{type(error).__name__}: {error}"
            )

            return resultado_normal

        tiempo_reproceso = (
            time.perf_counter()
            - inicio_reproceso
        )

        if not detecciones_reprocesadas:

            print(
                "[FARMACIAS] Reproceso: "
                f"{tiempo_reproceso:.3f}s | "
                "sin detecciones nuevas"
            )

            return resultado_normal

        detecciones = (
            self._fusionar_detecciones_farmacias(
                detecciones_originales,
                detecciones_reprocesadas
            )
        )

        detecciones = self._ordenar_detecciones(
            detecciones
        )

        lineas = self._reconstruir_lineas(
            detecciones
        )

        texto_completo = "\n".join(
            lineas
        )

        print(
            "[FARMACIAS] Reproceso: "
            f"{tiempo_reproceso:.3f}s | "
            f"detecciones nuevas: {len(detecciones_reprocesadas)} | "
            f"Total: {time.perf_counter() - inicio:.3f}s"
        )

        return ResultadoOCR(
            detecciones=detecciones,
            lineas=lineas,
            texto_completo=texto_completo,
            ancho_imagen=resultado_normal.ancho_imagen,
            alto_imagen=resultado_normal.alto_imagen
        )

    # ========================================================
    # UTILIDADES FARMACIAS
    # ========================================================

    def _farmacias_texto(
        self,
        deteccion
    ):
        return " ".join(
            str(
                getattr(
                    deteccion,
                    "texto",
                    ""
                ) or ""
            ).strip().upper().split()
        )

    def _farmacias_rect(
        self,
        deteccion
    ):
        try:

            bbox = getattr(
                deteccion,
                "bbox",
                None
            )

            if not bbox:
                return None

            xs = [
                float(p[0])
                for p in bbox
                if len(p) >= 2
            ]

            ys = [
                float(p[1])
                for p in bbox
                if len(p) >= 2
            ]

            if not xs or not ys:
                return None

            return (
                min(xs),
                min(ys),
                max(xs),
                max(ys)
            )

        except Exception:

            return None

    def _farmacias_numero(
        self,
        texto,
        longitud_minima=1,
        longitud_maxima=30
    ):
        import re

        numeros = re.findall(
            r"\d+",
            texto
        )

        return any(
            longitud_minima <= len(numero) <= longitud_maxima
            for numero in numeros
        )

    def _farmacias_valor_derecha(
        self,
        detecciones,
        etiqueta,
        validador,
        tolerancia_y=75,
        distancia_maxima=1400
    ):
        rect_etiqueta = self._farmacias_rect(
            etiqueta
        )

        if rect_etiqueta is None:
            return False

        centro_y = (
            rect_etiqueta[1]
            + rect_etiqueta[3]
        ) / 2.0

        derecha = rect_etiqueta[2]

        for candidata in detecciones:

            if candidata is etiqueta:
                continue

            rect_candidata = self._farmacias_rect(
                candidata
            )

            if rect_candidata is None:
                continue

            texto = self._farmacias_texto(
                candidata
            )

            if not validador(texto):
                continue

            centro_y_candidata = (
                rect_candidata[1]
                + rect_candidata[3]
            ) / 2.0

            diferencia_y = abs(
                centro_y_candidata
                - centro_y
            )

            distancia_x = (
                rect_candidata[0]
                - derecha
            )

            if (
                diferencia_y <= tolerancia_y
                and distancia_x >= -40
                and distancia_x <= distancia_maxima
            ):
                return True

        return False

    def _farmacias_tiene_monto(
        self,
        detecciones
    ):
        """
        No considera cualquier importe del ticket como MONTO.

        Prioridad:
        1. MONTO + valor a la derecha.
        2. HSBC DEPOSITO... + importe cercano.
        """

        import re

        for etiqueta in detecciones:

            texto = self._farmacias_texto(
                etiqueta
            )

            if "MONTO" not in texto:
                continue

            if self._farmacias_valor_derecha(
                detecciones,
                etiqueta,
                lambda valor: bool(
                    re.search(
                        r"\$?\s*\d+(?:[.,]\d{1,2})?",
                        valor
                    )
                ),
                tolerancia_y=85,
                distancia_maxima=1600
            ):
                return True

        for bloque in detecciones:

            texto_bloque = self._farmacias_texto(
                bloque
            )

            if not (
                "HSBC" in texto_bloque
                and "DEPOSITO" in texto_bloque
                and "TARJETA" in texto_bloque
            ):
                continue

            rect_bloque = self._farmacias_rect(
                bloque
            )

            if rect_bloque is None:
                continue

            y_bloque = (
                rect_bloque[1]
                + rect_bloque[3]
            ) / 2.0

            for candidata in detecciones:

                if candidata is bloque:
                    continue

                texto = self._farmacias_texto(
                    candidata
                )

                if not re.search(
                    r"\$?\s*\d+(?:[.,]\d{2})",
                    texto
                ):
                    continue

                rect_candidata = self._farmacias_rect(
                    candidata
                )

                if rect_candidata is None:
                    continue

                y_candidata = (
                    rect_candidata[1]
                    + rect_candidata[3]
                ) / 2.0

                distancia_x = (
                    rect_candidata[0]
                    - rect_bloque[2]
                )

                if (
                    abs(y_candidata - y_bloque) <= 90
                    and -50 <= distancia_x <= 2500
                ):
                    return True

        return False

    def _farmacias_campos_faltantes(
        self,
        detecciones
    ):
        """
        Determina exactamente qué campo crítico necesita
        reprocesamiento.

        Esta función es EXCLUSIVA de Farmacias.
        """

        import re

        tiene_transaccion = False
        tiene_autorizacion = False
        tiene_referencia = False
        tiene_deposito = False
        tiene_monto = self._farmacias_tiene_monto(
            detecciones
        )

        # ----------------------------------------------------
        # TRANSACCION
        # ----------------------------------------------------

        for etiqueta in detecciones:

            texto = self._farmacias_texto(
                etiqueta
            )

            if "TRANSACC" not in texto:
                continue

            if self._farmacias_valor_derecha(
                detecciones,
                etiqueta,
                lambda valor: self._farmacias_numero(
                    valor,
                    10,
                    10
                ),
                tolerancia_y=85,
                distancia_maxima=1600
            ):
                tiene_transaccion = True
                break

        # ----------------------------------------------------
        # AUTORIZACION
        # ----------------------------------------------------

        for etiqueta in detecciones:

            texto = self._farmacias_texto(
                etiqueta
            )

            if "AUTORIZ" not in texto:
                continue

            if self._farmacias_valor_derecha(
                detecciones,
                etiqueta,
                lambda valor: self._farmacias_numero(
                    valor,
                    6,
                    6
                ),
                tolerancia_y=85,
                distancia_maxima=1600
            ):
                tiene_autorizacion = True
                break

        # ----------------------------------------------------
        # REFERENCIA
        # ----------------------------------------------------

        for deteccion in detecciones:

            texto = self._farmacias_texto(
                deteccion
            )

            if re.search(
                r"2278\s*$",
                texto
            ):
                tiene_referencia = True
                break

        # ----------------------------------------------------
        # DEPOSITO
        # ----------------------------------------------------

        textos = [
            self._farmacias_texto(
                deteccion
            )
            for deteccion in detecciones
        ]

        texto_global = " ".join(
            textos
        )

        if (
            "DEPOSITO" in texto_global
            and "HSBC" in texto_global
        ):
            tiene_deposito = True

        faltantes = []

        if not tiene_transaccion:
            faltantes.append("transaccion")

        if not tiene_autorizacion:
            faltantes.append("autorizacion")

        if not tiene_referencia:
            faltantes.append("referencia")

        if not tiene_deposito:
            faltantes.append("deposito")

        if not tiene_monto:
            faltantes.append("monto")

        return faltantes

    # ========================================================
    # REPROCESAMIENTO FARMACIAS
    # ========================================================

    def _reprocesar_farmacias_ahorro(
        self,
        ruta_imagen,
        ancho_imagen,
        alto_imagen,
        campos_faltantes=None,
        detecciones_originales=None
    ):
        """
        OCR regional EXCLUSIVO de Farmacias.

        CAMBIO IMPORTANTE:
        Ya no procesa 45%-86% de la imagen completa.

        Cuando falta TRANSACCION se procesa solamente la franja
        donde está TRANSACCION, usando AUTORIZACION como ancla
        si la etiqueta TRANSACCION no fue reconocida.

        Para otros campos faltantes se utiliza únicamente el bloque
        crítico de datos bancarios.

        Se reutiliza self.ocr, por lo que NO se crea un segundo
        modelo PaddleOCR.
        """

        import cv2
        import numpy as np

        if detecciones_originales is None:
            detecciones_originales = []

        if campos_faltantes is None:
            campos_faltantes = [
                "transaccion",
                "autorizacion",
                "referencia",
                "deposito",
                "monto"
            ]

        imagen = cv2.imread(
            ruta_imagen,
            cv2.IMREAD_COLOR
        )

        if imagen is None:
            return []

        altura, ancho = imagen.shape[:2]

        # ----------------------------------------------------
        # DETERMINAR REGION CRITICA
        # ----------------------------------------------------

        x_inicio = 0
        x_fin = ancho

        y_inicio = None
        y_fin = None

        # Primero buscamos TRANSACCION.
        deteccion_transaccion = None

        for deteccion in detecciones_originales:

            texto = self._farmacias_texto(
                deteccion
            )

            if "TRANSACC" in texto:

                deteccion_transaccion = (
                    deteccion
                )

                break

        # Si no existe TRANSACCION, AUTORIZACION sirve como ancla.
        deteccion_autorizacion = None

        for deteccion in detecciones_originales:

            texto = self._farmacias_texto(
                deteccion
            )

            if "AUTORIZ" in texto:

                deteccion_autorizacion = (
                    deteccion
                )

                break

        # ----------------------------------------------------
        # CASO 1: SOLO TRANSACCION FALTA
        # ----------------------------------------------------

        if (
            campos_faltantes == ["transaccion"]
            or (
                "transaccion" in campos_faltantes
                and len(campos_faltantes) == 1
            )
        ):

            if deteccion_transaccion is not None:

                rect = self._farmacias_rect(
                    deteccion_transaccion
                )

                if rect is not None:

                    y_inicio = int(
                        rect[1] - max(
                            35,
                            (rect[3] - rect[1]) * 1.8
                        )
                    )

                    y_fin = int(
                        rect[3]
                        + max(
                            85,
                            (rect[3] - rect[1]) * 2.8
                        )
                    )

            elif deteccion_autorizacion is not None:

                rect = self._farmacias_rect(
                    deteccion_autorizacion
                )

                if rect is not None:

                    alto_linea = max(
                        25,
                        rect[3] - rect[1]
                    )

                    y_inicio = int(
                        rect[1]
                        - alto_linea * 4.5
                    )

                    y_fin = int(
                        rect[1]
                        - alto_linea * 0.5
                    )

            else:

                # Último recurso: zona inferior aproximada.
                y_inicio = int(
                    altura * 0.62
                )

                y_fin = int(
                    altura * 0.74
                )

        else:

            # ------------------------------------------------
            # CASO 2: UNO O VARIOS CAMPOS CRITICOS
            # ------------------------------------------------

            anclas = []

            for deteccion in detecciones_originales:

                texto = self._farmacias_texto(
                    deteccion
                )

                if any(
                    palabra in texto
                    for palabra in (
                        "TRANSACC",
                        "AUTORIZ",
                        "REFERENCIA",
                        "DEPOSITO",
                        "MONTO",
                        "EFECTIVO"
                    )
                ):

                    rect = self._farmacias_rect(
                        deteccion
                    )

                    if rect is not None:
                        anclas.append(rect)

            if anclas:

                y_inicio = int(
                    min(
                        rect[1]
                        for rect in anclas
                    )
                    - 45
                )

                y_fin = int(
                    max(
                        rect[3]
                        for rect in anclas
                    )
                    + 100
                )

            else:

                y_inicio = int(
                    altura * 0.58
                )

                y_fin = int(
                    altura * 0.82
                )

        y_inicio = max(
            0,
            min(
                y_inicio if y_inicio is not None else 0,
                altura - 1
            )
        )

        y_fin = max(
            y_inicio + 1,
            min(
                y_fin if y_fin is not None else altura,
                altura
            )
        )

        recorte = imagen[
            y_inicio:y_fin,
            x_inicio:x_fin
        ]

        if recorte.size == 0:
            return []

        print(
            "[FARMACIAS] Región OCR: "
            f"x={x_inicio}:{x_fin} "
            f"y={y_inicio}:{y_fin} "
            f"campos={','.join(campos_faltantes)}"
        )

        # ----------------------------------------------------
        # PREPROCESAMIENTO ESPECIFICO
        # ----------------------------------------------------

        gris = cv2.cvtColor(
            recorte,
            cv2.COLOR_BGR2GRAY
        )

        clahe = cv2.createCLAHE(
            clipLimit=2.0,
            tileGridSize=(8, 8)
        )

        mejorada = clahe.apply(
            gris
        )

        # Un poco de suavizado para ruido de fotografía.
        mejorada = cv2.GaussianBlur(
            mejorada,
            (3, 3),
            0
        )

        # ----------------------------------------------------
        # ESCALA
        # ----------------------------------------------------

        factor = 3.0

        max_lado = max(
            mejorada.shape[1],
            mejorada.shape[0]
        )

        if max_lado * factor > 3200:

            factor = (
                3200
                / max_lado
            )

        factor = max(
            1.5,
            factor
        )

        nuevo_ancho = max(
            1,
            int(
                mejorada.shape[1]
                * factor
            )
        )

        nuevo_alto = max(
            1,
            int(
                mejorada.shape[0]
                * factor
            )
        )

        procesada = cv2.resize(
            mejorada,
            (
                nuevo_ancho,
                nuevo_alto
            ),
            interpolation=cv2.INTER_CUBIC
        )

        ruta_temporal = (
            ruta_imagen
            + ".farmacias_regional.png"
        )

        detecciones = []

        try:

            guardada = cv2.imwrite(
                ruta_temporal,
                procesada,
                [
                    cv2.IMWRITE_PNG_COMPRESSION,
                    1
                ]
            )

            if not guardada:
                return []

            # ------------------------------------------------
            # REUTILIZAR EL MISMO MODELO OCR
            # ------------------------------------------------

            resultado = self.ocr.predict(
                ruta_temporal
            )

            for pagina in resultado:

                datos = self._obtener_datos(
                    pagina
                )

                if datos is None:
                    continue

                textos = datos["textos"]
                scores = datos["scores"]
                cajas = datos["cajas"]

                for texto, score, bbox in zip(
                    textos,
                    scores,
                    cajas
                ):

                    texto = str(
                        texto
                    ).strip()

                    if not texto:
                        continue

                    puntos = []

                    for punto in bbox:

                        x = (
                            float(punto[0])
                            / factor
                            + x_inicio
                        )

                        y = (
                            float(punto[1])
                            / factor
                            + y_inicio
                        )

                        puntos.append(
                            [
                                x,
                                y
                            ]
                        )

                    if not puntos:
                        continue

                    detecciones.append(
                        self._crear_deteccion(
                            texto=texto,
                            confianza=float(score),
                            bbox=puntos,
                            ancho_imagen=ancho_imagen,
                            alto_imagen=alto_imagen
                        )
                    )

        except Exception as error:

            print(
                "[FARMACIAS] Error OCR regional: "
                f"{type(error).__name__}: {error}"
            )

        finally:

            try:

                if os.path.exists(
                    ruta_temporal
                ):
                    os.remove(
                        ruta_temporal
                    )

            except Exception:
                pass

        return detecciones

    # ========================================================
    # FUSIONAR DETECCIONES FARMACIAS
    # ========================================================

    def _fusionar_detecciones_farmacias(
        self,
        detecciones_originales,
        detecciones_reprocesadas
    ):
        """
        Fusion EXCLUSIVA de Farmacias.

        No reemplaza automáticamente una detección original.
        Agrega información nueva para que el extractor pueda
        seleccionar el valor correcto.
        """

        resultado = list(
            detecciones_originales
        )

        def texto(deteccion):

            return " ".join(
                str(
                    getattr(
                        deteccion,
                        "texto",
                        ""
                    ) or ""
                )
                .strip()
                .upper()
                .split()
            )

        def centro(deteccion):

            rect = self._farmacias_rect(
                deteccion
            )

            if rect is None:
                return None

            return (
                (
                    rect[0]
                    + rect[2]
                ) / 2.0,
                (
                    rect[1]
                    + rect[3]
                ) / 2.0
            )

        for nueva in detecciones_reprocesadas:

            texto_nuevo = texto(
                nueva
            )

            if not texto_nuevo:
                continue

            centro_nuevo = centro(
                nueva
            )

            duplicada = False

            for existente in resultado:

                if texto_nuevo != texto(
                    existente
                ):
                    continue

                centro_existente = centro(
                    existente
                )

                if (
                    centro_nuevo is None
                    or centro_existente is None
                ):

                    duplicada = True
                    break

                distancia = (
                    (
                        centro_nuevo[0]
                        - centro_existente[0]
                    ) ** 2
                    +
                    (
                        centro_nuevo[1]
                        - centro_existente[1]
                    ) ** 2
                ) ** 0.5

                if distancia <= 80:

                    duplicada = True
                    break

            if not duplicada:

                resultado.append(
                    nueva
                )

        return resultado

    # ========================================================
    # ESTIMAR INCLINACION FARMACIAS
    # ========================================================

    def _farmacias_estimar_inclinacion(
        self,
        imagen
    ):
        return 0.0

    # ========================================================
    # OBTENER DATOS
    # ========================================================

    def _obtener_datos(
        self,
        pagina
    ):

        textos = None
        scores = None
        cajas = None

        # ----------------------------------------------------
        # PaddleOCR 3.x
        # ----------------------------------------------------

        if hasattr(
            pagina,
            "rec_texts"
        ):

            textos = pagina.rec_texts

        if hasattr(
            pagina,
            "rec_scores"
        ):

            scores = pagina.rec_scores

        if hasattr(
            pagina,
            "rec_polys"
        ):

            cajas = pagina.rec_polys

        # ----------------------------------------------------
        # DICCIONARIO
        # ----------------------------------------------------

        if isinstance(
            pagina,
            dict
        ):

            textos = pagina.get(
                "rec_texts",
                textos
            )

            scores = pagina.get(
                "rec_scores",
                scores
            )

            cajas = pagina.get(
                "rec_polys",
                cajas
            )

        if textos is None or cajas is None:

            return None

        if scores is None:

            scores = [
                1.0
                for _ in textos
            ]

        ancho, alto = (
            self._obtener_dimensiones(
                pagina,
                cajas
            )
        )

        return {
            "textos": textos,
            "scores": scores,
            "cajas": cajas,
            "ancho": ancho,
            "alto": alto,
        }

    # ========================================================
    # DIMENSIONES
    # ========================================================

    def _obtener_dimensiones(
        self,
        pagina,
        cajas
    ):

        for atributo in (
            "input_img",
            "img"
        ):

            imagen = getattr(
                pagina,
                atributo,
                None
            )

            if imagen is not None:

                try:

                    alto, ancho = (
                        imagen.shape[:2]
                    )

                    return (
                        int(ancho),
                        int(alto)
                    )

                except Exception:

                    pass

        max_x = 0
        max_y = 0

        for bbox in cajas:

            for punto in bbox:

                if len(punto) >= 2:

                    max_x = max(
                        max_x,
                        float(punto[0])
                    )

                    max_y = max(
                        max_y,
                        float(punto[1])
                    )

        return (
            int(max_x),
            int(max_y)
        )

    # ========================================================
    # CREAR DETECCIÓN
    # ========================================================

    def _crear_deteccion(
        self,
        texto,
        confianza,
        bbox,
        ancho_imagen,
        alto_imagen,
    ):

        puntos = [
            [
                float(punto[0]),
                float(punto[1])
            ]
            for punto in bbox
        ]

        xs = [
            punto[0]
            for punto in puntos
        ]

        ys = [
            punto[1]
            for punto in puntos
        ]

        x = min(xs)
        y = min(ys)

        x_max = max(xs)
        y_max = max(ys)

        ancho = (
            x_max - x
        )

        alto = (
            y_max - y
        )

        ancho_seguro = max(
            ancho_imagen,
            1
        )

        alto_seguro = max(
            alto_imagen,
            1
        )

        return OCRDeteccion(
            texto=texto,
            confianza=confianza,

            bbox=puntos,

            x=x,
            y=y,

            ancho=ancho,
            alto=alto,

            x_rel=(
                x
                / ancho_seguro
            ),

            y_rel=(
                y
                / alto_seguro
            ),

            ancho_rel=(
                ancho
                / ancho_seguro
            ),

            alto_rel=(
                alto
                / alto_seguro
            ),
        )

    # ========================================================
    # ORDENAR DETECCIONES
    # ========================================================

    def _ordenar_detecciones(
        self,
        detecciones
    ):

        return sorted(
            detecciones,
            key=lambda d: (
                d.y,
                d.x
            )
        )

    # ========================================================
    # RECONSTRUIR LÍNEAS
    # ========================================================

    def _reconstruir_lineas(
        self,
        detecciones
    ):

        if not detecciones:

            return []

        altura_promedio = (
            sum(
                d.alto
                for d in detecciones
            )
            / len(detecciones)
        )

        tolerancia_y = max(
            altura_promedio * 0.6,
            5
        )

        grupos = []

        for deteccion in detecciones:

            grupo_encontrado = None

            for grupo in grupos:

                promedio_y = (
                    sum(
                        d.y
                        for d in grupo
                    )
                    / len(grupo)
                )

                if abs(
                    deteccion.y
                    - promedio_y
                ) <= tolerancia_y:

                    grupo_encontrado = grupo

                    break

            if grupo_encontrado is None:

                grupos.append(
                    [
                        deteccion
                    ]
                )

            else:

                grupo_encontrado.append(
                    deteccion
                )

        lineas = []

        for grupo in grupos:

            grupo.sort(
                key=lambda d: d.x
            )

            texto = " ".join(
                d.texto
                for d in grupo
            )

            texto = " ".join(
                texto.split()
            )

            if texto:

                lineas.append(
                    texto
                )

        return lineas