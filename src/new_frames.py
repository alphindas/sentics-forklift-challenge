"""Frames #1062 and #1068 (your clicks). The right end of the load is cut off by the frame edge, so only the LEFT-end height (truck scale) and a
lower bound of the length can be measured. Compare with the 3 main frames."""
import json, numpy as np
from measure import d, TRUCK_H1, load_points
def left_height(P):
    s = TRUCK_H1 / abs(P["ref_front_wheel_ground"][1] - P["ref_mast_top"][1])          # mm per px, vertical, truck
    return d(P["load_BL"], P["load_TL"]) * s / 1000, s
out = {}
for k in ("1062", "1068"):
    P = list(json.load(open(f"outputs/points_{k}.json")).values())[0]
    H, s = left_height(P); out[k] = {"scale_mm_per_px": s, "H_left_m": H, "per_layer_mm": H / 4 * 1000}
    if P["load_TR"]:                                                                    # top edge is at least this long (right end at the frame edge)
        out[k]["top_edge_px"] = d(P["load_TL"], P["load_TR"]); out[k]["Lx_lower_bound_m"] = out[k]["top_edge_px"] * s / 1000
    print(k, {a: round(v, 3) for a, v in out[k].items()})
old = [left_height(P)[0] for P in load_points().values()]
print("main frames (1086, 1092, 1098) left-end height m:", [round(x, 3) for x in old])
allH = old + [v["H_left_m"] for v in out.values()]
print(f"all 5 frames: {min(allH):.2f}-{max(allH):.2f} m, mean {np.mean(allH):.2f} m (spread {100*(max(allH)-min(allH))/np.mean(allH):.1f} %)")
json.dump(out, open("outputs/new_frames.json", "w"), indent=1)
