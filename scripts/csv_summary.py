#!/usr/bin/env python3
"""Affiche un résumé JSON d'un fichier CSV (UTF-8)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# permettre: python scripts/csv_summary.py depuis la racine du repo
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from productivity_kit.csv_tools import summarize_csv  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv_file", type=Path)
    p.add_argument("--rows", type=int, default=8, help="Lignes d'aperçu")
    args = p.parse_args()
    data = summarize_csv(args.csv_file, preview_rows=args.rows)
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
