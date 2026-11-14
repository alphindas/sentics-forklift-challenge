"""Collect the final numbers into outputs/results.json (reads the outputs of measure.py, uncertainty.py and new_frames.py; run those first)."""
import json
u, m, nf = (json.load(open(f"outputs/{n}.json")) for n in ("uncertainty", "measure_step3", "new_frames"))
r3 = lambda d: {"median": round(d["median"], 2), "p10": round(d["p10"], 2), "p90": round(d["p90"], 2)}   # 80 % range = p10..p90
res = {
    "note": "D (3 pallets) is most likely, not proven: the number of pallets is NOT verified. Volumes in m3, load only, 80 % range (p10-p90) INSIDE each scenario.",
    "scenarios_load_only_m3": {{"A": "A one EUR pallet (excluded)", "B": "B two pallets, height from image", "B_crates": "B two pallets, height from crates", "C": "C length from clicks", "D": "D three pallets 2.4 x 1.2 m"}[k]: r3(v["load_only"]) for k, v in u["main_case"].items()},
    "per_frame_height_m_truck_scale": {k: round(v["H_m"]["truck"], 3) for k, v in m.items()} | {k: round(v["H_left_m"], 3) for k, v in nf.items()},
    "per_frame_height_m_pallet_scale": {k: round(v["H_m"]["pallet144"], 3) for k, v in m.items()},
    "length_lower_bound_m_frame_1068": round(nf["1068"]["Lx_lower_bound_m"], 2),
    "monte_carlo_runs": u["runs"], "ranges_assumed": u["ranges"],
    "overall_range_m3_across_scenarios": [1.8, 3.7], "most_likely_scenario": "D (3 pallets, 2.4 x 1.2 m), most likely, not proven",
}
json.dump(res, open("outputs/results.json", "w"), indent=1); print(json.dumps(res, indent=1))
