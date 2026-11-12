"""Step 3: scales, perspective check, lengths and volumes for each clicked frame.
Everything is plain arithmetic on the clicked points. Nothing here picks a winner between the cases."""
import json, numpy as np, cv2

# ---- known sizes (mm) ----
PAL_H = 144                        # EUR pallet height. ASSUMPTION: the pallet really is a EUR pallet
TRUCK_L2, TRUCK_H1 = 3503, 2888    # Linde E60/E80 datasheet rows 4.20 and 4.2 (see README sources)
CASES = {"A one EUR pallet": 1200, "B two pallets in a row": 2400}   # length along the long face (mm)
WIDTHS = (0.8, 1.2)                # m. NOT visible in this view. 0.8 = EUR short side, 1.2 = pallet turned the other way
FOCAL_PX = (800, 1400)             # ASSUMED camera focal length in pixels (about 100 deg .. 70 deg wide on a 1920 px image). Unknown!

def load_points():
    f = lambda p: {k: v for k, v in json.load(open(p)).items()}
    r1, r2 = f("outputs/points_run1.json")["A_01092.jpg"], f("outputs/points_run2.json")["A_01092.jpg"]
    avg = {n: list(np.mean([r1[n], r2[n]], axis=0)) for n in r1 if r1[n] is not None and r2.get(n) is not None}
    return {"1086": f("outputs/points_1086.json")["A_01086.jpg"], "1092": avg, "1098": f("outputs/points_1098.json")["A_01098.jpg"]}

d = lambda p, q: float(np.hypot(p[0] - q[0], p[1] - q[1]))      # distance in px

def measure(P):
    r = {}
    pal_len = d(P["pallet_BL"], P["pallet_BR"])                              # px, long edge of the pallet
    pal_h = (d(P["pallet_BL"], P["pallet_TL"]), d(P["pallet_BR"], P["pallet_TR"]))   # px, left and right end
    load_len = (d(P["load_BL"], P["load_BR"]) + d(P["load_TL"], P["load_TR"])) / 2
    load_h = (d(P["load_BL"], P["load_TL"]), d(P["load_BR"], P["load_TR"]))
    r["px"] = dict(pallet_len=pal_len, pallet_h_left=pal_h[0], pallet_h_right=pal_h[1], load_len=load_len, load_h_left=load_h[0], load_h_right=load_h[1])
    # --- scales, mm per px ---
    s_pal_h = PAL_H / np.mean(pal_h)                                          # vertical, from pallet height (measured at the load)
    s_truck_v = TRUCK_H1 / abs(P["ref_front_wheel_ground"][1] - P["ref_mast_top"][1])      # vertical, from mast height
    s_truck_h = TRUCK_L2 / abs(P["ref_carriage_face"][0] - P["ref_truck_rear"][0])         # horizontal, truck rear -> fork face
    s_len = {c: L / pal_len for c, L in CASES.items()}                         # horizontal, "single scale" from pallet length
    r["scale"] = dict(pallet_height=s_pal_h, truck_vertical=s_truck_v, truck_horizontal=s_truck_h, **{"pallet_length_" + c[0]: v for c, v in s_len.items()})
    # --- load height (m): vertical scale only, so foreshortening does not matter ---
    h_px = np.mean(load_h)
    H = {"pallet144": h_px * s_pal_h / 1000, "truck": h_px * s_truck_v / 1000}
    r["H_m"] = H; H_lo, H_hi = min(H.values()), max(H.values())
    # --- case C: length of the long face (m), with perspective ---
    # The nearer end of the face looks taller. Heights give the distance difference between the two ends:
    #   distance ~ 1/height, so  dZ = Z_left * (h_left/h_right - 1),   and  Z_left = focal * (mm per px at the left end)
    # The face is the diagonal of a right triangle: sideways part Lx (what we measure in px) and depth part dZ.
    rho = load_h[0] / load_h[1]
    LC = {}
    for sname, s_v in (("pallet144", s_pal_h), ("truck", s_truck_v)):
        Lx = load_len * s_v / 1000
        for f in FOCAL_PX:
            z_left = f * s_v * (np.mean(load_h) / load_h[0]) / 1000
            dz = z_left * (rho - 1)
            LC[(sname, f)] = dict(L=float(np.hypot(Lx, dz)), Lx=float(Lx), dz=float(dz), turn_deg=float(np.degrees(np.arctan2(dz, Lx))))
    r["C"] = {f"{k[0]}/f{k[1]}": v for k, v in LC.items()}; r["rho_left_over_right"] = rho
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
    r["V_single_scale"] = {c: {w: (L / 1000) * w * (h_px * s_len[c] / 1000) for w in WIDTHS} for c, L in CASES.items()}   # naive: one scale for both directions
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
