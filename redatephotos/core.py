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


@dataclass(frozen=True)
class Rename:
    source: Path
    destination: Path
    captured_at: datetime
    date_source: str


def scan_directory(directory: str | Path) -> ScanResult:
    folder = Path(directory).expanduser().resolve()
    photos = tuple(_read_photo(path) for path in folder.iterdir() if path.suffix.lower() in {".jpg", ".jpeg"})
    return ScanResult(photos=photos)


def plan_renames(scan: ScanResult) -> tuple[Rename, ...]:
    reserved: set[Path] = set()
    plan: list[Rename] = []
    for photo in sorted(scan.photos, key=lambda item: (item.captured_at, item.source.name.casefold())):
        stem = photo.captured_at.strftime("%Y-%m-%d_%H-%M-%S")
        destination = photo.source.with_name(f"{stem}.jpg")
        suffix = 2
        while destination in reserved:
            destination = photo.source.with_name(f"{stem}_{suffix}.jpg")
            suffix += 1
        reserved.add(destination)
        plan.append(Rename(photo.source, destination, photo.captured_at, photo.date_source))
    return tuple(plan)


def _read_photo(path: Path) -> Photo:
    with Image.open(path) as image:
        exif = image.getexif()
        for tag in (36867, 36868, 306):
            if value := exif.get(tag):
                return Photo(path, datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S"), "EXIF")

    return Photo(path, datetime.fromtimestamp(path.stat().st_mtime), "Modified time")
