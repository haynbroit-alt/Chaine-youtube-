#!/usr/bin/env python3
"""Range les fichiers d'un dossier dans des sous-dossiers par extension."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


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

    for item in root.iterdir():
        if not item.is_file():
            continue
        ext = item.suffix.lower().lstrip(".") or "sans_extension"
        dest_dir = root / ext
        dest = dest_dir / item.name
        if dest_dir == root:
            continue
        if args.dry_run:
            print(f"mv {item} -> {dest}")
        else:
            dest_dir.mkdir(exist_ok=True)
            if dest.exists():
                stem, suf = item.stem, item.suffix
                n = 1
                while dest.exists():
                    dest = dest_dir / f"{stem}_{n}{suf}"
                    n += 1
            shutil.move(str(item), str(dest))
            print(f"déplacé: {item.name} -> {dest.relative_to(root)}")


if __name__ == "__main__":
    main()
