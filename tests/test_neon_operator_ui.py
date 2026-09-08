import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.main import BingoMainWindow
from app.ui.main_window import TVWindow


def _texts(window):
    return [widget.text() for widget in window.findChildren(type(window.current_label)) if widget.text()]


def test_operator_window_has_approved_layout_and_90_ball_board():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    window.show()
    app.processEvents()

    assert window.windowTitle() == "FB-BINGO — Sala de Juego"
    assert window.minimumSize().width() == 1200
    assert len(window._buttons) == 90
    assert window.current_label.objectName() == "CurrentBall"
    assert window.count_label.text() == "0 / 90"
    assert window.ball_input.placeholderText() == "1–90"
    assert window.ball_input.hasFocus()
    labels = _texts(window)
    assert "CONTROLES DEL JUEGO" not in labels
    assert "INFORMACIÓN GENERAL" not in labels
    assert "PRÓXIMO PREMIO" not in labels
    assert "PREMIOS" not in labels

    window.close()
    app.processEvents()


def test_manual_ball_entry_updates_board_and_rejects_duplicates_and_invalid_values():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()

    window.ball_input.setText("47")
    assert window.enter_ball() is True
    assert window.game.history == (47,)
    assert window.current_label.text() == "47"
    assert window.count_label.text() == "1 / 90"
    assert window._buttons[47].property("called") is True
    assert window._buttons[47].property("current") is True

    window.ball_input.setText("47")
    assert window.enter_ball() is False
    assert window.game.history == (47,)

    window.ball_input.setText("91")
    assert window.enter_ball() is False
    assert window.game.history == (47,)

    window.ball_input.setText("0")
    assert window.enter_ball() is False
    assert window.game.history == (47,)

    window.ball_input.setText("abc")
    assert window.enter_ball() is False
    assert window.game.history == (47,)

    window.close()
    app.processEvents()


def test_manual_ball_entry_is_blocked_while_game_is_paused():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()

    window.toggle_pause()
    window.ball_input.setText("47")

    assert window.enter_ball() is False
    assert window.game.history == ()
    assert window.game.state.paused is True
    assert "PAUSADA" in window.ball_message.text()

    window.close()
    app.processEvents()


def test_sales_navigation_is_connected_to_operational_sales_window():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    sales_buttons = [button for button in window.findChildren(type(window.pause_button)) if button.text().startswith("🛒  VENTAS")]
    assert len(sales_buttons) == 1
    assert hasattr(window, "open_sales")
    window.close()
    app.processEvents()


def test_operator_controls_use_history_wrappers_when_clicked():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()

    window.ball_input.setText("47")
    enter_buttons = [button for button in window.findChildren(type(window.pause_button)) if button.text() == "ENTER"]
    assert len(enter_buttons) == 1
    enter_buttons[0].click()
    app.processEvents()
    assert window.game.history == (47,)
    assert window.history_repository.get_game(window.history_game_id)["called_numbers"] == (47,)

    window.close()
    app.processEvents()


def test_tv_window_has_public_90_ball_board_and_compact_counter():
    app = QApplication.instance() or QApplication([])
    window = TVWindow()
    assert len(window.board_buttons) == 90
    window.update_game(25, (10, 18, 24, 3, 25))
    assert window.number.text() == "25"
    assert window.count.text() == "5 / 90"
    assert window.board_buttons[25].property("current") is True
    assert window.board_buttons[10].property("called") is True
    window.close()
    app.processEvents()
