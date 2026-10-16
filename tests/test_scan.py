from datetime import datetime

from PIL import Image

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


def test_scan_skips_damaged_images(tmp_path):
    make_jpeg(tmp_path / "good.jpg", captured_at=datetime(2025, 1, 2, 3, 4, 5))
    (tmp_path / "broken.jpg").write_bytes(b"this is not a jpeg")

    result = scan_directory(tmp_path)

    assert [photo.source.name for photo in result.photos] == ["good.jpg"]
    assert [(item.path.name, item.reason) for item in result.skipped] == [
        ("broken.jpg", "Unreadable image")
    ]


def test_scan_tries_later_dates_when_preferred_exif_is_malformed(tmp_path):
    photo = tmp_path / "odd-camera.jpg"
    exif = Image.Exif()
    exif[36867] = "not a date"
    exif[36868] = "2023:04:05 06:07:08"
    Image.new("RGB", (10, 10)).save(photo, "JPEG", exif=exif)

    result = scan_directory(tmp_path)

    assert result.photos[0].captured_at == datetime(2023, 4, 5, 6, 7, 8)
    assert result.photos[0].date_source == "EXIF"
