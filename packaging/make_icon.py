from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QGuiApplication, QImage, QImageReader

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "packaging" / "assets" / "FB-BINGO.svg"
ICO = ROOT / "packaging" / "assets" / "FB-BINGO.ico"
PNG = ROOT / "packaging" / "assets" / "FB-BINGO.png"

app = QGuiApplication.instance() or QGuiApplication([])
reader = QImageReader(str(SVG))
reader.setAutoTransform(True)
reader.setScaledSize(QSize(1024, 1024))
image = reader.read()
if image.isNull():
    raise SystemExit(f"No se pudo rasterizar {SVG}: {reader.errorString()}")
image = image.convertToFormat(QImage.Format.Format_RGBA8888)
if not image.save(str(PNG), "PNG"):
    raise SystemExit(f"No se pudo generar {PNG}")

pil = Image.open(PNG).convert("RGBA")
pil.save(ICO, format="ICO", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print(f"Icono generado: {ICO}")
