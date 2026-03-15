DEFAULT_QUERY = "пальто из натуральной шерсти"
DEFAULT_OUTPUT_DIR = "output"

SEARCH_ENDPOINTS = [
    "https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search",
    "https://search.wb.ru/exactmatch/ru/common/v18/search",
    "https://search.wb.ru/exactmatch/ru/common/v13/search",
]

SEARCH_PARAMS = {
    "ab_testing": "false",
    "appType": "1",
    "curr": "rub",
    "dest": "-1257786",
    "hide_vflags": "4294967296",
    "inheritFilters": "false",
    "lang": "ru",
    "resultset": "catalog",
    "sort": "popular",
    "spp": "30",
    "suppressSpellcheck": "false",
}

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*",
}

# Legacy WB ranges; used as heuristic only, with host scanning fallback.
VOL_HOST_UPPER_BOUNDS = [
    143,
    287,
    431,
    719,
    1007,
    1061,
    1115,
    1169,
    1313,
    1601,
    1655,
    1919,
    2045,
    2189,
    2405,
    2621,
    2837,
    3053,
    3269,
    3485,
    3701,
    3917,
    4133,
    4349,
    4565,
    4781,
    4997,
    5213,
    5429,
    5645,
]

MAX_BASKET_HOST = 30

COLUMN_SPECS: list[tuple[str, str]] = [
    ("product_url", "Ссылка на товар"),
    ("article", "Артикул"),
    ("name", "Название"),
    ("price", "Цена"),
    ("description", "Описание"),
    ("image_urls", "Ссылки на изображения"),
    ("characteristics", "Все характеристики"),
    ("seller_name", "Название селлера"),
    ("seller_url", "Ссылка на селлера"),
    ("sizes", "Размеры"),
    ("quantity", "Остатки"),
    ("rating", "Рейтинг"),
    ("feedbacks", "Количество отзывов"),
    ("country", "Страна производства"),
]
