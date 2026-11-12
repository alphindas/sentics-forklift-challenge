"""Early frame #999 (19.98 s) and the two-frame test. THE POINTS OF #999 BELOW WERE READ BY EYE BY CLAUDE FROM A GRID (+-10 px).
They are PROPOSED, NOT VERIFIED, and have to be replaced by your clicks. #1092 uses your clicked points."""
import numpy as np
from measure import measure, load_points, d, PAL_H, TRUCK_H1, TRUCK_L2
P999 = {"load_BL": (1097, 900), "load_BR": (1903, 878), "load_TR": (1880, 384), "load_TL": (1055, 508),
        "pallet_BL": (1108, 946), "pallet_TL": (1097, 903), "pallet_BR": (1905, 925), "pallet_TR": (1903, 880),
        "ref_mast_top": (915, 118), "ref_front_wheel_ground": (870, 957), "ref_carriage_face": (1062, 905), "ref_truck_rear": (395, 700)}
r99, r92 = measure(P999), measure(load_points()["1092"])
print("PROPOSED #999 vs CLICKED #1092 (volumes columns not used here)")
for nm, r in (("#999 (proposed)", r99), ("#1092 (clicked)", r92)):
    px = r["px"]; hl, hr = px["load_h_left"], px["load_h_right"]
    print(f"{nm}: load face {px['load_len']:.0f} px long, edge heights left {hl:.0f} / right {hr:.0f} px (ratio {hl/hr:.2f}; <1 means the RIGHT end is nearer)")
    print(f"   scales mm/px: truck-vertical {r['scale']['truck_vertical']:.2f}, pallet-height {r['scale']['pallet_height']:.2f}")
    print(f"   load height m: truck {r['H_m']['truck']:.2f}, pallet {r['H_m']['pallet144']:.2f}  -> per layer (4): {r['H_m']['truck']/4*1000:.0f} / {r['H_m']['pallet144']/4*1000:.0f} mm")
    for k, v in r["C"].items(): print(f"   face length with perspective [{k}]: {v['L']:.2f} m (sideways {v['Lx']:.2f}, depth part {v['dz']:.2f}, turn {v['turn_deg']:.0f} deg)")
print("\nSame load, two different views -> the true length must be the same. Face length range per scale (f = 800..1400 px):")
for sc in ("truck", "pallet144"):
    a = [r["C"][f"{sc}/f{f}"]["L"] for r in (r99, r92) for f in (800, 1400)]
    print(f"   {sc:9s}: #999 {min(a[0],a[1]):.2f}-{max(a[0],a[1]):.2f} m | #1092 {min(a[2],a[3]):.2f}-{max(a[2],a[3]):.2f} m")
print("\nFORK-TIP GEOMETRY for 3 pallets with the 800 mm side along the forks (2.4 m deep). Datasheet forks: 1200 mm (600 load centre) and 1800 mm (900 load centre). No longer fork is listed for the E80.")
for fk in (1200, 1800):
    on = fk / 800; print(f"   forks {fk} mm: pallet 1 on forks 100 %, pallet 2 {min(max(on-1,0),1)*100:.0f} %, pallet 3 {min(max(on-2,0),1)*100:.0f} %; load overhangs the fork tips by {2400-fk} mm; load centre at {1200} mm from the carriage face (rated load centres: 600 / 900 mm)")
