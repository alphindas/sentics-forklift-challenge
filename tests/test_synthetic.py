"""Fake-box test: project a box of KNOWN size through a pinhole camera, 'click' its corners (optionally with noise), run measure() and check the answer.
Run: python -m pytest tests -q   (from the repo root)"""
import sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from measure import measure, TRUCK_H1, TRUCK_L2, PAL_H

F, CX, CY = 1100.0, 960.0, 540.0          # the "camera": focal length and image centre (px)
CAM_H = 1.2                               # camera 1.2 m above the floor
TRUE_L, TRUE_H = 2.4, 1.25                # the box we hide from the code: length and height of the load (m)

def project(X, Z, h):
    """Point at sideways X (m), depth Z (m), height h above the floor (m) -> pixel."""
    return (CX + F * X / Z, CY + F * (CAM_H - h) / Z)

def make_points(turn_deg, z_left=6.0, length=TRUE_L, height=TRUE_H, noise_px=0.0, seed=0):
    rng = np.random.default_rng(seed)
    t = np.radians(turn_deg)                                   # >0: right end farther away
    xl, xr, zl, zr = -1.0, -1.0 + length * np.cos(t), z_left, z_left + length * np.sin(t)
    pal, top = PAL_H / 1000, PAL_H / 1000 + height
    P = {"pallet_BL": project(xl, zl, 0), "pallet_BR": project(xr, zr, 0), "pallet_TL": project(xl, zl, pal), "pallet_TR": project(xr, zr, pal),
         "load_BL": project(xl, zl, pal), "load_BR": project(xr, zr, pal), "load_TL": project(xl, zl, top), "load_TR": project(xr, zr, top),
         "ref_mast_top": project(xl - 0.3, zl, TRUCK_H1 / 1000), "ref_front_wheel_ground": project(xl - 0.3, zl, 0),
         "ref_carriage_face": project(xl, zl, 0.5), "ref_truck_rear": project(xl - TRUCK_L2 / 1000, zl, 0.5)}
    return {k: tuple(np.array(v) + rng.normal(0, noise_px, 2)) for k, v in P.items()}

def test_height_exact_without_noise():
    r = measure(make_points(turn_deg=15))
    assert abs(r["H_m"]["truck"] - TRUE_H) < 0.02

def test_length_range_contains_truth_without_noise():
    for turn in (-25, -10, 10, 25):                                         # either end nearer
        lo, hi = measure(make_points(turn_deg=turn))["L_C_m"]
        assert lo * 0.95 <= TRUE_L <= hi * 1.05, (turn, lo, hi)

def test_volume_within_range_with_click_noise():
    vols = []
    for seed in range(200):
        r = measure(make_points(turn_deg=15, noise_px=3.0, seed=seed))
        H = r["H_m"]["truck"]; lo, hi = r["L_C_m"]
        vols.append(0.8 * H * (lo + hi) / 2)
    truth = TRUE_L * TRUE_H * 0.8
    lo, hi = np.percentile(vols, [10, 90])
    assert abs(np.median(vols) - truth) / truth < 0.10                     # median within 10 % of the known volume
    assert lo < truth * 1.10 and hi > truth * 0.90

def test_lower_truth_is_not_confused_with_longer_box():
    """A 1.2 m box must not measure like a 2.4 m box (case A vs B must be separable)."""
    short = measure(make_points(turn_deg=15, length=1.2))["L_C_m"]
    assert short[1] < 1.2 * 1.15 and short[1] < 2.0
