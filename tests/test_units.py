"""Unit tests for the small formulas (scale, height, volume, perspective)."""
import sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from measure import measure, d, TRUCK_H1, PAL_H, truck_px, floor_corr

def points(h_left, h_right, length_px, mast_px=902.0):
    """Flat clicked rectangle-ish face with given pixel sizes (no real camera)."""
    P = {"pallet_BL": (0, 1000), "pallet_BR": (length_px, 1000), "pallet_TL": (0, 1000 - 30), "pallet_TR": (length_px, 1000 - 30),
         "load_BL": (0, 1000), "load_BR": (length_px, 1000), "load_TL": (0, 1000 - h_left), "load_TR": (length_px, 1000 - h_right),
         "ref_mast_top": (0, 100), "ref_front_wheel_ground": (0, 100 + mast_px), "ref_carriage_face": (500, 900), "ref_truck_rear": (-500, 900),
         "mast_top": (0, 100), "mast_floor": (0, 100 + mast_px)}
    return P

def test_distance():
    assert d((0, 0), (3, 4)) == 5.0

def test_truck_scale_is_mast_over_pixels():
    r = measure(points(400, 400, 800, mast_px=902.0))
    assert abs(r["scale"]["truck_vertical"] - TRUCK_H1 / 902.0) < 1e-9

def test_height_is_pixels_times_scale():
    r = measure(points(400, 400, 800, mast_px=902.0))
    assert abs(r["H_m"]["truck"] - 400 * TRUCK_H1 / 902.0 / 1000) < 1e-9

def test_pallet_scale_is_144_over_pixels():
    r = measure(points(400, 400, 800))
    assert abs(r["scale"]["pallet_height"] - PAL_H / 30) < 1e-9

def test_equal_edge_heights_mean_frontal_face_no_depth_part():
    r = measure(points(400, 400, 800))
    for v in r["C"].values():
        assert v["dz"] < 1e-9 and abs(v["L"] - v["Lx"]) < 1e-9

def test_unequal_edge_heights_add_depth_part():
    r = measure(points(400, 350, 800))
    assert all(v["dz"] > 0 and v["L"] > v["Lx"] for v in r["C"].values())
    assert r["rho_left_over_right"] > 1

def test_volume_formula_cases():
    r = measure(points(400, 400, 800))
    lo, hi = r["V_load_only"]["B two pallets in a row"][0.8]
    assert abs(lo - 2.4 * 0.8 * min(r["H_m"].values())) < 1e-9 and abs(hi - 2.4 * 0.8 * max(r["H_m"].values())) < 1e-9

def test_truck_ruler_main_and_low_end():
    """Main ruler = mast top -> floor below the mast; low end = old ruler (floor under the front wheel, longer in pixels)."""
    P = points(400, 400, 800, mast_px=902.0); P["ref_front_wheel_ground"] = (0, 100 + 920.0)
    assert truck_px(P) == (902.0, 920.0)
    del P["mast_floor"]                                    # frame without the new click: old ruler / mean floor correction
    main, low = truck_px(P)
    assert low == 920.0 and abs(main - 920.0 / floor_corr()) < 1e-9 and 1.0 < floor_corr() < 1.05

def test_mast_check_recovers_made_up_truck():
    """Made-up truck: mast 3213 mm, roof 2838 mm, tyres 822 mm, strong perspective (front tyre 0.10 px/mm, rear 0.08 px/mm)."""
    import mast_check as m
    kf, kr, xf, xr, fy = 0.1, 0.08, 900, 400, 1000
    k = lambda x: kf + (kr - kf) * (x - xf) / (xr - xf)
    P = {"ftyre_top": [xf, fy - m.TYRE * kf], "ftyre_bottom": [xf, fy], "rtyre_top": [xr, fy - m.TYRE * kr], "rtyre_bottom": [xr, fy],
         "mast_top": [1000, fy - 3213 * k(1000)], "mast_floor": [1000, fy], "roof_top": [650, fy - 2838 * k(650)], "roof_floor": [650, fy]}
    r = m.analyse(P)
    assert abs(r["ratio_mast_roof_corr"] - 3213 / 2838) < 1e-6 and abs(r["mast_mm_tyre_scale"] - 3213) < 0.5 and abs(r["roof_check"] - 1) < 1e-6
    assert m.best_mast(r["ratio_mast_roof_corr"]) == 3213


def test_end_view_geometry_recovers_made_up_box():
    """Made-up box corner: long face 2.4 m, end face 2.4 m (or 1.2 m), at right angles, seen by a pinhole camera with f = 1500 px.
    faces() must give back the two lengths and 90 degrees from the edge heights in pixels alone."""
    import end_view as ev
    f, H, cx = 1500.0, 1.40, ev.CX
    for end in (2.4, 1.2):
        a = np.radians(35); C = np.array([0.6, 6.0])                       # near corner (X, Z) in metres
        L = C + 2.4 * np.array([-np.cos(a), np.sin(a)]); R = C + end * np.array([np.sin(a), np.cos(a)])
        px = lambda P: dict(x=cx + f * P[0] / P[1], h=f * H / P[1])
        e = {}
        for tag, P in (("L", L), ("C", C), ("R", R)):
            e["x" + tag], e["h" + tag] = px(P)["x"], px(P)["h"]
        lg, en, ang = ev.faces(e, f, H=H)
        assert abs(lg - 2.4) < 1e-9 and abs(en - end) < 1e-9 and abs(ang - 90) < 1e-6
        assert abs(ev.f_right_angle(e) - f) <= 5


def test_scenario_E_is_two_pallets_deep():
    """E = D with twice the depth (2 x 1.2 m + gap): with nothing varied, E / D = (2.4 + gap) / 1.2."""
    import uncertainty as u
    d, e = u.simulate("D", set(), width=1.2), u.simulate("E", set(), width=1.2)
    ratio = np.median(e["V"]) / np.median(d["V"])
    assert abs(ratio - (2.4 + u.NOMINAL["gap_m"]) / 1.2) < 1e-6
