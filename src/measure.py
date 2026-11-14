"""Step 3: scales, perspective check, lengths and volumes for each clicked frame.
Everything is plain arithmetic on the clicked points. Nothing here picks a winner between the cases."""
import json, numpy as np, cv2

# ---- known sizes (mm) ----
PAL_H = 144                        # EUR pallet height. ASSUMPTION: the pallet really is a EUR pallet
TRUCK_L2 = 3503                   # Linde E60/E80 datasheet row 4.20 (see README sources)
TRUCK_H1 = 3213                   # lowered mast height of the mast IN THE VIDEO: 3213 mm (checked in src/mast_check.py from the mast/roof
                                  # ratio and the tyres). 2888 mm (datasheet row 4.2) is only the shortest mast and was the wrong one.
MAST_CLICKS = "outputs/points_mast.json"   # mast_top / mast_floor (floor directly below the mast), clicked with src/annotate_mast.py
CASES = {"A one EUR pallet": 1200, "B two pallets in a row": 2400}   # length along the long face (mm)
WIDTHS = (0.8, 1.2)                # m. NOT visible in this view. 0.8 = EUR short side, 1.2 = pallet turned the other way
FOCAL_PX = (800, 1400)             # ASSUMED camera focal length in pixels (about 100 deg .. 70 deg wide on a 1920 px image). Unknown!

def load_points():
    f = lambda p: {k: v for k, v in json.load(open(p)).items()}
    r1, r2 = f("outputs/points_run1.json")["A_01092.jpg"], f("outputs/points_run2.json")["A_01092.jpg"]
    avg = {n: list(np.mean([r1[n], r2[n]], axis=0)) for n in r1 if r1[n] is not None and r2.get(n) is not None}
    P = {"1086": f("outputs/points_1086.json")["A_01086.jpg"], "1092": avg, "1098": f("outputs/points_1098.json")["A_01098.jpg"]}
    mast = f(MAST_CLICKS)
    for k in P:                                                       # add the mast-ruler clicks (floor directly below the mast)
        m = mast.get(f"A_0{k}.jpg", {})
        if m.get("mast_top") and m.get("mast_floor"): P[k] = dict(P[k], mast_top=m["mast_top"], mast_floor=m["mast_floor"])
    return P

def floor_corr():
    """Old ruler pixels (mast top -> floor under the front wheel) / new ruler pixels (mast top -> floor directly below the mast),
    mean over the frames that have both. About 1.017: the old floor point lies a little lower in the image (wheel is nearer the camera)."""
    r = [old_px(P) / abs(P["mast_floor"][1] - P["mast_top"][1]) for P in load_points().values() if "mast_floor" in P]
    return float(np.mean(r))

old_px = lambda P: abs(P["ref_front_wheel_ground"][1] - P["ref_mast_top"][1])

def truck_px(P):
    """Pixel length of the height ruler (mast, h1 = TRUCK_H1). Returns (main, low_end):
    main    = mast top -> floor directly below the mast (clicked; for frames without that click: old ruler / floor_corr())
    low_end = mast top -> floor under the front wheel (old ruler, a little longer in pixels -> smaller heights)."""
    if P.get("mast_floor") and P.get("mast_top"): return abs(P["mast_floor"][1] - P["mast_top"][1]), old_px(P)
    return old_px(P) / floor_corr(), old_px(P)

def truck_scale(P):
    """mm per px from the mast: (main, low_end)."""
    main, low = truck_px(P); return TRUCK_H1 / main, TRUCK_H1 / low

d = lambda p, q: float(np.hypot(p[0] - q[0], p[1] - q[1]))      # distance in px

