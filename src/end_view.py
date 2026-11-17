"""Step 7: the END of the green-crate load (the face across the forks), seen in the approach shot at 18.3-19.2 s.

Plain idea: in the side frames (#999, #1086-#1098) only the long side is visible, so the depth across the forks was assumed (1.2 m, scenario D).
In the approach shot the truck comes towards the camera at an angle, so the long side AND the end face are both visible, with a corner between them.
Two independent checks:
  1. Counting (by eye, marked on outputs/E_00930_18.60s_counts.jpg and E_00960_19.20s_counts.jpg): 9 columns on the long side, 6 crates across the
     end face in two blocks of 3, a step between the blocks, and 5 pallet-block positions under the end face with a double block in the middle.
  2. Geometry (automatic, this script): the green load is found by colour; the height of the load in pixels at the left end, at the corner and at the
     right end tells how far each edge is from the camera (twice as far = half as tall). With a pinhole camera this gives the two face lengths.
     The ratio end/long does not depend on the height ruler. 2 pallets across predicts about 1.0 (2.4 m / 2.4 m), 1 pallet across predicts 0.5.
The frames are read from outputs/ (saved there by extract(), which needs video.mp4), so the check runs without the video.
"""
import json, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

FPS = 50
FRAMES = {870: "close-up at the palletiser, EPAL stamp on a pallet block", 915: "approach, end face visible",
          930: "approach, clearest end face", 945: "approach, end face visible", 960: "approach, corner clearest"}
GEOM = [915, 930, 945, 960]            # frames used for the length ratio
CX = 960                               # principal point = image centre (1920 px wide)
H_LOAD = 1.40                          # m, measured load height (truck ruler, scenario D); only used for metres, NOT for the ratio
F_RANGE = (800, 1400)                  # px, same focal-length range as the Monte Carlo


def path(fr):
    return f"outputs/E_{fr:05d}_{fr / FPS:.2f}s.jpg"


def extract(video="video.mp4"):
    """Save the end-view frames to outputs/ with frame number and timestamp in the name."""
    v = cv2.VideoCapture(video)
    for fr in FRAMES:
        v.set(cv2.CAP_PROP_POS_FRAMES, fr); ok, f = v.read()
        assert ok, fr
        cv2.imwrite(path(fr), f, [cv2.IMWRITE_JPEG_QUALITY, 95])


