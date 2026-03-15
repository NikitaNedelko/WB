from __future__ import annotations

from pathlib import Path
from typing import Any

from wb.api import fetch_card_live
from wb.models import BuildStats
from wb.transform import build_row, filter_rows
from wb.utils import to_int
from wb.xlsx_writer import write_xlsx


def build_catalog_rows(
    products: list[dict[str, Any]],
    source: str,
    examples_cards_map: dict[int, dict[str, Any]],
    card_delay: float,
) -> tuple[list[dict[str, Any]], BuildStats]:
    host_cache: dict[int, int] = {}
    rows: list[dict[str, Any]] = []

    stats = BuildStats(total_products=len(products), source=source)

    for item in products:
        nm_id = to_int(item.get("id"))
        if nm_id is None:
            continue

        card: dict[str, Any] | None = None
        base_url: str | None = None

        if source == "live":
            live_card, live_base = fetch_card_live(nm_id, host_cache=host_cache, request_delay=card_delay)
            card = live_card
            base_url = live_base
            if card is None:
                stats.card_errors += 1
        else:
            card = examples_cards_map.get(nm_id)

        if card is None:
            stats.missing_cards += 1
            card = {}

        rows.append(build_row(item, card, base_url))

    stats.built_rows = len(rows)
    return rows, stats


def save_outputs(output_dir: Path, all_rows: list[dict[str, Any]]) -> tuple[Path, Path, list[dict[str, Any]]]:
    filtered_rows = filter_rows(all_rows)

    full_path = output_dir / "catalog_full.xlsx"
    filtered_path = output_dir / "catalog_filtered.xlsx"

    write_xlsx(full_path, all_rows)
    write_xlsx(filtered_path, filtered_rows)

    return full_path, filtered_path, filtered_rows
