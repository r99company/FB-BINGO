from __future__ import annotations

from collections.abc import Iterator


def iter_a4_series_batches(
    first_series: int,
    series_count: int,
    *,
    duplicate: bool = False,
) -> Iterator[tuple[int, int | None]]:
    """Yield the series placed on each A4 sheet.

    A normal sheet contains two consecutive six-card series, one per column.
    With ``duplicate=True`` the same series is placed in both columns so the
    exact six cards are physically repeated without regenerating them.
    """
    if first_series < 1:
        raise ValueError("La serie inicial debe ser positiva")
    if series_count < 1:
        raise ValueError("La cantidad de series debe ser positiva")

    current = first_series
    remaining = series_count
    while remaining:
        if duplicate:
            yield current, current
            current += 1
            remaining -= 1
            continue

        right = current + 1 if remaining > 1 else None
        yield current, right
        current += 2
        remaining -= 2 if right is not None else 1
