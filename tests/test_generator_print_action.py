from PySide6.QtWidgets import QApplication, QPushButton

from app.ui.generator_window import GeneratorWidget


def test_generator_has_real_a4_print_button():
    app = QApplication.instance() or QApplication([])
    window = GeneratorWidget(max_cards=30_000)
    buttons = {button.text() for button in window.findChildren(QPushButton)}
    assert "IMPRIMIR A4" in buttons
    window.close()
    app.quit()
