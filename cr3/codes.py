"""Official code tables for the Texas CR-3 crash report.

The tables are loaded from JSON built directly from TxDOT's CR-100 manual
(see tools/build_code_tables.py). Lookups never guess: a code that is not in
the table comes back as unknown so a person can check the report.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
SUPPORTED_VERSIONS = {"2023": "tx_cr3_2023_codes.json"}


@dataclass(frozen=True)
class Decoded:
    code: str
    meaning: str | None
    table: str

    @property
    def known(self) -> bool:
        return self.meaning is not None

    def __str__(self) -> str:
        return f"{self.code} = {self.meaning}" if self.known else f"{self.code} = NOT IN OFFICIAL TABLE"

    def as_dict(self) -> dict:
        return {"code": self.code, "meaning": self.meaning, "table": self.table, "known": self.known}


class CodeBook:
    def __init__(self, doc: dict):
        self.form_version: str = doc["form_version"]
        self.source: str = doc["source"]
        self.source_url: str = doc["source_url"]
        self._tables: dict[str, dict] = doc["tables"]

    def table(self, name: str) -> dict[str, str]:
        return self._tables[name]["values"]

    def code_sheet_number(self, name: str) -> int:
        return self._tables[name]["code_sheet"]

    def lookup(self, table: str, code) -> Decoded:
        """Decode one code. Codes are matched as written on the report, ignoring case and padding."""
        text = str(code).strip().upper()
        values = self.table(table)
        meaning = values.get(text)
        if meaning is None and text.isdigit():
            meaning = values.get(str(int(text)))  # "07" on a report means code 7
            if meaning is not None:
                text = str(int(text))
        return Decoded(text, meaning, table)


@lru_cache(maxsize=None)
def load(form_version: str = "2023") -> CodeBook:
    if form_version not in SUPPORTED_VERSIONS:
        raise KeyError(f"No code tables loaded for CR-3 form version {form_version!r}")
    with open(DATA_DIR / SUPPORTED_VERSIONS[form_version], encoding="utf-8") as fh:
        return CodeBook(json.load(fh))
