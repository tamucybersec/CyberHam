# 100% AI code, do not hold me to these standards or god awful naming

from bs4 import BeautifulSoup
from bs4.element import Tag
from typing import Sequence, cast
import json


def get_html_file(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        html: str = f.read()

    return html


def extract_major_names(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")

    seen: set[str] = set()
    output: list[str] = []

    all_tables_raw = soup.find_all("table")
    all_tables: Sequence[Tag] = cast(Sequence[Tag], all_tables_raw)
    top_level_tables: list[Tag] = [t for t in all_tables if not t.find_parent("table")]

    for table in top_level_tables:
        rows_raw = table.find_all("tr")
        rows: Sequence[Tag] = cast(Sequence[Tag], rows_raw)
        for row in rows:
            tds_raw = row.find_all("td")
            tds: Sequence[Tag] = cast(Sequence[Tag], tds_raw)
            if not tds:
                continue

            first_td = tds[0]

            # Skip if any <strong> exists inside the first <td>
            if first_td.find("strong") is not None:
                continue

            text = first_td.get_text(strip=True)
            if text not in seen:
                seen.add(text)
                output.append(text)

    output.append("Graduate")
    output.append("Other")
    
    return output


def save_rows_to_json(rows: list[str], filename: str = "majors.json") -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
