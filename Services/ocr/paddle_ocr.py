from dataclasses import dataclass
from typing import List, Optional
import os


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

    def _crear_ocr(self):

       from paddleocr import PaddleOCR

       return PaddleOCR(
        lang=self.idioma,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=True,
        enable_mkldnn=False,
    )

    def procesar_imagen(self, ruta_imagen: str) -> ResultadoOCR:

        if not os.path.isfile(ruta_imagen):
            raise FileNotFoundError(
                f"No existe la imagen: {ruta_imagen}"
            )

        resultado = self.ocr.predict(ruta_imagen)

        detecciones = []

        ancho_imagen = 0
        alto_imagen = 0

        for pagina in resultado:

            datos = self._obtener_datos(pagina)

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

                texto = str(texto).strip()

                if not texto:
                    continue

                deteccion = self._crear_deteccion(
                    texto=texto,
                    confianza=float(score),
                    bbox=bbox,
                    ancho_imagen=ancho_imagen,
                    alto_imagen=alto_imagen,
                )

                detecciones.append(deteccion)

        detecciones = self._ordenar_detecciones(
            detecciones
        )

        lineas = self._reconstruir_lineas(
            detecciones
        )

        texto_completo = "\n".join(lineas)

        return ResultadoOCR(
            detecciones=detecciones,
            lineas=lineas,
            texto_completo=texto_completo,
            ancho_imagen=ancho_imagen,
            alto_imagen=alto_imagen,
        )

    def _obtener_datos(self, pagina):

        textos = None
        scores = None
        cajas = None

        # PaddleOCR 3.x
        if hasattr(pagina, "rec_texts"):
            textos = pagina.rec_texts

        if hasattr(pagina, "rec_scores"):
            scores = pagina.rec_scores

        if hasattr(pagina, "rec_polys"):
            cajas = pagina.rec_polys

        # En caso de que el resultado sea tipo diccionario
        if isinstance(pagina, dict):

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
            scores = [1.0] * len(textos)

        ancho, alto = self._obtener_dimensiones(
            pagina,
            cajas
        )

        return {
            "textos": textos,
            "scores": scores,
            "cajas": cajas,
            "ancho": ancho,
            "alto": alto,
        }

    def _obtener_dimensiones(
        self,
        pagina,
        cajas
    ):

        # Intentar obtener dimensiones desde PaddleOCR
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
                    alto, ancho = imagen.shape[:2]

                    return int(ancho), int(alto)

                except Exception:
                    pass

        # Como respaldo usamos las coordenadas
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

        return int(max_x), int(max_y)

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

        ancho = x_max - x
        alto = y_max - y

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

            x_rel=x / ancho_seguro,
            y_rel=y / alto_seguro,
            ancho_rel=ancho / ancho_seguro,
            alto_rel=alto / alto_seguro,
        )

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

    def _reconstruir_lineas(
        self,
        detecciones
    ):

        if not detecciones:
            return []

        altura_promedio = sum(
            d.alto
            for d in detecciones
        ) / len(detecciones)

        tolerancia_y = max(
            altura_promedio * 0.6,
            5
        )

        grupos = []

        for deteccion in detecciones:

            grupo_encontrado = None

            for grupo in grupos:

                promedio_y = sum(
                    d.y
                    for d in grupo
                ) / len(grupo)

                if abs(
                    deteccion.y - promedio_y
                ) <= tolerancia_y:

                    grupo_encontrado = grupo
                    break

            if grupo_encontrado is None:

                grupos.append(
                    [deteccion]
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

                lineas.append(texto)

        return lineas