def green_profile(img):
    """For each image column: top and bottom of the green crates (colour mask). Returns x, top, bottom."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    m = ((hsv[..., 0] > 30) & (hsv[..., 0] < 80) & (hsv[..., 1] > 40) & (hsv[..., 2] > 110)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    xs, t, b = [], [], []
    for x in range(700, 1900, 2):
        ys = np.where(m[380:900, x])[0]
        if len(ys) > 150:
            xs.append(x); t.append(ys.min() + 380); b.append(ys.max() + 380)
    return np.array(xs), np.array(t, float), np.array(b, float)


def edges(xs, t, b):
    """Left end, corner (tallest = nearest edge) and right end, with heights from straight lines fitted to the top and bottom of each face."""
    h = np.convolve(b - t, np.ones(9) / 9, "same")
    iC = int(np.argmax(h[10:-10])) + 10
    xL, xC, xR = xs[0], xs[iC], xs[-1]
    def fit(lo, hi):
        s = (xs > lo) & (xs < hi)
        return np.polyfit(xs[s], t[s], 1), np.polyfit(xs[s], b[s], 1)
    (tl, bl), (tr, br) = fit(xL + 15, xC - 15), fit(xC + 15, xR - 15)
    hgt = lambda tp, bp, x: float(np.polyval(bp, x) - np.polyval(tp, x))
    return dict(xL=float(xL), hL=hgt(tl, bl, xL), xC=float(xC), hC=(hgt(tl, bl, xC) + hgt(tr, br, xC)) / 2, xR=float(xR), hR=hgt(tr, br, xR))


def faces(e, f, H=H_LOAD, cx=CX):
    """Pinhole camera: an edge of real height H that is h px tall is at depth Z = f*H/h and sideways X = (x-cx)*H/h.
    Returns long-face length, end-face length (m) and the angle between the two faces (deg)."""
    P = lambda x, h: np.array([(x - cx) * H / h, f * H / h])
    L, C, R = P(e["xL"], e["hL"]), P(e["xC"], e["hC"]), P(e["xR"], e["hR"])
    a, b = C - L, R - C
    ang = float(np.degrees(np.arccos(a @ b / np.linalg.norm(a) / np.linalg.norm(b))))
    return float(np.linalg.norm(a)), float(np.linalg.norm(b)), ang


def f_right_angle(e):
    """Focal length (px) at which the two faces meet at 90 degrees."""
    fs = np.arange(600, 3000, 5)
    return float(fs[np.argmin([abs(faces(e, f)[2] - 90) for f in fs])])


def measure():
    out = {}
    for fr in GEOM:
        e = edges(*green_profile(cv2.imread(path(fr))))
        rows = {}
        for f in (F_RANGE[0], 1100, F_RANGE[1], f_right_angle(e)):
            lg, en, ang = faces(e, f)
            rows[f"{f:.0f}"] = dict(long_m=lg, end_m=en, ratio_end_over_long=en / lg, angle_deg=ang)
        out[str(fr)] = dict(t_s=fr / FPS, edges_px=e, f_right_angle_px=f_right_angle(e), by_focal=rows)
    ratios = [r["ratio_end_over_long"] for v in out.values() for r in v["by_focal"].values()]
    r90 = [v["by_focal"][f"{v['f_right_angle_px']:.0f}"] for v in out.values()]
    summary = dict(ratio_all_min=min(ratios), ratio_all_max=max(ratios),
                   ratio_right_angle=[min(r["ratio_end_over_long"] for r in r90), max(r["ratio_end_over_long"] for r in r90)],
                   f_right_angle_px=[min(v["f_right_angle_px"] for v in out.values()), max(v["f_right_angle_px"] for v in out.values())],
                   long_m_right_angle=[min(r["long_m"] for r in r90), max(r["long_m"] for r in r90)],
                   end_m_right_angle=[min(r["end_m"] for r in r90), max(r["end_m"] for r in r90)],
                   predicted_ratio={"E: 2 pallets across (2.4 / 2.4)": 1.0, "D: 1 pallet across (1.2 / 2.4)": 0.5})
    return dict(frames=out, summary=summary,
                counts=dict(long_side_columns=9, end_face_crates_across=6, end_face_blocks="2 blocks of 3, step between them", layers=4,
                            labels_long_side="3, on columns 1, 4, 7", pallet_blocks_under_end_face="5 positions: corner, block, DOUBLE block, block, corner",
                            pallet_blocks_under_long_side="7 positions: double blocks between columns 3/4 and 6/7",
                            close_up="EPAL stamp on a pallet corner block (17.4 s)"))


# ---- annotated images (marker positions placed by eye on the zoomed frames; they illustrate the counts, they are not measurements) ----
ANN = {
    930: dict(long=[(874, 756), (912, 756), (952, 756), (990, 756), (1034, 756), (1080, 756), (1128, 756), (1182, 756), (1236, 756)],
              end=[(1288, 752), (1340, 748), (1386, 744), (1440, 738), (1480, 734), (1520, 730)],
              corner=((1240, 455), (1262, 812)), seam=((1388, 470), (1408, 800)),
              layers=[(820, 575), (820, 645), (820, 715), (820, 785)], labels=[(882, 697), (998, 690), (1145, 678)],
              feet_end=[(1262, 836), (1340, 830), (1412, 826), (1475, 820), (1530, 812)], double=[(971, 845), (1094, 843), (1412, 826)]),
    960: dict(long=[(965, 815), (1020, 815), (1077, 812), (1133, 810), (1195, 808), (1257, 806), (1325, 804), (1400, 802), (1470, 800)], end=[(1533, 663), (1569, 663), (1602, 663), (1635, 663), (1662, 663), (1685, 663)],
              corner=((1490, 430), (1505, 860)), seam=None, layers=[(905, 555), (905, 625), (905, 700), (905, 780)], labels=[(980, 722), (1143, 712), (1357, 697)], feet_end=[], double=[]),
}


def font(size):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        return ImageFont.load_default()


def annotate():
    for fr, a in ANN.items():
        im = Image.open(path(fr)).convert("RGB"); d = ImageDraw.Draw(im); f, fs = font(20), font(24)
        def tag(xy, text, fill, fnt=f):
            box = d.textbbox(xy, text, font=fnt, anchor="mm")
            d.rectangle((box[0] - 4, box[1] - 2, box[2] + 4, box[3] + 2), fill="black"); d.text(xy, text, font=fnt, fill=fill, anchor="mm")
        d.line(a["corner"], fill="red", width=4); tag((a["corner"][0][0], a["corner"][0][1] - 22), "corner", "red")
        if a["seam"]:
            d.line(a["seam"], fill="orange", width=4); tag((a["seam"][0][0] + 60, a["seam"][0][1] - 70), "step between blocks", "orange")
        for i, (x, y) in enumerate(a["long"], 1): tag((x, y), str(i), "yellow")
        for i, (x, y) in enumerate(a["end"], 1): tag((x, y), str(i), "cyan")
        for i, p in enumerate(a["layers"], 1): tag(p, f"L{i}", "white")
        for x, y in a["labels"]: d.rectangle((x - 18, y - 28, x + 18, y + 28), outline="magenta", width=4)
        for x, y in a["feet_end"]: d.ellipse((x - 9, y - 9, x + 9, y + 9), outline="cyan", width=3)
        for x, y in a["double"]: d.ellipse((x - 30, y - 18, x + 30, y + 18), outline="orange", width=4)
        legend = {930: [f"#{fr} ({fr / FPS:.2f} s): long side 9 columns (yellow), end face 6 crates across (cyan), 4 layers (L1-L4)",
                        "red = corner; orange line = step between two blocks of 3; magenta = 3 labels on columns 1, 4, 7",
                        "under the end face: 5 block positions (cyan circles) with a double block in the middle (orange) = 2 pallets",
                        "markers placed by eye on a zoomed frame"],
                  960: [f"#{fr} ({fr / FPS:.2f} s): long side 9 columns (yellow), end face 6 crates across (cyan, layer 3), 4 layers",
                        "red = corner; magenta = 3 labels on columns 1, 4, 7; same load as in #930 (one continuous shot)",
                        "markers placed by eye on a zoomed frame"]}[fr]
        for k, line in enumerate(legend): tag((960, 960 + k * 30), line, "white", fs)
        dst = path(fr).replace(".jpg", "_counts.jpg"); im.save(dst, quality=92); print("saved", dst)


if __name__ == "__main__":
    if os.path.exists("video.mp4") and not all(os.path.exists(path(fr)) for fr in FRAMES):
        extract()
    r = measure(); json.dump(r, open("outputs/end_view.json", "w"), indent=1)
    s = r["summary"]
    for fr, v in r["frames"].items():
        print(f"#{fr} ({v['t_s']:.2f} s): " + " | ".join(f"f={k}: long {x['long_m']:.2f} m, end {x['end_m']:.2f} m, end/long {x['ratio_end_over_long']:.2f}, angle {x['angle_deg']:.0f} deg" for k, x in v["by_focal"].items()))
    print(f"\nend/long ratio over all frames and focal lengths: {s['ratio_all_min']:.2f}-{s['ratio_all_max']:.2f}; with a right angle between the faces: "
          f"{s['ratio_right_angle'][0]:.2f}-{s['ratio_right_angle'][1]:.2f} (f = {s['f_right_angle_px'][0]:.0f}-{s['f_right_angle_px'][1]:.0f} px)")
    print("predicted: 2 pallets across -> 1.0, 1 pallet across -> 0.5")
    annotate(); print("saved outputs/end_view.json")
