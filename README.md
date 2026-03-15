# WB Catalog Collector (тестовое задание)

Скрипт собирает каталог Wildberries по запросу `"пальто из натуральной шерсти"` и формирует 2 XLSX-файла:
- полный каталог;
- отфильтрованный каталог (`rating >= 4.5`, `price <= 10000`, `country == "Россия"`).

## Что реализовано

- Поиск товаров через WB search endpoint с пагинацией.
- Enrichment карточек товаров через `card.json` по `nm_id`.
- Нормализация и маппинг полей в итоговую таблицу.
- Устойчивые fallback-правила для неполных данных.
- Запись XLSX без внешних зависимостей (через встроенный `zipfile`, минимальный OOXML).
- Набор unit-тестов для ключевой бизнес-логики преобразований.

## Требования

- Python `>=3.10`
- В проекте внешние зависимости не обязательны для базового запуска.

## Запуск

Базовый запуск:

```bash
python3 main.py
```

Скрипт пишет файлы в директорию `output/`:
- `output/catalog_full.xlsx`
- `output/catalog_filtered.xlsx`

### Режимы источников

- `--source auto` (по умолчанию): пытается live WB, при недоступности переключается на `examples_json`.
- `--source live`: только live WB endpoint (без fallback на examples).
- `--source examples`: только локальные примеры из `examples_json`.

Примеры:

```bash
python3 main.py --source examples
python3 main.py --source live --max-pages 30 --search-delay 0.35 --card-delay 0.02
python3 main.py --output-dir output --max-products 100
```

## Аргументы CLI

- `--query` — поисковый запрос (по умолчанию: `пальто из натуральной шерсти`)
- `--output-dir` — директория для XLSX (по умолчанию: `output`)
- `--source` — `auto|live|examples` (по умолчанию: `auto`)
- `--max-pages` — максимум страниц search (по умолчанию: `50`)
- `--search-delay` — пауза между search-запросами в секундах (по умолчанию: `0.35`)
- `--card-delay` — пауза между card-запросами в секундах (по умолчанию: `0.02`)
- `--max-products` — ограничение числа товаров (0 = без ограничения)

## Схема колонок XLSX

1. Ссылка на товар
2. Артикул
3. Название
4. Цена
5. Описание
6. Ссылки на изображения
7. Все характеристики
8. Название селлера
9. Ссылка на селлера
10. Размеры
11. Остатки
12. Рейтинг
13. Количество отзывов
14. Страна производства

## Ключевые правила маппинга

- Seller: `supplier` / `supplierId` (fallback: `card.selling.supplier_id`), не `brand`.
- Цена: `min(sizes[].price.product) / 100` (из копеек в рубли).
- Размеры: `sizes[].name` с fallback на `sizes[].origName`, дедупликация.
- Рейтинг/отзывы: `reviewRating` + `feedbacks` (fallback на `nmReviewRating`/`nmFeedbacks`).
- Характеристики: `grouped_options` сохраняются как JSON-строка без потери структуры.
- Страна: поиск `name == "Страна производства"` в `grouped_options`, fallback в `options`.
- Фото: `card.media.photo_count`, fallback `search.pics`.
- URL товара: `https://www.wildberries.ru/catalog/{nm_id}/detail.aspx`
- URL селлера: `https://www.wildberries.tj/seller/{supplier_id}`

## Тесты

Запуск:

```bash
python3 -m unittest discover -s tests -v
```

Покрыты проверки:
- расчет минимальной цены;
- сбор и дедуп размеров;
- извлечение страны;
- формирование URL;
- фильтр второй таблицы.

## Ограничения среды

- В некоторых окружениях WB может возвращать `429/498` на live search/card endpoint.
- В `auto` режиме это обрабатывается fallback на локальные `examples_json`.
