from datetime import datetime
import os
from pathlib import Path

from PIL import Image


def make_jpeg(path: Path, *, captured_at: datetime | None = None) -> None:
    image = Image.new("RGB", (32, 24), "#d97706")
    if captured_at is None:
        image.save(path, "JPEG")
        return

    exif = Image.Exif()
    exif[36867] = captured_at.strftime("%Y:%m:%d %H:%M:%S")
    image.save(path, "JPEG", exif=exif)


def set_mtime(path: Path, value: datetime) -> None:
    timestamp = value.timestamp()
    os.utime(path, (timestamp, timestamp))

