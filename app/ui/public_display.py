"""Helpers for the clean public-facing Bingo display."""


TOTAL_BALLS = 90


def format_ball_count(count: int) -> str:
    """Return the compact public counter used on the operator screen."""
    if not 0 <= count <= TOTAL_BALLS:
        raise ValueError("count must be between 0 and 90")
    return f"{count} / {TOTAL_BALLS}"


def next_prize_label(line_completed: bool) -> str:
    """Return the next prize stage without exposing prize amounts."""
    return "BINGO" if line_completed else "LÍNEA"
