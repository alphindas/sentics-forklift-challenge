"""Step 4: Monte Carlo (10,000 runs) for the load volume. D (3 pallets, from the crate counts) is the most likely scenario, but it is not proven; B (length from the crate count, height from crate heights) and C (length from clicks + truck geometry) are kept for comparison. A (one EUR pallet) is excluded by the clicks.
Plain idea: every input that we are not sure about gets a range; each run draws one value for each, computes the volume, and we
look at the spread of the 10,000 results. All ranges are ASSUMPTIONS written in README.md. Nothing here decides which case is true.
Clicks vary independently per frame; the other inputs (scale bias, lens, fill, tolerances) are shared by the three frames, because
the frames are 0.1-0.24 s apart and share the same systematic errors."""
import json, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from measure import load_points, PAL_H, TRUCK_H1

N = 10_000
SHARP = {"load_BL", "load_BR", "load_TL", "load_TR", "ref_mast_top", "ref_carriage_face", "pallet_BL", "pallet_BR"}   # click error 2-5 px
BLURRY_SD = 10.0                                                                                                         # all other points
NEED = ["load_BL", "load_BR", "load_TL", "load_TR", "ref_mast_top", "ref_front_wheel_ground", "pallet_BL", "pallet_BR", "pallet_TL", "pallet_TR"]
PALLET_V = PAL_H / 1000                      # m, pallet height used for "load + pallets"
RANGES = {   # (low, high) uniform unless noted. ALL ASSUMED, see README.
    "scale_bias": (-0.10, 0.10),   # truck scale: mast and wheel are at different depths -> +-10 % (assumed)
    "fill":       (0.90, 1.00),    # share of the bounding box that is really filled (crate stack with small gaps)
    "focal_px":   (800, 1400),     # lens; upper end from the truck geometry (src/focal check), lower end = wide-angle guess
    "gap_m":      (0.0, 0.03),     # gap between two pallets in a row (case B only)
    "tol_m":      0.003,           # sd of one EUR pallet length/width tolerance (assumed +-3 mm)
}
NOMINAL = {"scale_bias": 0.0, "fill": 0.95, "focal_px": 1100, "gap_m": 0.015, "tol_m": 0.0}
INPUTS = ["clicks", "scale_bias", "fill", "pallet_size", "focal"]      # groups shown in the bar chart

def simulate(case, vary, width=0.8, scale="truck", seed=1):
    """Return dict of arrays (N runs) pooled (mean) over the 3 frames, plus per-frame volumes."""
    rng = np.random.default_rng(seed); U = lambda r: rng.uniform(*r, N)
    on = lambda g: g in vary
    bias = U(RANGES["scale_bias"]) if on("scale_bias") else np.zeros(N)
    fill = U(RANGES["fill"]) if on("fill") else np.full(N, NOMINAL["fill"])
    focal = U(RANGES["focal_px"]) if on("focal") else np.full(N, NOMINAL["focal_px"])
    tol = RANGES["tol_m"] if on("pallet_size") else 0.0
    gap = U(RANGES["gap_m"]) if on("pallet_size") else np.full(N, NOMINAL["gap_m"])
    w = width + rng.normal(0, tol, N)
    L_case = {"A": 1.2 + rng.normal(0, tol, N), "B": 2 * 1.2 + rng.normal(0, tol, N) + rng.normal(0, tol, N) + gap}
    sd_sharp = rng.uniform(2, 5, N) if on("clicks") else np.zeros(N)            # per run: how sloppy are sharp clicks (2-5 px)
    out = {"V": [], "Vp": [], "H": [], "L": []}
    for k, P in load_points().items():
        pt = {}
        for n in NEED:                                   # each clicked point + a random click error (px) in x and y
            sd = sd_sharp if n in SHARP else np.full(N, BLURRY_SD)
            noise = rng.normal(0, 1, (N, 2)) * sd.reshape(-1, 1) if on("clicks") else np.zeros((N, 2))
            pt[n] = np.array(P[n], float) + noise
        dist = lambda a, b: np.hypot(*(pt[a] - pt[b]).T)
        hl, hr = dist("load_BL", "load_TL"), dist("load_BR", "load_TR")
        if scale == "truck":                      # height ruler: mast height / pixels from mast top to floor under the front wheel (valid at the LEFT end)
            s_L = TRUCK_H1 / np.abs(pt["ref_front_wheel_ground"][:, 1] - pt["ref_mast_top"][:, 1]) * (1 + bias)
        else:                                     # weak cross-check: pallet height 144 mm on ~30 px at the left end
            s_L = PAL_H / dist("pallet_BL", "pallet_TL")
        H = hl * s_L / 1000
        if case == "C":                           # measured length with perspective (see measure.py)
            ll = (dist("load_BL", "load_BR") + dist("load_TL", "load_TR")) / 2
            s_R = s_L * hl / hr
            L = np.hypot(ll * (s_L + s_R) / 2 / 1000, focal * np.abs(s_R - s_L) / 1000)
        else: L = L_case[case]
        V = L * w * H * fill; out["V"].append(V); out["Vp"].append(V + L * w * PALLET_V); out["H"].append(H); out["L"].append(L)
    return {k: np.array(v) for k, v in out.items()}

