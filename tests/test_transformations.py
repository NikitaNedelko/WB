import unittest

from wb.transform import build_row, collect_sizes, extract_country, filter_rows, select_price_rub


class TransformTests(unittest.TestCase):
    def test_select_price_uses_minimum_size_price(self):
        sizes = [
            {"price": {"product": 299900}},
            {"price": {"product": 109900}},
            {"price": {"product": 159900}},
        ]
        self.assertEqual(select_price_rub(sizes), 1099.0)

    def test_collect_sizes_deduplicates_and_fallbacks(self):
        sizes = [
            {"name": "40-42", "origName": "44"},
            {"name": "40-42", "origName": "44"},
            {"origName": "46"},
            {"name": " 48-50 "},
        ]
        self.assertEqual(collect_sizes(sizes), "40-42, 46, 48-50")

    def test_extract_country_grouped_then_options(self):
        grouped_card = {
            "grouped_options": [
                {
                    "group_name": "Info",
                    "options": [{"name": "Страна производства", "value": "Россия"}],
                }
            ]
        }
        self.assertEqual(extract_country(grouped_card), "Россия")

        options_card = {
            "options": [{"name": "Страна производства", "value": "Беларусь"}],
        }
        self.assertEqual(extract_country(options_card), "Беларусь")

    def test_build_row_uses_supplier_and_urls(self):
        search_item = {
            "id": 123456789,
            "name": "Тестовое пальто",
            "supplier": "Seller",
            "supplierId": 987,
            "reviewRating": 4.7,
            "feedbacks": 42,
            "totalQuantity": 18,
            "pics": 2,
            "sizes": [
                {"name": "42", "price": {"product": 105000}},
                {"name": "44", "price": {"product": 99000}},
            ],
        }
        card = {
            "nm_id": 123456789,
            "description": "Описание",
            "grouped_options": [{"group_name": "X", "options": []}],
            "media": {"photo_count": 2},
            "options": [{"name": "Страна производства", "value": "Россия"}],
        }
        base_url = "https://basket-10.wbbasket.ru/vol1234/part123456/123456789"

        row = build_row(search_item, card, base_url)

        self.assertEqual(row["article"], 123456789)
        self.assertEqual(row["seller_name"], "Seller")
        self.assertEqual(row["seller_url"], "https://www.wildberries.tj/seller/987")
        self.assertEqual(row["product_url"], "https://www.wildberries.ru/catalog/123456789/detail.aspx")
        self.assertEqual(row["price"], 990.0)
        self.assertEqual(
            row["image_urls"],
            "https://basket-10.wbbasket.ru/vol1234/part123456/123456789/images/big/1.webp,"
            "https://basket-10.wbbasket.ru/vol1234/part123456/123456789/images/big/2.webp",
        )

    def test_filter_rows(self):
        rows = [
            {"rating": 4.6, "price": 9999, "country": "Россия"},
            {"rating": 4.49, "price": 5000, "country": "Россия"},
            {"rating": 4.8, "price": 15000, "country": "Россия"},
            {"rating": 4.9, "price": 9000, "country": "Казахстан"},
        ]
        filtered = filter_rows(rows)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["country"], "Россия")


if __name__ == "__main__":
    unittest.main()
