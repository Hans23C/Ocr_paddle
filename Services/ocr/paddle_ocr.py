from dataclasses import dataclass
from typing import List
import os

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