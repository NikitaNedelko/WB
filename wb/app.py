from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from wb.api import fetch_search_catalog
from wb.constants import DEFAULT_OUTPUT_DIR, DEFAULT_QUERY
from wb.pipeline import build_catalog_rows, save_outputs
from wb.sources import load_examples_cards, load_examples_products


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WB catalog collector to XLSX")
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--source", choices=["auto", "live", "examples"], default="auto")
    parser.add_argument("--max-pages", type=int, default=50)
    parser.add_argument("--search-delay", type=float, default=0.35)
    parser.add_argument("--card-delay", type=float, default=0.02)
    parser.add_argument("--max-products", type=int, default=0, help="0 means no limit")
    return parser.parse_args()


def select_products(
    source_mode: str,
    query: str,
    max_pages: int,
    search_delay: float,
    examples_products_path: Path,
) -> tuple[list[dict[str, Any]], str]:
    source_used = source_mode
    products: list[dict[str, Any]] = []

    if source_mode in {"auto", "live"}:
        try:
            products = fetch_search_catalog(
                query=query,
                max_pages=max(1, max_pages),
                request_delay=max(0.0, search_delay),
            )
            source_used = "live"
        except RuntimeError:
            if source_mode == "live":
                raise

    if not products:
        products = load_examples_products(examples_products_path)
        source_used = "examples"

    return products, source_used


def main() -> None:
    args = parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    examples_products_path = repo_root / "examples_json" / "products.json"
    examples_cards_path = repo_root / "examples_json" / "cards.json"
    output_dir = (repo_root / args.output_dir).resolve()

    examples_cards_map = load_examples_cards(examples_cards_path)

    products, source_used = select_products(
        source_mode=args.source,
        query=args.query,
        max_pages=args.max_pages,
        search_delay=args.search_delay,
        examples_products_path=examples_products_path,
    )

    if args.max_products and args.max_products > 0:
        products = products[: args.max_products]

    all_rows, stats = build_catalog_rows(
        products=products,
        source=source_used,
        examples_cards_map=examples_cards_map,
        card_delay=max(0.0, args.card_delay),
    )

    full_path, filtered_path, filtered_rows = save_outputs(output_dir, all_rows)

    print(f"Source mode: {source_used}")
    print(f"Products fetched: {stats.total_products}")
    print(f"Rows written: {stats.built_rows}")
    print(f"Missing cards: {stats.missing_cards}")
    print(f"Card fetch errors: {stats.card_errors}")
    print(f"Filtered rows: {len(filtered_rows)}")
    print(f"Full catalog XLSX: {full_path}")
    print(f"Filtered catalog XLSX: {filtered_path}")