def q(x): return dict(median=float(np.median(x)), p10=float(np.percentile(x, 10)), p90=float(np.percentile(x, 90)), p2_5=float(np.percentile(x, 2.5)), p97_5=float(np.percentile(x, 97.5)))
fmt = lambda s: f"{s['median']:.2f}  (80%: {s['p10']:.2f}-{s['p90']:.2f} | 95%: {s['p2_5']:.2f}-{s['p97_5']:.2f})"

def scenario_B_from_crates(width=0.8, seed=2):
    """Scenario B, self-consistent version: length from the CRATE COUNT (8 crates x 0.300 m = two EUR pallets), height from
    4 layers x crate height, where the crate height is NOT measured in the image. 0.29-0.36 m is the range of 12-bottle and 20 x 0.5 l crates
    in the Delbrouck catalogue (crate type of the video is NOT verified). The image only supplies the count (4 layers, 8 crates)."""
    rng = np.random.default_rng(seed)
    L = 8 * 0.300 + rng.normal(0, 0.003, N); w = width + rng.normal(0, RANGES["tol_m"], N)
    H = 4 * rng.uniform(0.29, 0.36, N); fill = rng.uniform(*RANGES["fill"], N)
    V = L * w * H * fill; return {"V": V, "Vp": V + L * w * PALLET_V, "H": H, "L": L}

def scenario_D(seed=3):
    """Scenario D: 3 EUR pallets in a row with the 800 mm side along the forks (L = 3 x 0.8 m), 3 crates of 400 mm across (W = 1.2 m),
    4 layers of a 12 x 0.75 L crate 400 x 266 x 310-333 mm (Delbrouck catalogue; crate of the video NOT verified). Image supplies only the counts."""
    rng = np.random.default_rng(seed)
    L = 3 * 0.800 + rng.normal(0, 0.003, N) + rng.uniform(0, 0.03, N) * 2; w = 1.2 + rng.normal(0, RANGES["tol_m"], N)
    H = 4 * rng.uniform(0.310, 0.333, N); fill = rng.uniform(*RANGES["fill"], N); V = L * w * H * fill
    crates = 108 * 0.400 * 0.266 * rng.uniform(0.310, 0.333, N)           # second estimate: 108 crates x crate volume (no gaps, no fill)
    return {"V": V, "Vp": V + 3 * 0.8 * 1.2 * PALLET_V, "H": H, "L": L, "V_crates": crates}

