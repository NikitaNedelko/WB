from __future__ import annotations

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from wb.constants import (
    DEFAULT_HEADERS,
    MAX_BASKET_HOST,
    SEARCH_ENDPOINTS,
    SEARCH_PARAMS,
    VOL_HOST_UPPER_BOUNDS,
)
from wb.errors import HTTPStatusError
from wb.utils import to_int


def fetch_json(url: str, params: dict[str, Any] | None = None, timeout: int = 20) -> dict[str, Any]:
    full_url = url
    if params:
        full_url = f"{url}?{urlencode(params, doseq=True)}"

    request = Request(full_url, headers=DEFAULT_HEADERS)
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            status = response.status
    except HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        raise HTTPStatusError(err.code, full_url, body) from err
    except URLError as err:
        raise RuntimeError(f"Network error for {full_url}: {err}") from err

    if status != 200:
        raise HTTPStatusError(status, full_url, body)

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as err:
        raise RuntimeError(f"Invalid JSON from {full_url}") from err

    if not isinstance(parsed, dict):
        raise RuntimeError(f"Expected JSON object from {full_url}")
    return parsed


def extract_products(payload: dict[str, Any]) -> list[dict[str, Any]]:
    direct = payload.get("products")
    if isinstance(direct, list):
        return [item for item in direct if isinstance(item, dict)]

    data = payload.get("data")
    if isinstance(data, dict):
        products = data.get("products")
        if isinstance(products, list):
            return [item for item in products if isinstance(item, dict)]

    return []


def fetch_search_catalog(query: str, max_pages: int, request_delay: float) -> list[dict[str, Any]]:
    all_products: list[dict[str, Any]] = []
    seen_ids: set[int] = set()

    for page in range(1, max_pages + 1):
        payload: dict[str, Any] | None = None

        for endpoint in SEARCH_ENDPOINTS:
            params = dict(SEARCH_PARAMS)
            params.update({"query": query, "page": str(page)})
            try:
                candidate = fetch_json(endpoint, params=params, timeout=20)
                products = extract_products(candidate)
                if products or page == 1:
                    payload = candidate
                    break
            except (HTTPStatusError, RuntimeError):
                continue

        if payload is None:
            if page == 1:
                raise RuntimeError("Could not fetch first search page from WB endpoints")
            break

        products = extract_products(payload)
        if not products:
            break

        new_rows = 0
        for item in products:
            nm_id = to_int(item.get("id"))
            if nm_id is None or nm_id in seen_ids:
                continue
            seen_ids.add(nm_id)
            all_products.append(item)
            new_rows += 1

        # Stops if endpoint ignores page and keeps returning same first page.
        if new_rows == 0:
            break

        if request_delay > 0:
            time.sleep(request_delay)

    return all_products


def predict_host_by_vol(vol: int) -> int | None:
    for idx, upper_bound in enumerate(VOL_HOST_UPPER_BOUNDS, start=1):
        if vol <= upper_bound:
            return idx
    return None


def build_card_url(host_id: int, nm_id: int) -> str:
    vol = nm_id // 100000
    part = nm_id // 1000
    return f"https://basket-{host_id:02d}.wbbasket.ru/vol{vol}/part{part}/{nm_id}/info/ru/card.json"


def build_item_base_url(host_id: int, nm_id: int) -> str:
    vol = nm_id // 100000
    part = nm_id // 1000
    return f"https://basket-{host_id:02d}.wbbasket.ru/vol{vol}/part{part}/{nm_id}"


def fetch_card_live(
    nm_id: int,
    host_cache: dict[int, int],
    request_delay: float,
) -> tuple[dict[str, Any] | None, str | None]:
    vol = nm_id // 100000

    candidates: list[int] = []
    if vol in host_cache:
        candidates.append(host_cache[vol])

    predicted = predict_host_by_vol(vol)
    if predicted is not None and predicted not in candidates:
        candidates.append(predicted)

    for host_id in range(1, MAX_BASKET_HOST + 1):
        if host_id not in candidates:
            candidates.append(host_id)

    for host_id in candidates:
        try:
            card = fetch_json(build_card_url(host_id, nm_id), timeout=12)
            host_cache[vol] = host_id
            if request_delay > 0:
                time.sleep(request_delay)
            return card, build_item_base_url(host_id, nm_id)
        except HTTPStatusError as err:
            if err.status in {404, 429, 498}:
                continue
            continue
        except RuntimeError:
            continue

    return None, None
