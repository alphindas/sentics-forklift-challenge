"""Crate checks (Step 4). The crate type in THIS video is NOT verified. Sizes come from other products:
  iplschoeller 3150001: 400 x 300 x 290 mm | 3283001: 400 x 300 x 300 mm  (20 x 0.5 L crates, product pages)
  Paderborner datasheets: crate 40 x 30 x 30 cm, 8 crates per layer, 5 layers, EUR pallet, 161 cm incl. pallet.
Ground truth from my own look at the frame (confirmed by you): 4 layers high, 8 crates along the lower rows (9 on top)."""
import numpy as np
from measure import load_points, d, PAL_H

CRATE_L, CRATE_W, CRATE_H = 0.400, 0.300, (0.290, 0.300)
LAYERS, N_ALONG = 4, (8, 9)
PITCH = (1610 - PAL_H) / 5 / 1000        # layer pitch from the Paderborner datasheet: (161 cm - 14.4 cm) / 5 layers
CASES = {"A one EUR pallet": 1.2, "B two pallets in a row": 2.4}
PER_LAYER = {"A one EUR pallet": 8, "B two pallets in a row": 16}     # 8 per layer on one EUR pallet (Paderborner datasheet)
print(f"layer pitch from the datasheet: {PITCH*1000:.0f} mm  (5 x 300 mm + 144 mm would be 1644 mm, but the datasheet says 1610 -> crates nest a little)")
print(f"height of {LAYERS} layers: {LAYERS*CRATE_H[0]:.2f} .. {LAYERS*CRATE_H[1]:.2f} m  (or {LAYERS*PITCH:.2f} m with the nested pitch)\n")

print("== crate count x crate volume (independent of the image scale, but it ASSUMES the case and the crate type)")
for c, n in PER_LAYER.items():
    v = [n * LAYERS * CRATE_L * CRATE_W * h for h in CRATE_H]
    print(f"  {c}: {n*LAYERS} crates x {CRATE_L*CRATE_W*CRATE_H[0]*1000:.1f}-{CRATE_L*CRATE_W*CRATE_H[1]*1000:.1f} L = {v[0]:.2f} .. {v[1]:.2f} m3 load only")

print("\n== orientation test: which crate side runs along the long face?")
for side, name in ((CRATE_W, "300 mm side along the face (400 mm deep)"), (CRATE_L, "400 mm side along the face (300 mm deep)")):
    print(f"  {name}: {N_ALONG[0]} crates -> {N_ALONG[0]*side:.1f} m,  {N_ALONG[1]} crates -> {N_ALONG[1]*side:.1f} m")

print("\n== per frame: what would each case imply for the load height? (we count 4 layers = %.2f..%.2f m)" % (LAYERS*CRATE_H[0], LAYERS*CRATE_H[1]))
print("   Idea: if the long face really is L metres, the metres-per-pixel is fixed by L (with the perspective turn included),")
print("   and that scale then fixes the height. A case is only believable if its height is about 4 layers.")
for k, P in load_points().items():
    hl, hr = d(P["load_BL"], P["load_TL"]), d(P["load_BR"], P["load_TR"]); hm = (hl + hr) / 2; rho = hl / hr
    ll = (d(P["load_BL"], P["load_BR"]) + d(P["load_TL"], P["load_TR"])) / 2
    cell = (ll / N_ALONG[0]) / (hm / LAYERS)
    print(f"  #{k}: cell width/height in pixels = {cell:.2f}  (a crate face with 300 mm side and 290-300 mm height would be ~1.0, with 400 mm ~1.35, before foreshortening)")
    for c, L in CASES.items():
        out = []
        for f in (800, 1400):
            s_req = 1000 * L / np.hypot(ll * (1 + hl / hr) / 2, f * abs(hl / hr - 1))           # mm per px at the left end needed for the face to be L long
            out.append(hl * s_req / 1000)
        print(f"      {c}: needs {min(out):.2f}..{max(out):.2f} m tall = {min(out)/CRATE_H[1]:.1f}..{max(out)/CRATE_H[0]:.1f} crate layers")
    for side, nm in ((CRATE_W, "300"), (CRATE_L, "400")):
        L = N_ALONG[0] * side; s_req = 1000 * L / np.hypot(ll * (1 + hl / hr) / 2, 1100 * abs(hl / hr - 1))
        print(f"      {nm} mm side x {N_ALONG[0]} crates ({L:.1f} m): needs {hl*s_req/1000:.2f} m tall = {hl*s_req/1000/0.295:.1f} layers (f=1100)")

# =====================================================================================================
print("\n\n== REDO with the crate sizes found in a manufacturer catalogue (Delbrouck, https://www.delbrouck.de/en/getraenkekaesten/, read 2026-11-12).")
print("   The crate TYPE IN THE VIDEO IS STILL NOT VERIFIED (stickers unreadable). These are real crates of the right family, not a match.")
# (side that would run along the face in m, name, verified heights in m of crates with that footprint)
FOOT = [(0.266, "400 x 266 (12 x 0.75 l / 12 x 1 l; 9 per EUR layer)", (0.310, 0.333)),
        (0.300, "400 x 300 (20 x 0.5 l, 12 x 0.75 l, 12 x 1 l)",       (0.290, 0.360)),
        (0.375, "375 x 266 (12 x 0.7 l)",                              (0.305, 0.305)),
        (0.400, "400 side along the face (any 400 x 266/300 crate)",    (0.290, 0.360))]
print("   Idea: n crates of side s give a face length L = n*s. That length fixes the scale (with perspective), the scale fixes the height,")
print("   height / 4 layers = implied crate height. A candidate fits if the implied height lies inside the verified heights of that footprint (+-5 %).\n")
for k, P in load_points().items():
    hl, hr = d(P["load_BL"], P["load_TL"]), d(P["load_BR"], P["load_TR"]); hm = (hl + hr) / 2; rho = hl / hr
    ll = (d(P["load_BL"], P["load_BR"]) + d(P["load_TL"], P["load_TR"])) / 2
    ratio = lambda f: hl / np.hypot(ll * (1 + hl / hr) / 2, f * abs(hl / hr - 1))            # height of the left edge per metre of face length (see measure.py)
    print(f"  #{k}:")
    for s, name, (h0, h1) in FOOT:
        row = []
        for n in N_ALONG:
            L = n * s; himp = [L * ratio(f) / LAYERS for f in (800, 1400)]; lo, hi = min(himp), max(himp)
            ok = hi >= h0 * 0.95 and lo <= h1 * 1.05
            row.append(f"{n} crates = {L:.2f} m -> crate {lo*1000:.0f}-{hi*1000:.0f} mm {'FITS' if ok else 'no'}")
        print(f"     {name}: " + " | ".join(row))
    print(f"     for comparison, crate height from the truck scale = {hl*2888/abs(P['ref_front_wheel_ground'][1]-P['ref_mast_top'][1])/LAYERS:.0f} mm, from the pallet-height scale = {hl*PAL_H/d(P['pallet_BL'],P['pallet_TL'])/LAYERS:.0f} mm")
