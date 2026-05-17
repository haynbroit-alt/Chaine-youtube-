from __future__ import annotations

import shutil
from pathlib import Path


def organize_folder(root: Path, *, dry_run: bool = False) -> list[str]:
    """
    Déplace chaque fichier direct du dossier `root` vers `root/<extension>/`.
    Retourne une ligne de journal par action (ou simulation).
    """
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(str(root))

    lines: list[str] = []
    for item in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not item.is_file():
            continue
        ext = item.suffix.lower().lstrip(".") or "sans_extension"
        dest_dir = root / ext
        dest = dest_dir / item.name
        if dest_dir == root:
            continue
        if dry_run:
            lines.append(f"[simulation] {item} → {dest}")
            continue
        dest_dir.mkdir(exist_ok=True)
        final = dest
        if final.exists():
            stem, suf = item.stem, item.suffix
            n = 1
            while final.exists():
                final = dest_dir / f"{stem}_{n}{suf}"
                n += 1
        shutil.move(str(item), str(final))
        lines.append(f"déplacé: {item.name} -> {final.relative_to(root)}")
    return lines
