from __future__ import annotations

import math
import zipfile
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as xml_escape

from wb.constants import COLUMN_SPECS


def excel_column_name(index: int) -> str:
    if index < 1:
        raise ValueError("Index must be >= 1")

    out = ""
    n = index
    while n > 0:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


def make_cell_xml(row_idx: int, col_idx: int, value: Any) -> str:
    ref = f"{excel_column_name(col_idx)}{row_idx}"
    if value is None or value == "":
        return f'<c r="{ref}"/>'

    if isinstance(value, bool):
        return f'<c r="{ref}" t="b"><v>{"1" if value else "0"}</v></c>'

    if isinstance(value, int):
        return f'<c r="{ref}"><v>{value}</v></c>'

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return f'<c r="{ref}"/>'
        return f'<c r="{ref}"><v>{value}</v></c>'

    text = xml_escape(str(value))
    preserve = " xml:space=\"preserve\"" if (text[:1] == " " or text[-1:] == " ") else ""
    return f'<c r="{ref}" t="inlineStr"><is><t{preserve}>{text}</t></is></c>'


def build_sheet_xml(headers: list[str], records: list[list[Any]]) -> str:
    row_xml: list[str] = []

    header_cells = [make_cell_xml(1, idx + 1, value) for idx, value in enumerate(headers)]
    row_xml.append(f'<row r="1">{"".join(header_cells)}</row>')

    for row_idx, record in enumerate(records, start=2):
        cells = [make_cell_xml(row_idx, col_idx + 1, value) for col_idx, value in enumerate(record)]
        row_xml.append(f'<row r="{row_idx}">{"".join(cells)}</row>')

    max_col = excel_column_name(max(len(headers), 1))
    max_row = max(len(records) + 1, 1)

    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
        f"<dimension ref=\"A1:{max_col}{max_row}\"/>"
        "<sheetData>"
        f"{''.join(row_xml)}"
        "</sheetData>"
        "</worksheet>"
    )


def write_xlsx(path: Path, rows: list[dict[str, Any]]) -> None:
    headers = [title for _, title in COLUMN_SPECS]
    records = [[row.get(key) for key, _ in COLUMN_SPECS] for row in rows]
    sheet_xml = build_sheet_xml(headers, records)

    content_types = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
        "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
        "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
        "<Override PartName=\"/xl/workbook.xml\" "
        "ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>"
        "<Override PartName=\"/xl/worksheets/sheet1.xml\" "
        "ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>"
        "</Types>"
    )
    root_rels = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        "<Relationship Id=\"rId1\" "
        "Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" "
        "Target=\"xl/workbook.xml\"/>"
        "</Relationships>"
    )
    workbook_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" "
        "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
        "<sheets><sheet name=\"Catalog\" sheetId=\"1\" r:id=\"rId1\"/></sheets>"
        "</workbook>"
    )
    workbook_rels = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        "<Relationship Id=\"rId1\" "
        "Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" "
        "Target=\"worksheets/sheet1.xml\"/>"
        "</Relationships>"
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