def measure(P):
    r = {}
    pal_len = d(P["pallet_BL"], P["pallet_BR"])                              # px, long edge of the pallet
    pal_h = (d(P["pallet_BL"], P["pallet_TL"]), d(P["pallet_BR"], P["pallet_TR"]))   # px, left and right end
    load_len = (d(P["load_BL"], P["load_BR"]) + d(P["load_TL"], P["load_TR"])) / 2
    load_h = (d(P["load_BL"], P["load_TL"]), d(P["load_BR"], P["load_TR"]))
    r["px"] = dict(pallet_len=pal_len, pallet_h_left=pal_h[0], pallet_h_right=pal_h[1], load_len=load_len, load_h_left=load_h[0], load_h_right=load_h[1])
    # --- scales, mm per px ---
    s_pal_h = PAL_H / pal_h[0]                                                # vertical, from pallet height at the LEFT end (next to the mast)
    s_truck_v, s_truck_low = truck_scale(P)                                  # vertical, from mast height (main: floor below the mast; low end: old floor point)
    s_truck_h = TRUCK_L2 / abs(P["ref_carriage_face"][0] - P["ref_truck_rear"][0])         # horizontal, truck rear -> fork face
    s_len = {c: L / pal_len for c, L in CASES.items()}                         # horizontal, "single scale" from pallet length
    r["scale"] = dict(pallet_height=s_pal_h, truck_vertical=s_truck_v, truck_vertical_low=s_truck_low, truck_horizontal=s_truck_h, **{"pallet_length_" + c[0]: v for c, v in s_len.items()})
    # --- load height (m): height of the LEFT edge (next to the mast/carriage) x the vertical scale valid at that depth ---
    h_l, h_r = load_h; rho = h_l / h_r                      # rho < 1: the right end is nearer to the camera
    H = {"pallet144": h_l * s_pal_h / 1000, "truck": h_l * s_truck_v / 1000}
    r["H_m"] = H; r["H_truck_low_m"] = h_l * s_truck_low / 1000; H_lo, H_hi = min(H.values()), max(H.values()); r["rho_left_over_right"] = rho
    # --- case C: length of the long face (m), with perspective ---
    # The scale at the right end is s_R = s_L * h_left / h_right (a box has equal edge heights). Sideways part Lx = pixels x mean scale.
    # Depth part dz = difference of the distances of the two ends = focal * (s_R - s_L)   (distance = focal * mm-per-px).
    # The face is the diagonal of the right triangle (Lx, dz).
    LC = {}
    for sname, s_L in (("pallet144", s_pal_h), ("truck", s_truck_v)):
        s_R = s_L * rho; Lx = load_len * (s_L + s_R) / 2 / 1000
        for f in FOCAL_PX:
            dz = f * abs(s_R - s_L) / 1000
            LC[(sname, f)] = dict(L=float(np.hypot(Lx, dz)), Lx=float(Lx), dz=float(dz), turn_deg=float(np.degrees(np.arctan2(dz, Lx))))
    r["C"] = {f"{k[0]}/f{k[1]}": v for k, v in LC.items()}
    r["L_C_m"] = (min(v["L"] for v in LC.values()), max(v["L"] for v in LC.values()))
    # --- vertical-plane homography: map the pallet FRONT FACE quad to a (length x 144 mm) rectangle ---
    homog = {}
    src = np.float32([P["pallet_BL"], P["pallet_BR"], P["pallet_TR"], P["pallet_TL"]])
    for c, L in CASES.items():
        M = cv2.getPerspectiveTransform(src, np.float32([[0, 0], [L, 0], [L, PAL_H], [0, PAL_H]]))
        q = cv2.perspectiveTransform(np.float32([[P[k] for k in ("load_BL", "load_BR", "load_TR", "load_TL")]]), M)[0]
        homog[c] = dict(length_mm=float((np.hypot(*(q[1] - q[0])) + np.hypot(*(q[2] - q[3]))) / 2), height_mm=float((abs(q[3][1] - q[0][1]) + abs(q[2][1] - q[1][1])) / 2))
    r["homography"] = homog
    # --- volumes (m3), load only. L from the case, H from the vertical scales (range), W from WIDTHS ---
    V = {}
    for c, L in CASES.items():
        V[c] = {w: (L / 1000 * w * H_lo, L / 1000 * w * H_hi) for w in WIDTHS}
    vc = lambda w: [v["L"] * w * H[k[0]] for k, v in LC.items()]      # each length paired with the height from the SAME scale
    V["C measured length"] = {w: (min(vc(w)), max(vc(w))) for w in WIDTHS}
    r["V_load_only"] = V
    r["V_single_scale"] = {c: {w: (L / 1000) * w * (np.mean(load_h) * s_len[c] / 1000) for w in WIDTHS} for c, L in CASES.items()}   # naive: one scale for both directions
    r["pallet_ratio_len_over_h"] = pal_len / np.mean(pal_h)
    return r

