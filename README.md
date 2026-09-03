Instalación de Paddle OCR 

1. Abrir tu proyecto en VS Code
Abre VS Code y abre tu proyecto:
C:\Users\user_name\OneDrive\Subcarpeta\Ocr_paddle

Después abre:
Terminal -> New Terminal

Debe aparecer algo parecido a:
PS C:\Users\user_name\OneDrive\Escritorio\Ocr_paddle>

2. Comprobar Python

En la terminal ejecuta:

python --version (Verifica versión de python)

También:

python -m pip --version (Verifica la versión instalada de PIP)

Una vez que verficaste la version de python, la versión ocupada en este proyecto fue Python 3.13.15.

Versión Ocupada:
Python 3.13.15

Link para descargar Python 3.13.15:

https://www.python.org/downloads/release/python-31315/


Idealmente tendrás una versión de Python compatible con la versión de PaddlePaddle que vayamos a instalar.


3. Instalar PaddlePaddle

Aquí es importante separar PaddlePaddle de PaddleOCR. 

PaddleOCR depende de PaddlePaddle.

Para CPU podemos instalar PaddlePaddle y posteriormente PaddleOCR.

Primero:

python -m pip install paddlepaddle

Deja que termine.

4. Comprobar PaddlePaddle

Ejecuta:

python -c "import paddle; print(paddle.__version__)"


Debe mostrar una versión, por ejemplo:

3.3.1

Después:

python -c "import paddle; paddle.utils.run_check()"

Si todo está correcto debería terminar indicando que la instalación pasó la comprobación, por ejemplo:

PaddlePaddle is installed successfully!

La comprobación mediante paddle.utils.run_check() es también una de las formas recomendadas por la documentación de Paddle para verificar la instalación.

5. Instalar PaddleOCR

Coloca en Power shell:


python -m pip install paddleocr

Deja que termine.

6. Comprobar PaddleOCR
   
Ejecuta:

python -c "from paddleocr import PaddleOCR; print('PaddleOCR instalado correctamente')"

Si aparece:

PaddleOCR instalado correctamente

ya tenemos la librería funcionando.

7. Instalar OpenCV

Para el de Ocr_paddle también necesitamos OpenCV:

python -m pip install opencv-python

Y:

python -c "import cv2; print(cv2.__version__)"

8. Instalar las librerías que normalmente usaremos

Para tu proyecto también puedes dejar instaladas:

python -m pip install numpy pillow

Y comprobar:

python -c "import numpy; import PIL; print('NumPy y Pillow OK')"

