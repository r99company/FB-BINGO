from app.ui.public_display import format_ball_count, next_prize_label


def test_ball_count_is_compact_and_shows_ninety_ball_limit():
    assert format_ball_count(5) == "5 / 90"
    assert format_ball_count(0) == "0 / 90"
    assert format_ball_count(90) == "90 / 90"


def test_prize_label_starts_at_line_and_switches_to_bingo():
    assert next_prize_label(False) == "LÍNEA"
    assert next_prize_label(True) == "BINGO"
