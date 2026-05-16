#!/usr/bin/env python3
"""Range les fichiers d'un dossier dans des sous-dossiers par extension."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from productivity_kit.organize import organize_folder  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder", type=Path, help="Dossier à organiser")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche les déplacements sans les exécuter",
    )
    args = p.parse_args()
    root: Path = args.folder.resolve()
    if not root.is_dir():
        raise SystemExit(f"Dossier introuvable: {root}")
    for line in organize_folder(root, dry_run=args.dry_run):
        print(line)


if __name__ == "__main__":
    main()
