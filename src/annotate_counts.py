"""Draw the crate counts on frame #999 (outputs/A_00999_counts.jpg).

Counts were made by eye on the zoomed frame: 9 columns (top and bottom row), 4 layers,
3 labels (columns 1-2, 4, 7), double pallet feet between columns 3/4 and 6/7.
Marker positions are approximate pixel positions, placed by eye; they illustrate the
count and are not measurements.
"""
from PIL import Image, ImageDraw, ImageFont

SRC, DST = "frames/A_00999.jpg", "outputs/A_00999_counts.jpg"

TOP_ROW = [(1095, 535), (1172, 528), (1252, 518), (1333, 508), (1418, 498), (1510, 488), (1605, 478), (1705, 465), (1815, 455)]
BOTTOM_ROW = [(1135, 840), (1212, 845), (1293, 848), (1378, 848), (1465, 848), (1560, 845), (1655, 842), (1760, 840), (1870, 835)]
LAYERS = [(1065, 560), (1065, 650), (1065, 735), (1065, 830)]
LABELS = [(1152, 740), (1392, 718), (1698, 690)]
DOUBLE_FEET = [(1320, 930), (1610, 922)]


def font(size):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        return ImageFont.load_default()


def main():
    im = Image.open(SRC).convert("RGB")
    d = ImageDraw.Draw(im)
    f, fs = font(30), font(24)

    def tag(xy, text, fill, fnt=f):
        x, y = xy
        box = d.textbbox((x, y), text, font=fnt, anchor="mm")
        d.rectangle((box[0] - 5, box[1] - 3, box[2] + 5, box[3] + 3), fill="black")
        d.text((x, y), text, font=fnt, fill=fill, anchor="mm")

    for i, p in enumerate(TOP_ROW, 1):
        tag(p, str(i), "yellow")
    for i, p in enumerate(BOTTOM_ROW, 1):
        tag(p, str(i), "cyan")
    for i, p in enumerate(LAYERS, 1):
        tag(p, f"L{i}", "white", fs)
    for x, y in LABELS:
        d.rectangle((x - 38, y - 42, x + 38, y + 42), outline="magenta", width=5)
    for x, y in DOUBLE_FEET:
        d.ellipse((x - 45, y - 28, x + 45, y + 28), outline="orange", width=5)

    legend = ["#999: 9 columns (yellow top row, cyan bottom row), 4 layers (L1-L4)",
              "magenta = 3 labels (columns 1-2, 4, 7); orange = double feet where pallets meet (3/4, 6/7)",
              "markers placed by eye; right end of lower rows and pallet at frame edge"]
    for k, line in enumerate(legend):
        tag((960, 1000 + k * 30), line, "white", fs)
    im.save(DST, quality=92)
    print("saved", DST)


if __name__ == "__main__":
    main()
