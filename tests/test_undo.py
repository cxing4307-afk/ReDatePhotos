from datetime import datetime

from conftest import make_jpeg
from redatephotos.core import apply_plan, plan_renames, scan_directory, undo_last


def test_undo_restores_original_names(tmp_path):
    make_jpeg(tmp_path / "holiday-a.jpg", captured_at=datetime(2021, 5, 4, 3, 2, 1))
    make_jpeg(tmp_path / "holiday-b.jpg", captured_at=datetime(2021, 5, 4, 3, 2, 2))
    plan = plan_renames(scan_directory(tmp_path))

    assert apply_plan(plan) == 2
    assert sorted(path.name for path in tmp_path.glob("*.jpg")) == [
        "2021-05-04_03-02-01.jpg",
        "2021-05-04_03-02-02.jpg",
    ]

    assert undo_last(tmp_path) == 2
    assert sorted(path.name for path in tmp_path.glob("*.jpg")) == ["holiday-a.jpg", "holiday-b.jpg"]
    assert not (tmp_path / ".redatephotos-undo.json").exists()
