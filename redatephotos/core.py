from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class Photo:
    source: Path
    captured_at: datetime
    date_source: str


@dataclass(frozen=True)
class ScanResult:
    photos: tuple[Photo, ...]


def scan_directory(directory: str | Path) -> ScanResult:
    folder = Path(directory).expanduser().resolve()
    photos = tuple(_read_photo(path) for path in folder.iterdir() if path.suffix.lower() in {".jpg", ".jpeg"})
    return ScanResult(photos=photos)


def _read_photo(path: Path) -> Photo:
    with Image.open(path) as image:
        exif = image.getexif()
        for tag in (36867, 36868, 306):
            if value := exif.get(tag):
                return Photo(path, datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S"), "EXIF")

    return Photo(path, datetime.fromtimestamp(path.stat().st_mtime), "Modified time")
