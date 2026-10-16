"""Rebuild the small, synthetic demo set committed with the project."""

from datetime import datetime
import os
from pathlib import Path

from PIL import Image, ImageDraw


HERE = Path(__file__).parent


def make_photo(filename: str, colors: tuple[str, str], label: str, captured_at: datetime | None) -> None:
    image = Image.new("RGB", (960, 640), colors[0])
    draw = ImageDraw.Draw(image)
    for y in range(image.height):
        ratio = y / image.height
        start = ImageColor.getrgb(colors[0])
        end = ImageColor.getrgb(colors[1])
        color = tuple(round(a + (b - a) * ratio) for a, b in zip(start, end))
        draw.line((0, y, image.width, y), fill=color)
    draw.ellipse((620, 70, 820, 270), fill="#fff3c4")
    draw.polygon(((0, 510), (260, 250), (460, 510)), fill="#334d43")
    draw.polygon(((300, 510), (610, 190), (900, 510)), fill="#243b35")
    draw.rectangle((0, 510, 960, 640), fill="#182c35")
    draw.text((42, 570), label, fill="#fffdf8", stroke_width=1)

    if captured_at:
        exif = Image.Exif()
        exif[36867] = captured_at.strftime("%Y:%m:%d %H:%M:%S")
        image.save(HERE / filename, "JPEG", quality=88, exif=exif)
    else:
        image.save(HERE / filename, "JPEG", quality=88)


if __name__ == "__main__":
    from PIL import ImageColor

    make_photo("IMG_1042.jpg", ("#dc7756", "#546d7b"), "MORNING RIDGE", datetime(2024, 5, 18, 7, 42, 11))
    make_photo("DSC0098.jpg", ("#e9b968", "#6c7489"), "LATE LIGHT", datetime(2024, 5, 18, 18, 6, 32))
    make_photo("phone-export.jpg", ("#9cc8c0", "#53698f"), "THE WAY HOME", None)
    timestamp = datetime(2024, 5, 19, 10, 15, 0).timestamp()
    os.utime(HERE / "phone-export.jpg", (timestamp, timestamp))
    (HERE / "damaged.jpg").write_bytes(b"Intentionally damaged JPEG for the demo.\n")
