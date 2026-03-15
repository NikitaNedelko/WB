from dataclasses import dataclass


@dataclass
class BuildStats:
    total_products: int = 0
    built_rows: int = 0
    missing_cards: int = 0
    card_errors: int = 0
    source: str = ""
