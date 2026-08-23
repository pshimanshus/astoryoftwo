from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PACKAGE = Path(
    "output/carousels/2026-08-14/"
    "certain-of-you-lost-in-us-no-script-repair-01"
)
SOURCE = PACKAGE / ".internal/visual-quarantine/attempt-01/final"
OUTPUT = PACKAGE / ".internal/full-deck-contact-sheet.png"

thumb_width = 720
thumb_height = 960
outer_margin = 64
gutter = 48
label_height = 52
columns = 2
rows = 3

canvas_width = outer_margin * 2 + columns * thumb_width + gutter
canvas_height = outer_margin * 2 + rows * (label_height + thumb_height) + gutter * (rows - 1)
canvas = Image.new("RGB", (canvas_width, canvas_height), (246, 238, 221))
draw = ImageDraw.Draw(canvas)

try:
    font = ImageFont.truetype(
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        30,
    )
except OSError:
    font = ImageFont.load_default()

for index in range(6):
    slide_number = index + 1
    row, column = divmod(index, columns)
    x = outer_margin + column * (thumb_width + gutter)
    y = outer_margin + row * (label_height + thumb_height + gutter)
    draw.text((x, y + 5), f"SLIDE {slide_number:02d}", fill=(36, 42, 60), font=font)
    with Image.open(SOURCE / f"slide-{slide_number:02d}.png") as image:
        normalized = image.convert("RGB").resize(
            (thumb_width, thumb_height),
            Image.Resampling.LANCZOS,
        )
    canvas.paste(normalized, (x, y + label_height))

canvas.save(OUTPUT, format="PNG", optimize=True)
print(OUTPUT)
