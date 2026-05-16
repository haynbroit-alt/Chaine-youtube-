from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def summarize_csv(path: Path, preview_rows: int = 8) -> dict[str, Any]:
    """Lit un CSV encodé UTF-8 et renvoie métadonnées + aperçu."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(str(path))

    with path.open(newline="", encoding="utf-8") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        f.seek(0)
        reader = csv.reader(f, dialect)
        rows = list(reader)

    if not rows:
        return {
            "path": str(path),
            "row_count": 0,
            "column_count": 0,
            "headers": [],
            "preview": [],
            "column_types_hint": {},
        }

    headers = rows[0]
    data_rows = rows[1:]
    row_count = len(data_rows)
    col_count = len(headers)

    preview = data_rows[: max(0, preview_rows)]

    type_hints: dict[str, str] = {}
    if data_rows:
        for i, name in enumerate(headers):
            col_vals = [r[i] if i < len(r) else "" for r in data_rows[:200]]
            nonempty = [v for v in col_vals if v.strip()]
            if not nonempty:
                type_hints[name] = "vide"
                continue
            numeric_ok = all(_looks_numeric(v) for v in nonempty)
            type_hints[name] = "nombre" if numeric_ok else "texte"

    return {
        "path": str(path.resolve()),
        "row_count": row_count,
        "column_count": col_count,
        "headers": headers,
        "preview": preview,
        "column_types_hint": type_hints,
    }


def _looks_numeric(value: str) -> bool:
    value = value.strip().replace(" ", "")
    if not value:
        return False
    try:
        float(value.replace(",", "."))
        return True
    except ValueError:
        return False

