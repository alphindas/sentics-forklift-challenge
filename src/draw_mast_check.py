"""Draw the mast-check clicks on frame #1092 -> outputs/mast_check_1092.jpg (mast, cabin roof, front and rear tyre)."""
import json
from PIL import Image, ImageDraw, ImageFont

KEY = "A_01092.jpg"

def font(size):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        return ImageFont.load_default()

def main():
    P = json.load(open("outputs/points_mast.json"))[KEY]
    r = json.load(open("outputs/mast_check.json"))["frames"][KEY]
    im = Image.open(f"frames/{KEY}").convert("RGB"); d = ImageDraw.Draw(im); f, fs = font(28), font(24)

    def tag(xy, text, fill, fnt=f):
        box = d.textbbox(xy, text, font=fnt, anchor="lm")
        d.rectangle((box[0] - 5, box[1] - 3, box[2] + 5, box[3] + 3), fill="black"); d.text(xy, text, font=fnt, fill=fill, anchor="lm")

    for a, b, col, label in (("mast_top", "mast_floor", "yellow", f"mast {r['mast_px']:.0f} px"),
                             ("roof_top", "roof_floor", "cyan", f"roof {r['roof_px']:.0f} px"),
                             ("ftyre_top", "ftyre_bottom", "orange", f"front tyre {r['front_tyre_px']:.0f} px"),
                             ("rtyre_top", "rtyre_bottom", "magenta", f"rear tyre {r['rear_tyre_px']:.0f} px")):
        (x0, y0), (x1, y1) = P[a], P[b]
        d.line((x0, y0, x1, y1), fill=col, width=5)
        for x, y in ((x0, y0), (x1, y1)): d.ellipse((x - 9, y - 9, x + 9, y + 9), outline=col, width=4)
        tag((max(x0, x1) + 16, (y0 + y1) / 2), label, col)
    lines = [f"#1092: mast/roof {r['ratio_mast_roof_raw']:.3f} raw -> {r['ratio_mast_roof_corr']:.3f} corrected with the tyres (3213 mm mast: 1.132; 2888 mm: 1.018)",
             f"tyre scale: mast {r['mast_mm_tyre_scale']:.0f} mm, roof {r['roof_mm_tyre_scale']:.0f} mm (datasheet 2838 mm)"]
    for k, line in enumerate(lines): tag((30, 40 + 34 * k), line, "white", fs)
    im.save("outputs/mast_check_1092.jpg", quality=92); print("saved outputs/mast_check_1092.jpg")

if __name__ == "__main__":
    main()
