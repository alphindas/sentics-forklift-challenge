"""Step 3: pallet checks with the 3213 mm mast. Writes outputs/pallet_checks.json. Changes no other result.

(a) truck scale vs pallet-height scale (EUR pallet 144 mm), and the pallet ruler's own click spread
(b) the same gap if the pallets were 166 mm drinks-industry pallets
(c) every length estimate of the long face with the new scale
(d) crate-shape check: crate width implied by the measured cell width/height ratio x the measured layer height, x 9 columns
Compared with 2.4 m (3 EUR pallets, 800 mm side along the face) and 3.0-3.3 m (3 drinks-industry pallets: 1000 x 1200 or 1100 x 1070 mm).
"""
import json, numpy as np
from measure import measure, load_points, PAL_H
import early_frames                                   # #999 points, ESTIMATED BY EYE (not clicked)

PAL_DRINKS = 166                                     # mm, German drinks-industry pallet height
CELL_RATIO = (0.81, 0.91)                            # apparent crate cell width/height in the image (window pitch, README consistency table)
TURN_DEG = (22, 25)                                  # turn of the face (Method step 4); the apparent width is shortened by cos(turn)
COLUMNS = 9
TARGETS = {"3 EUR pallets (800 side)": (2.4, 2.4), "3 drinks pallets (1000/1070/1100 side)": (3.0, 3.3)}

def pallet_ruler_click_spread():
    """80 % half-range of the height from the pallet ruler with click error only (same click model as uncertainty.py)."""
    import uncertainty as u
    H = u.simulate("B", {"clicks"}, scale="pallet")["H"].mean(0); p10, p50, p90 = np.percentile(H, [10, 50, 90])
    return float((p90 - p10) / 2 / p50)

def main():
    out = {"a_gap_eur144": {}, "b_gap_drinks166": {}, "c_lengths_m": {}, "d_crate_shape": {}}
    R = {k: measure(P) for k, P in load_points().items()}
    for k, r in R.items():
        s = r["scale"]; g = s["pallet_height"] / s["truck_vertical"] - 1; g_low = s["pallet_height"] / s["truck_vertical_low"] - 1
        out["a_gap_eur144"][k] = [g, g_low]                                       # main ruler, old-floor ruler
        out["b_gap_drinks166"][k] = [(1 + g) * PAL_DRINKS / PAL_H - 1, (1 + g_low) * PAL_DRINKS / PAL_H - 1]
        lt = [v["L"] for kk, v in r["C"].items() if kk.startswith("truck")]; lp = [v["L"] for kk, v in r["C"].items() if kk.startswith("pallet")]
        f_low = s["truck_vertical_low"] / s["truck_vertical"]
        out["c_lengths_m"][f"#{k} truck ruler (clicked)"] = [min(lt) * f_low, max(lt)]
        out["c_lengths_m"][f"#{k} pallet ruler (clicked)"] = [min(lp), max(lp)]
    out["pallet_ruler_click_spread"] = pallet_ruler_click_spread()
    nf = json.load(open("outputs/new_frames.json"))["1068"]
    out["c_lengths_m"]["#1068 lower bound, truck ruler (clicked; +-15 % for the depth of the right end)"] = [nf["Lx_lower_bound_low_m"], nf["Lx_lower_bound_m"]]
    r99 = early_frames.r99
    for sc, nm in (("truck", "truck ruler"), ("pallet144", "pallet ruler")):
        L = [v["L"] for kk, v in r99["C"].items() if kk.startswith(sc)]
        out["c_lengths_m"][f"#999 {nm} (points ESTIMATED BY EYE, not clicked)"] = [min(L), max(L)]
    # (d) crate shape: layer height from the truck ruler, 3 clicked frames (main and old-floor ruler)
    layer = [r["H_truck_low_m"] / 4 for r in R.values()] + [r["H_m"]["truck"] / 4 for r in R.values()]
    lay = (min(layer), max(layer))
    w_app = (CELL_RATIO[0] * lay[0], CELL_RATIO[1] * lay[1])
    w_turn = (w_app[0] / np.cos(np.radians(TURN_DEG[0])), w_app[1] / np.cos(np.radians(TURN_DEG[1])))
    out["d_crate_shape"] = dict(layer_height_m=lay, crate_width_m_as_seen=w_app, face_length_m_as_seen=[9 * w for w in w_app],
                                crate_width_m_turn_corrected=w_turn, face_length_m_turn_corrected=[9 * w for w in w_turn])
    out["targets_m"] = TARGETS
    json.dump(out, open("outputs/pallet_checks.json", "w"), indent=1, default=float)
    pct = lambda v: f"{100 * v:+.0f} %"
    print(f"(a) pallet-height scale (EUR 144 mm) vs truck scale, per frame [main ruler, old-floor ruler]:")
    for k, (g, gl) in out["a_gap_eur144"].items(): print(f"    #{k}: {pct(g)}, {pct(gl)}")
    print(f"    pallet ruler's own click spread (80 % half-range, Monte Carlo click model): {100 * out['pallet_ruler_click_spread']:.0f} %")
    print(f"(b) same gap if the pallets were 166 mm drinks pallets:")
    for k, (g, gl) in out["b_gap_drinks166"].items(): print(f"    #{k}: {pct(g)}, {pct(gl)}")
    print("(c) length of the long face, m:")
    for k, (a, b) in out["c_lengths_m"].items(): print(f"    {k:80s} {a:.2f}-{b:.2f}")
    d = out["d_crate_shape"]
    print(f"(d) layer height {d['layer_height_m'][0]*1000:.0f}-{d['layer_height_m'][1]*1000:.0f} mm x cell ratio {CELL_RATIO[0]}-{CELL_RATIO[1]}"
          f" -> crate width {d['crate_width_m_as_seen'][0]*1000:.0f}-{d['crate_width_m_as_seen'][1]*1000:.0f} mm as seen,"
          f" x 9 = {d['face_length_m_as_seen'][0]:.2f}-{d['face_length_m_as_seen'][1]:.2f} m;"
          f" turn-corrected (22-25 deg): {d['crate_width_m_turn_corrected'][0]*1000:.0f}-{d['crate_width_m_turn_corrected'][1]*1000:.0f} mm,"
          f" x 9 = {d['face_length_m_turn_corrected'][0]:.2f}-{d['face_length_m_turn_corrected'][1]:.2f} m")
    print("targets:", TARGETS)

if __name__ == "__main__":
    main()
