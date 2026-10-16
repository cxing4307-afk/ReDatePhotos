from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path

from PIL import Image


MANIFEST_NAME = ".redatephotos-undo.json"


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


def apply_plan(plan: tuple[Rename, ...]) -> int:
    if not plan:
        return 0
    sources = {item.source for item in plan}
    blocked = [item.destination for item in plan if item.destination.exists() and item.destination not in sources]
    if blocked:
        raise FileExistsError(f"Destination already exists: {blocked[0].name}")

    staged: list[tuple[Rename, Path]] = []
    for index, item in enumerate(plan):
        temporary = item.source.with_name(f".redatephotos-{index}.tmp")
        if temporary.exists():
            raise FileExistsError(f"Temporary file already exists: {temporary.name}")
        item.source.rename(temporary)
        staged.append((item, temporary))

    for item, temporary in staged:
        temporary.rename(item.destination)

    manifest = plan[0].source.parent / MANIFEST_NAME
    manifest.write_text(
        json.dumps(
            [{"original": item.source.name, "renamed": item.destination.name} for item in plan],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return len(plan)


def undo_last(directory: str | Path) -> int:
    folder = Path(directory).expanduser().resolve()
    manifest = folder / MANIFEST_NAME
    entries = json.loads(manifest.read_text(encoding="utf-8"))

    staged: list[tuple[dict[str, str], Path]] = []
    for index, entry in enumerate(entries):
        source = folder / entry["renamed"]
        temporary = folder / f".redatephotos-undo-{index}.tmp"
        source.rename(temporary)
        staged.append((entry, temporary))

    for entry, temporary in staged:
        temporary.rename(folder / entry["original"])
    manifest.unlink()
    return len(entries)


def _read_photo(path: Path) -> Photo:
    with Image.open(path) as image:
        exif = image.getexif()
        for tag in (36867, 36868, 306):
            if value := exif.get(tag):
                return Photo(path, datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S"), "EXIF")

    return Photo(path, datetime.fromtimestamp(path.stat().st_mtime), "Modified time")
