"""Unit tests for the small formulas (scale, height, volume, perspective)."""
import sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from measure import measure, d, TRUCK_H1, PAL_H

def points(h_left, h_right, length_px, mast_px=902.0):
    """Flat clicked rectangle-ish face with given pixel sizes (no real camera)."""
    P = {"pallet_BL": (0, 1000), "pallet_BR": (length_px, 1000), "pallet_TL": (0, 1000 - 30), "pallet_TR": (length_px, 1000 - 30),
         "load_BL": (0, 1000), "load_BR": (length_px, 1000), "load_TL": (0, 1000 - h_left), "load_TR": (length_px, 1000 - h_right),
         "ref_mast_top": (0, 100), "ref_front_wheel_ground": (0, 100 + mast_px), "ref_carriage_face": (500, 900), "ref_truck_rear": (-500, 900)}
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
