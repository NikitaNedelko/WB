from __future__ import annotations

import json
from pathlib import Path

from wb.api import extract_products
from wb.utils import to_int


def load_examples_products(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return []
    return extract_products(data)


def load_examples_cards(path: Path) -> dict[int, dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))

    cards: list[dict[str, object]] = []
    if isinstance(data, dict):
        if isinstance(data.get("cards"), list):
            cards = [item for item in data["cards"] if isinstance(item, dict)]
        elif data.get("nm_id") is not None:
            cards = [data]
    elif isinstance(data, list):
        cards = [item for item in data if isinstance(item, dict)]

    result: dict[int, dict[str, object]] = {}
    for card in cards:
        nm_id = to_int(card.get("nm_id"))
        if nm_id is not None:
            result[nm_id] = card
    return result
