from __future__ import annotations


def test_designer_exposes_reference_sections_and_live_preview():
    from app.ui.designer_window import DesignerWindow

    window = DesignerWindow()
    assert window.section_buttons_text() == [
        "General",
        "Colores",
        "Logo",
        "Numeración",
        "QR y Seguridad",
        "Texto inferior",
        "Tamaño",
        "Vista previa",
    ]
    assert window.preview_is_real_card()
    assert window.preview_has_grid(3, 9)


def test_designer_preview_uses_print_style_and_hides_internal_model():
    from app.ui.designer_window import DesignerWindow

    window = DesignerWindow()
    window.set_preview_card_number("11534")
    svg = window.preview_svg()

    assert "11534" in svg
    assert "MODELO" not in svg
    assert "FB-BINGO" in svg
    assert "BINGO DE 90 BOLAS" in svg


def test_designer_has_saved_default_visual_identity():
    from app.ui.designer_window import DesignerWindow

    window = DesignerWindow()
    design = window.current_design()

    assert design["accent"] == "#FF4FA3"
    assert design["secondary_accent"] == "#8FD9FF"
    assert design["empty"] == "#F7DDE7"
    assert design["show_model"] is False
