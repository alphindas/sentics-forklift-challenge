"""Mast check: which mast does the truck have? Reads outputs/points_mast.json (clicked with src/annotate_mast.py).
Writes outputs/mast_check.json. Changes NO other result: it only reports what a different mast would change.

Known sizes (Linde E60/E80 datasheet, series 1279):
  h6 cabin roof (overhead guard) = 2838 mm;  tyres 315/70-15 front and rear: 2*315*0.70 + 15*25.4 = 822 mm diameter
  h1 lowered mast heights: 2863, 2888 (used so far), 3013, 3213, 3363, 3563, 3963 mm

Perspective: front and rear tyre have the same real size, so their pixel heights give the scale (px per mm) at two places along
the truck. In a pinhole image the scale of points on one straight 3D line is linear in the image x coordinate, so the scale at the
mast and at the roof point is interpolated (or extrapolated) linearly in x between the two tyres.
Limits: tyres sit on the near side of the truck, mast and roof are nearer the centre line (a bit further away -> the tyre scale
overestimates their height by a few %, roughly the same for both, so the mast/roof RATIO is affected much less than the absolute heights);
loaded tyres are squashed by some %, which also makes the tyre-based absolute heights too high.
"""
import json, os, numpy as np

H6, TYRE = 2838.0, 2 * 315 * 0.70 + 15 * 25.4          # mm
MASTS = [2863, 2888, 3013, 3213, 3363, 3563, 3963]      # h1 lowered, mm
H1_USED = 2888.0
CLICK_SD = 3.0                                          # px, assumed click error for the range (sharp points 2-5 px)
GAP_NOW = (0.22, 0.27)                                  # README: pallet scale larger than truck scale by 22-27 %
H_LOAD_NOW = 1.25                                       # m, load height with the truck scale (left end, mean of #1086-#1098)

def analyse(P):
    """P: dict name -> [x, y]. Returns ratios, perspective-corrected heights and the best-fitting mast."""
    y = lambda a, b: abs(P[a][1] - P[b][1])
    xm = lambda a, b: (P[a][0] + P[b][0]) / 2
    mast_px, roof_px = y("mast_top", "mast_floor"), y("roof_top", "roof_floor")
    tf_px, tr_px = np.hypot(*np.subtract(P["ftyre_top"], P["ftyre_bottom"])), np.hypot(*np.subtract(P["rtyre_top"], P["rtyre_bottom"]))
    xf, xr = xm("ftyre_top", "ftyre_bottom"), xm("rtyre_top", "rtyre_bottom")
    kf, kr = tf_px / TYRE, tr_px / TYRE                                          # px per mm at the two tyres
    k = lambda x: kf + (kr - kf) * (x - xf) / (xr - xf)                          # px per mm along the truck
    k_mast, k_roof = k(xm("mast_top", "mast_floor")), k(xm("roof_top", "roof_floor"))
    mast_mm, roof_mm = mast_px / k_mast, roof_px / k_roof
    return dict(mast_px=mast_px, roof_px=roof_px, front_tyre_px=tf_px, rear_tyre_px=tr_px,
                ratio_mast_roof_raw=mast_px / roof_px, ratio_mast_front_tyre_raw=mast_px / tf_px, ratio_front_rear_tyre=tf_px / tr_px,
                ratio_mast_roof_corr=mast_mm / roof_mm, mast_mm_tyre_scale=mast_mm, roof_mm_tyre_scale=roof_mm,
                roof_check=roof_mm / H6)                                         # 1.00 = tyre scale agrees with the datasheet roof

def best_mast(ratio):
    table = np.array(MASTS) / H6
    return MASTS[int(np.argmin(abs(table - ratio)))]

def with_click_error(P, n=2000, seed=0):
    rng = np.random.default_rng(seed); out = []
    for _ in range(n):
        Q = {k: list(np.add(v, rng.normal(0, CLICK_SD, 2))) for k, v in P.items()}
        r = analyse(Q); out.append((r["ratio_mast_roof_corr"], r["mast_mm_tyre_scale"]))
    return np.array(out)

