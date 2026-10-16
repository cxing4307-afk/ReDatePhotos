from datetime import datetime

from conftest import make_jpeg
from redatephotos.core import plan_renames, scan_directory


def test_plan_sorts_photos_by_capture_time(tmp_path):
    make_jpeg(tmp_path / "z-last-name.jpg", captured_at=datetime(2020, 1, 2, 3, 4, 5))
    make_jpeg(tmp_path / "a-first-name.jpg", captured_at=datetime(2022, 6, 7, 8, 9, 10))

    plan = plan_renames(scan_directory(tmp_path))

    assert [(item.source.name, item.destination.name) for item in plan] == [
        ("z-last-name.jpg", "2020-01-02_03-04-05.jpg"),
        ("a-first-name.jpg", "2022-06-07_08-09-10.jpg"),
    ]


def test_plan_numbers_photos_with_the_same_destination(tmp_path):
    captured_at = datetime(2024, 7, 8, 9, 10, 11)
    make_jpeg(tmp_path / "left.jpg", captured_at=captured_at)
    make_jpeg(tmp_path / "right.jpg", captured_at=captured_at)

    plan = plan_renames(scan_directory(tmp_path))

    assert [item.destination.name for item in plan] == [
        "2024-07-08_09-10-11.jpg",
        "2024-07-08_09-10-11_2.jpg",
    ]


def test_plan_avoids_an_existing_destination(tmp_path):
    make_jpeg(tmp_path / "camera.jpg", captured_at=datetime(2024, 7, 8, 9, 10, 11))
    (tmp_path / "2024-07-08_09-10-11.jpg").write_bytes(b"occupied")

    plan = plan_renames(scan_directory(tmp_path))

    assert [item.destination.name for item in plan] == ["2024-07-08_09-10-11_2.jpg"]


def test_plan_omits_a_photo_that_already_has_the_right_name(tmp_path):
    make_jpeg(tmp_path / "2024-07-08_09-10-11.jpg", captured_at=datetime(2024, 7, 8, 9, 10, 11))

    assert plan_renames(scan_directory(tmp_path)) == ()
