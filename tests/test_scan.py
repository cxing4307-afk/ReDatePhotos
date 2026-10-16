from datetime import datetime

from conftest import make_jpeg, set_mtime
from redatephotos.core import scan_directory


def test_scan_reads_original_capture_time(tmp_path):
    photo = tmp_path / "camera.jpg"
    make_jpeg(photo, captured_at=datetime(2024, 6, 8, 9, 10, 11))

    result = scan_directory(tmp_path)

    assert [(item.source.name, item.captured_at, item.date_source) for item in result.photos] == [
        ("camera.jpg", datetime(2024, 6, 8, 9, 10, 11), "EXIF")
    ]


def test_scan_falls_back_to_file_modified_time(tmp_path):
    photo = tmp_path / "download.jpg"
    make_jpeg(photo)
    set_mtime(photo, datetime(2023, 2, 3, 4, 5, 6))

    result = scan_directory(tmp_path)

    assert result.photos[0].captured_at == datetime(2023, 2, 3, 4, 5, 6)
    assert result.photos[0].date_source == "Modified time"
