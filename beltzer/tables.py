from pathlib import Path
from typing import List

TABLES_DIR = Path(__file__).parent / "tables"


def table_lookup(table: str, value: int) -> List:
    with open(TABLES_DIR / f"{table}.table") as f:
        for row in f.read().split("\n"):
            if row.startswith("#"):
                continue
            start_val, end_val, *data = row.split("\t")
            if int(start_val) <= value <= int(end_val):
                return data
