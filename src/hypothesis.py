"""PRELIMINARY test: is the load one EUR pallet (A) or two pallets in a row (B)?
All pixel numbers below were READ BY EYE (by Claude) from outputs/grid_1092.jpg, frame #1092.
They are NOT your clicked points. Each is good to roughly +-15 px. Replace them with clicks later.
Truck sizes come from the Linde E60/E80 datasheet (see README sources)."""
# --- datasheet rulers (mm) ---
L2 = 3503            # rear of truck -> fork face (row 4.20)
H1 = 3213            # lowered mast height of the mast in the video (src/mast_check.py); 2888 was the wrong mast
FORK = (1200, 1800)  # fork length for the 600 mm / 900 mm load-centre versions (row 4.22)
# --- eyeballed pixels, frame #1092 ---
rear_x, carriage_x = 310, 1330          # truck rear end, fork carriage face
mast_top_y, wheel_ground_y = 215, 997   # top of mast, ground under the front wheel
load_x0, load_x1 = 1360, 1795           # long face of the load, left/right end
load_h_px = 308                         # average height of the load face (left 328, right 288)

s_along = L2 / (carriage_x - rear_x)           # mm per px along the truck, averaged rear..carriage
s_up    = H1 / (wheel_ground_y - mast_top_y)   # mm per px, vertical, at the mast / front wheel
print(f"scale along truck (avg, rear is nearer the camera): {s_along:.2f} mm/px")
print(f"scale vertical at mast (closer to the load):        {s_up:.2f} mm/px")
lo, hi = s_along, s_up + 0.1            # load is a bit farther away than the truck average
print(f"-> use {lo:.2f} .. {hi:.2f} mm/px for the load face\n")

L_px = load_x1 - load_x0
print(f"Load face length: {L_px} px = {L_px*lo:.0f} .. {L_px*hi:.0f} mm")
print(f"Load height     : {load_h_px} px = {load_h_px*lo:.0f} .. {load_h_px*hi:.0f} mm  (4 layers -> {load_h_px*lo/4:.0f}..{load_h_px*hi/4:.0f} mm per layer)")
for name, mm in (("A one EUR pallet (1200)", 1200), ("B two pallets in a row (2400)", 2400)):
    print(f"  {name}: would need {mm/hi:.0f} .. {mm/lo:.0f} px  (we see {L_px})")
print()
for f in FORK:
    mid = (lo + hi) / 2
    print(f"If forks are {f} mm: fork tip expected at x = {carriage_x + f/hi:.0f} .. {carriage_x + f/lo:.0f}   (load ends at x = {load_x1})")
print()
H = (load_h_px * lo / 1000, load_h_px * hi / 1000); W = 0.8      # width across the forks: ASSUMED 800 mm, not visible
for name, D in (("A", 1.2), ("B", 2.4), ("measured depth (not a hypothesis)", (L_px*lo/1000 + L_px*hi/1000)/2)):
    print(f"Case {name}: depth {D:.2f} m x width {W} m (assumed) x height {H[0]:.2f}..{H[1]:.2f} m  -> load-only volume {D*W*H[0]:.2f} .. {D*W*H[1]:.2f} m3")