if __name__ == "__main__":
    res = {k: measure(P) for k, P in load_points().items()}
    json.dump(res, open("outputs/measure_step3.json", "w"), indent=1, default=float)
    for k, r in res.items():
        print(f"\n===== frame #{k} =====")
        px = r["px"]; print("px:", {a: round(b, 1) for a, b in px.items()})
        print("scales mm/px:", {a: round(float(b), 2) for a, b in r["scale"].items()})
        print(f"pallet long edge / pallet height = {r['pallet_ratio_len_over_h']:.1f}  (a real EUR face: 1200/144 = 8.3 for A, 2400/144 = 16.7 for B)")
        print("load height m:", {a: round(float(b), 2) for a, b in r["H_m"].items()}, "| case C length m: %.2f .. %.2f" % r["L_C_m"])
        print(f"left/right height ratio of the load face {r['rho_left_over_right']:.3f};  case C pieces:", {k: (round(v['Lx'], 2), round(v['dz'], 2), round(v['turn_deg'])) for k, v in r['C'].items()}, "(Lx m, dZ m, turn deg)")
        print("homography, load face in mm:", {c: (round(v["length_mm"]), round(v["height_mm"])) for c, v in r["homography"].items()})
        for c, byw in r["V_load_only"].items(): print(f"  V load only  {c:24s}", {w: f"{a:.2f}-{b:.2f}" for w, (a, b) in byw.items()}, "m3")
        for c, byw in r["V_single_scale"].items(): print(f"  V single-scale (naive) {c[:1]}", {w: f"{v:.2f}" for w, v in byw.items()}, "m3")
    # ---- do the frames agree with each other? (spread = max-min relative to the mean) ----
    print("\n===== spread across the 3 frames (they are only 0.1-0.24 s apart, so errors are correlated) =====")
    def spread(name, vals):
        v = np.array(vals); print(f"{name:42s} " + "  ".join(f"{x:6.2f}" for x in v) + f"   spread {100 * (v.max() - v.min()) / v.mean():4.1f}%")
    R = list(res.values())
    spread("height m (pallet-144 scale)", [r["H_m"]["pallet144"] for r in R]); spread("height m (truck scale)", [r["H_m"]["truck"] for r in R])
    spread("pallet-height scale mm/px", [r["scale"]["pallet_height"] for r in R]); spread("truck-vertical scale mm/px", [r["scale"]["truck_vertical"] for r in R])
    spread("pallet-vs-truck scale ratio", [r["scale"]["pallet_height"] / r["scale"]["truck_vertical"] for r in R])
    spread("case C length m, low end", [r["L_C_m"][0] for r in R]); spread("case C length m, high end", [r["L_C_m"][1] for r in R])
    for c in CASES:
        spread(f"V {c[:1]} W=0.8, low end", [r["V_load_only"][c][0.8][0] for r in R]); spread(f"V {c[:1]} W=0.8, high end", [r["V_load_only"][c][0.8][1] for r in R])
    spread("V C W=0.8, low end", [r["V_load_only"]["C measured length"][0.8][0] for r in R]); spread("V C W=0.8, high end", [r["V_load_only"]["C measured length"][0.8][1] for r in R])
