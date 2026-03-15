from __future__ import annotations

from typing import Any, Iterable

from wb.api import build_item_base_url, predict_host_by_vol
from wb.utils import safe_json_dumps, to_float, to_int


def select_price_rub(sizes: Any) -> float | None:
    if not isinstance(sizes, list):
        return None

    prices: list[float] = []
    for size in sizes:
        if not isinstance(size, dict):
            continue
        price_obj = size.get("price")
        if not isinstance(price_obj, dict):
            continue
        product_price = to_float(price_obj.get("product"))
        if product_price is None:
            continue
        prices.append(product_price / 100.0)

    if not prices:
        return None
    return round(min(prices), 2)


def collect_sizes(sizes: Any) -> str:
    if not isinstance(sizes, list):
        return ""

    seen: set[str] = set()
    ordered: list[str] = []

    for size in sizes:
        if not isinstance(size, dict):
            continue
        raw = size.get("name") or size.get("origName")
        if raw is None:
            continue
        value = str(raw).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)

    return ", ".join(ordered)


def extract_country(card: dict[str, Any]) -> str:
    grouped = card.get("grouped_options")
    if isinstance(grouped, list):
        for group in grouped:
            if not isinstance(group, dict):
                continue
            options = group.get("options")
            if not isinstance(options, list):
                continue
            for option in options:
                if not isinstance(option, dict):
                    continue
                if str(option.get("name", "")).strip() == "Страна производства":
                    return str(option.get("value", "")).strip()

    options_flat = card.get("options")
    if isinstance(options_flat, list):
        for option in options_flat:
            if not isinstance(option, dict):
                continue
            if str(option.get("name", "")).strip() == "Страна производства":
                return str(option.get("value", "")).strip()

    return ""


def extract_rating(search_item: dict[str, Any]) -> float | None:
    rating = to_float(search_item.get("reviewRating"))
    if rating is None:
        rating = to_float(search_item.get("nmReviewRating"))
    return rating


def extract_feedbacks(search_item: dict[str, Any]) -> int | None:
    feedbacks = to_int(search_item.get("feedbacks"))
    if feedbacks is None:
        feedbacks = to_int(search_item.get("nmFeedbacks"))
    return feedbacks


def create_image_urls(base_url: str | None, photo_count: int | None) -> str:
    if not base_url or not photo_count or photo_count <= 0:
        return ""
    links = [f"{base_url}/images/big/{idx}.webp" for idx in range(1, photo_count + 1)]
    return ",".join(links)


def build_row(search_item: dict[str, Any], card: dict[str, Any] | None, item_base_url: str | None) -> dict[str, Any]:
    card = card or {}

    nm_id = to_int(search_item.get("id")) or to_int(card.get("nm_id")) or 0
    supplier_id = to_int(search_item.get("supplierId"))
    if supplier_id is None:
        selling = card.get("selling")
        if isinstance(selling, dict):
            supplier_id = to_int(selling.get("supplier_id"))

    grouped_options = card.get("grouped_options")
    if grouped_options is None:
        grouped_options = []

    media = card.get("media") if isinstance(card.get("media"), dict) else {}
    photo_count = to_int(media.get("photo_count"))
    if photo_count is None:
        photo_count = to_int(search_item.get("pics"))

    if item_base_url is None and nm_id > 0:
        predicted_host = predict_host_by_vol(nm_id // 100000)
        if predicted_host is not None:
            item_base_url = build_item_base_url(predicted_host, nm_id)

    return {
        "product_url": f"https://www.wildberries.ru/catalog/{nm_id}/detail.aspx" if nm_id else "",
        "article": nm_id or "",
        "name": search_item.get("name") or card.get("imt_name") or "",
        "price": select_price_rub(search_item.get("sizes")),
        "description": str(card.get("description") or "").strip(),
        "image_urls": create_image_urls(item_base_url, photo_count),
        "characteristics": safe_json_dumps(grouped_options),
        "seller_name": search_item.get("supplier") or "",
        "seller_url": f"https://www.wildberries.tj/seller/{supplier_id}" if supplier_id else "",
        "sizes": collect_sizes(search_item.get("sizes")),
        "quantity": to_int(search_item.get("totalQuantity")),
        "rating": extract_rating(search_item),
        "feedbacks": extract_feedbacks(search_item),
        "country": extract_country(card),
    }


def filter_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        rating = to_float(row.get("rating"))
        price = to_float(row.get("price"))
        country = str(row.get("country") or "").strip()
        if rating is None or price is None:
            continue
        if rating >= 4.5 and price <= 10000 and country == "Россия":
            result.append(row)
    return result
