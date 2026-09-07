from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "packaging" / "assets" / "FB-BINGO.svg"
ICO = ROOT / "packaging" / "assets" / "FB-BINGO.ico"
PNG = ROOT / "packaging" / "assets" / "FB-BINGO.png"

app = QGuiApplication.instance() or QGuiApplication([])
renderer = QSvgRenderer(str(SVG))
if not renderer.isValid():
    raise SystemExit(f"No se pudo cargar el logo SVG: {SVG}")

image = QImage(QSize(1024, 1024), QImage.Format.Format_RGBA8888)
image.fill(Qt.GlobalColor.transparent)
painter = QPainter(image)
renderer.render(painter)
painter.end()
if image.isNull() or not image.save(str(PNG), "PNG"):
    raise SystemExit(f"No se pudo generar {PNG}")

pil = Image.open(PNG).convert("RGBA")
pil.save(ICO, format="ICO", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print(f"Icono generado: {ICO}")