if __name__ == "__main__":
    ALL = set(INPUTS); res = {}
    names = {"B": "B-with-image-scale (2.4 m long but 4 layers of 290 mm: NOT self-consistent, kept only for comparison)", "A": "A one EUR pallet (EXCLUDED by the clicks)", "C": "C length from clicks + truck geometry"}
    print("Median and ranges in m3, pooled over the 3 frames, width 0.8 m, truck scale\n")
    for c in "BAC":
        r = simulate(c, ALL); res[c] = {"load_only": q(r["V"].mean(0)), "load_plus_pallets": q(r["Vp"].mean(0)), "height_m": q(r["H"].mean(0)), "length_m": q(r["L"].mean(0)),
                                        "per_frame_median_load_only": [float(np.median(v)) for v in r["V"]]}
        print(f"{names[c]}\n   load only        {fmt(res[c]['load_only'])}\n   load + pallets   {fmt(res[c]['load_plus_pallets'])}")
        print(f"   height {res[c]['height_m']['median']:.2f} m | length {res[c]['length_m']['median']:.2f} m | per-frame medians (#1086, #1092, #1098): {[round(x, 2) for x in res[c]['per_frame_median_load_only']]}")
    rb = scenario_B_from_crates(); res["B_crates"] = {"load_only": q(rb["V"]), "load_plus_pallets": q(rb["Vp"]), "height_m": q(rb["H"]), "length_m": q(rb["L"])}
    print(f"SCENARIO B from crate count (L 2.4 m, H = 4 x 0.29-0.36 m, no image scale)\n   load only        {fmt(res['B_crates']['load_only'])}\n   load + pallets   {fmt(res['B_crates']['load_plus_pallets'])}")
    rd = scenario_D(); res["D"] = {"load_only": q(rd["V"]), "load_plus_pallets": q(rd["Vp"]), "height_m": q(rd["H"]), "length_m": q(rd["L"]), "crates_x_crate_volume": q(rd["V_crates"])}
    print(f"SCENARIO D (3 pallets, 800 mm side along the forks: 2.4 m x 1.2 m, 4 layers of 310-333 mm)\n   load only        {fmt(res['D']['load_only'])}\n   load + pallets   {fmt(res['D']['load_plus_pallets'])}\n   second estimate, 108 crates x crate volume {fmt(res['D']['crates_x_crate_volume'])}")
    print("\nScenarios outside the main range (NOT mixed into it):")
    scen = {"B_crates": {"width_1.2": q(scenario_B_from_crates(1.2)["V"])}}
    print(f"  SCENARIO B (crate count): width 1.2 m -> {fmt(scen['B_crates']['width_1.2'])}")
    for c in "BAC":
        scen[c] = {"width_1.2": q(simulate(c, ALL, width=1.2)["V"].mean(0)), "pallet_height_scale": q(simulate(c, ALL, scale="pallet")["V"].mean(0))}
        print(f"  {c}: width 1.2 m -> {fmt(scen[c]['width_1.2'])} | height from pallet-height scale -> {fmt(scen[c]['pallet_height_scale'])}")
    # ---- which input matters most: let ONE input vary, others fixed; spread = half of the 80% range / median ----
    sens = {}
    for c in "BC":
        base = {g: (q(simulate(c, {g})["V"].mean(0))) for g in INPUTS}
        sens[c] = {g: 100 * (b["p90"] - b["p10"]) / 2 / b["median"] for g, b in base.items()}
        sens[c]["all together"] = 100 * (res[c]["load_only"]["p90"] - res[c]["load_only"]["p10"]) / 2 / res[c]["load_only"]["median"]
    print("\nSpread caused by each input alone (half of the 80% range, in % of the median):"); [print(f"  {c}: " + ", ".join(f"{g} {v:.1f}%" for g, v in s.items())) for c, s in sens.items()]
    # weak cross-check: why the pallet-height scale is weak
    r = simulate("B", {"clicks"}, scale="pallet"); r2 = simulate("B", {"clicks"}); print(f"\nclick error alone on the PALLET-height scale -> height spread {100*np.std(r['H'].mean(0))/np.mean(r['H']):.1f}% ; on the TRUCK scale -> {100*np.std(r2['H'].mean(0))/np.mean(r2['H']):.1f}%")
    json.dump({"main_case": res, "scenarios": scen, "sensitivity_pct": sens, "ranges": RANGES, "runs": N}, open("outputs/uncertainty.json", "w"), indent=1)
    # ---- figures ----
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.6), sharex=True)
    for a, c in zip(ax, "BC"):
        s = sens[c]; ks = sorted(s, key=s.get); a.barh(ks, [s[k] for k in ks], color=["#444" if k == "all together" else "#3a7" for k in ks]); a.set_title(f"Case {c}: spread caused by one input alone"); a.set_xlabel("half of 80% range, % of median volume")
    plt.tight_layout(); plt.savefig("outputs/uncertainty_bars.png", dpi=130); plt.close()
    fig, a = plt.subplots(figsize=(8, 3.8))
    for lab, v, col in (("A one EUR pallet (excluded)", simulate("A", ALL)["V"].mean(0), "#c63"), ("C: clicks + truck geometry", simulate("C", ALL)["V"].mean(0), "#3a7"), ("B: 2 pallets in a row, 8 x 300 mm crates (2.4 m x 0.8 m)", scenario_B_from_crates()["V"], "#37a"), ("D: 3 pallets (2.4 m x 1.2 m)", scenario_D()["V"], "#a37")):
        a.hist(v, bins=80, alpha=0.6, color=col, label=lab)
    a.set_xlabel("load-only volume, m3 (width 0.8 m for A, B, C; 1.2 m for D)"); a.set_ylabel("runs out of 10,000"); a.set_ylim(0, a.get_ylim()[1] * 1.35); a.legend(loc="upper center", ncol=2, fontsize=8); plt.tight_layout(); plt.savefig("outputs/volume_hist.png", dpi=130); plt.close()
    fig, a = plt.subplots(figsize=(6, 3.4)); pf = simulate("C", ALL)["V"]
    for i, (k, col) in enumerate(zip(("#1086", "#1092", "#1098"), ("#c63", "#37a", "#3a7"))): a.hist(pf[i], bins=60, alpha=0.5, color=col, label=k)
    a.set_xlabel("case C load-only volume, m3, per frame"); a.legend(); plt.tight_layout(); plt.savefig("outputs/frames_spread.png", dpi=130); plt.close()
    print("\nsaved outputs/uncertainty.json, uncertainty_bars.png, volume_hist.png, frames_spread.png")
