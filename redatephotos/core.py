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
    skipped: tuple["SkippedPhoto", ...] = ()


@dataclass(frozen=True)
class SkippedPhoto:
    path: Path
    reason: str


@dataclass(frozen=True)
class UndoEntry:
    original: str
    renamed: str


@dataclass(frozen=True)
class Rename:
    source: Path
    destination: Path
    captured_at: datetime
    date_source: str


def scan_directory(directory: str | Path) -> ScanResult:
    folder = Path(directory).expanduser().resolve()
    photos: list[Photo] = []
    skipped: list[SkippedPhoto] = []
    candidates = sorted(
        (path for path in folder.iterdir() if not path.name.startswith(".") and path.suffix.lower() in {".jpg", ".jpeg"}),
        key=lambda path: path.name.casefold(),
    )
    for path in candidates:
        try:
            photos.append(_read_photo(path))
        except (OSError, ValueError):
            skipped.append(SkippedPhoto(path, "Unreadable image"))
    return ScanResult(photos=tuple(photos), skipped=tuple(skipped))


def plan_renames(scan: ScanResult) -> tuple[Rename, ...]:
    reserved: set[Path] = set()
    sources = {photo.source for photo in scan.photos}
    occupied = set(scan.photos[0].source.parent.iterdir()) - sources if scan.photos else set()
    plan: list[Rename] = []
    for photo in sorted(scan.photos, key=lambda item: (item.captured_at, item.source.name.casefold())):
        stem = photo.captured_at.strftime("%Y-%m-%d_%H-%M-%S")
        destination = photo.source.with_name(f"{stem}.jpg")
        suffix = 2
        while destination in reserved or destination in occupied:
            destination = photo.source.with_name(f"{stem}_{suffix}.jpg")
            suffix += 1
        reserved.add(destination)
        if destination != photo.source:
            plan.append(Rename(photo.source, destination, photo.captured_at, photo.date_source))
    return tuple(plan)


def apply_plan(plan: tuple[Rename, ...]) -> int:
    if not plan:
        return 0
    _move_in_two_phases(
        tuple((item.source, item.destination) for item in plan),
        temporary_prefix=".redatephotos-",
    )

    manifest = plan[0].source.parent / MANIFEST_NAME
    entries = [UndoEntry(item.source.name, item.destination.name) for item in plan]
    manifest.write_text(
        json.dumps(
            [entry.__dict__ for entry in entries],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return len(plan)


def undo_last(directory: str | Path) -> int:
    folder = Path(directory).expanduser().resolve()
    manifest = folder / MANIFEST_NAME
    entries = tuple(UndoEntry(**item) for item in json.loads(manifest.read_text(encoding="utf-8")))
    _move_in_two_phases(
        tuple((folder / entry.renamed, folder / entry.original) for entry in entries),
        temporary_prefix=".redatephotos-undo-",
    )
    manifest.unlink()
    return len(entries)


def _move_in_two_phases(moves: tuple[tuple[Path, Path], ...], *, temporary_prefix: str) -> None:
    sources = {source for source, _ in moves}
    blocked = [destination for _, destination in moves if destination.exists() and destination not in sources]
    if blocked:
        raise FileExistsError(f"Destination already exists: {blocked[0].name}")

    staged = [
        (source, destination, source.with_name(f"{temporary_prefix}{index}.tmp"))
        for index, (source, destination) in enumerate(moves)
    ]
    blocked_temporary = [temporary for _, _, temporary in staged if temporary.exists()]
    if blocked_temporary:
        raise FileExistsError(f"Temporary file already exists: {blocked_temporary[0].name}")

    moved_to_temporary: list[tuple[Path, Path]] = []
    try:
        for source, _, temporary in staged:
            source.rename(temporary)
            moved_to_temporary.append((source, temporary))
    except OSError:
        for source, temporary in reversed(moved_to_temporary):
            temporary.rename(source)
        raise

    moved_to_destination: list[tuple[Path, Path]] = []
    try:
        for _, destination, temporary in staged:
            temporary.rename(destination)
            moved_to_destination.append((temporary, destination))
    except OSError:
        for temporary, destination in reversed(moved_to_destination):
            destination.rename(temporary)
        for source, temporary in reversed(moved_to_temporary):
            temporary.rename(source)
        raise


def _read_photo(path: Path) -> Photo:
    with Image.open(path) as image:
        image.load()
        exif = image.getexif()
        for tag in (36867, 36868, 306):
            if value := exif.get(tag):
                try:
                    return Photo(path, datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S"), "EXIF")
                except ValueError:
                    continue

    return Photo(path, datetime.fromtimestamp(path.stat().st_mtime), "Modified time")