def impact(h1):
    """What changes if the mast is h1 instead of 2888 mm. Truck scale (mm/px) is proportional to h1."""
    f = h1 / H1_USED
    return dict(scale_factor=f, load_height_m=H_LOAD_NOW * f, per_layer_mm=H_LOAD_NOW * f / 4 * 1000,
                pallet_vs_truck_gap_pct=[round(((1 + g) / f - 1) * 100, 1) for g in GAP_NOW],
                C_volume_factor=f ** 2, A_and_B_image_height_factor=f, D_and_B_crates_factor=1.0)

def impact_table():
    return {m: impact(m) for m in MASTS}

if __name__ == "__main__":
    src = "outputs/points_mast.json"
    clicks = json.load(open(src)) if os.path.exists(src) else {}
    res = {"frames": {}, "impact_if_mast_is": impact_table()}
    need = ["mast_top", "mast_floor", "roof_top", "roof_floor", "ftyre_top", "ftyre_bottom", "rtyre_top", "rtyre_bottom"]
    for key, P in sorted(clicks.items()):
        if any(P.get(n) is None for n in need):
            print(f"{key}: some points missing or not visible, skipped"); continue
        r = analyse(P); mc = with_click_error(P)
        r["ratio_corr_p10_p90"] = [float(np.percentile(mc[:, 0], 10)), float(np.percentile(mc[:, 0], 90))]
        r["mast_mm_p10_p90"] = [float(np.percentile(mc[:, 1], 10)), float(np.percentile(mc[:, 1], 90))]
        r["best_mast_by_ratio"] = best_mast(r["ratio_mast_roof_corr"])
        r["best_mast_by_tyre_scale"] = MASTS[int(np.argmin([abs(m - r["mast_mm_tyre_scale"]) for m in MASTS]))]
        res["frames"][key] = r
        print(f"\n== {key} ==")
        print(f"  px: mast {r['mast_px']:.0f}, roof {r['roof_px']:.0f}, front tyre {r['front_tyre_px']:.1f}, rear tyre {r['rear_tyre_px']:.1f}")
        print(f"  mast/roof raw {r['ratio_mast_roof_raw']:.3f} -> perspective-corrected {r['ratio_mast_roof_corr']:.3f} "
              f"(80 %: {r['ratio_corr_p10_p90'][0]:.3f}-{r['ratio_corr_p10_p90'][1]:.3f})  -> best mast {r['best_mast_by_ratio']} mm")
        print(f"  mast/front tyre raw {r['ratio_mast_front_tyre_raw']:.2f};  front/rear tyre {r['ratio_front_rear_tyre']:.3f}")
        print(f"  tyre scale: mast {r['mast_mm_tyre_scale']:.0f} mm (80 %: {r['mast_mm_p10_p90'][0]:.0f}-{r['mast_mm_p10_p90'][1]:.0f}), "
              f"roof {r['roof_mm_tyre_scale']:.0f} mm (datasheet 2838, check {r['roof_check']:.3f}) -> best mast {r['best_mast_by_tyre_scale']} mm")
    if res["frames"]:
        rs = [r["ratio_mast_roof_corr"] for r in res["frames"].values()]
        res["pooled"] = dict(ratio_corr_mean=float(np.mean(rs)), best_mast=best_mast(float(np.mean(rs))))
        print(f"\npooled mast/roof (corrected) {np.mean(rs):.3f} -> best mast {res['pooled']['best_mast']} mm")
    else:
        print("no clicks yet: run  python src/annotate_mast.py frames/A_01092.jpg  (and A_01086.jpg, A_01098.jpg)")
    print("\nh1/h6 table:", {m: round(m / H6, 3) for m in MASTS})
    print("\nimpact if the mast is h1 (nothing is changed in the results):")
    for m, d in res["impact_if_mast_is"].items():
        print(f"  {m} mm: scale x{d['scale_factor']:.3f}, load height {d['load_height_m']:.2f} m ({d['per_layer_mm']:.0f} mm/layer), "
              f"pallet-vs-truck gap {d['pallet_vs_truck_gap_pct'][0]:+.1f}..{d['pallet_vs_truck_gap_pct'][1]:+.1f} %, "
              f"C volume x{d['C_volume_factor']:.2f}, D unchanged")
    json.dump(res, open("outputs/mast_check.json", "w"), indent=1, default=float)
