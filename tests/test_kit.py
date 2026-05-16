from pathlib import Path

from productivity_kit.csv_tools import summarize_csv
from productivity_kit.organize import organize_folder


def test_summarize_csv(tmp_path: Path) -> None:
    p = tmp_path / "x.csv"
    p.write_text("h1,h2\nv1,v2\n", encoding="utf-8")
    s = summarize_csv(p)
    assert s["row_count"] == 1
    assert s["headers"] == ["h1", "h2"]


def test_organize_dry_run(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x")
    lines = organize_folder(tmp_path, dry_run=True)
    assert lines and "mv" in lines[0]
    assert (tmp_path / "a.txt").exists()
