"""Collect the final numbers into outputs/results.json (reads the outputs of mast_check.py, measure.py, new_frames.py, uncertainty.py and pallet_checks.py; run those first)."""
import json
u, m, nf, mc, pc, ev = (json.load(open(f"outputs/{n}.json")) for n in ("uncertainty", "measure_step3", "new_frames", "mast_check", "pallet_checks", "end_view"))
r3 = lambda d: {"median": round(d["median"], 2), "p10": round(d["p10"], 2), "p90": round(d["p90"], 2)}   # 80 % range = p10..p90
res = {
    "note": "E (6 EUR pallets: 3 along the forks x 2 side by side across, 2.4 x 2.4 m, measured height) is the main answer. The side frames hide the depth; the end view at 18.3-19.2 s shows two pallets side by side (6 crates across, double pallet block in the middle, end face about as long as the long side). D (1 pallet deep, 2.4 x 1.2 m) is kept as history. Volumes in m3, 80 % range (p10-p90) INSIDE each scenario; the crate type is still not verified.",
    "main_answer_E_load_only_m3": r3(u["main_case"]["E"]["load_only"]), "main_answer_E_load_plus_pallets_m3": r3(u["main_case"]["E"]["load_plus_pallets"]),
    "end_view": {"frames_s": [v["t_s"] for v in ev["frames"].values()], "counts": ev["counts"],
                 "ratio_end_over_long_all_focal": [round(ev["summary"]["ratio_all_min"], 2), round(ev["summary"]["ratio_all_max"], 2)],
                 "ratio_end_over_long_right_angle": [round(x, 2) for x in ev["summary"]["ratio_right_angle"]],
                 "focal_px_for_right_angle": ev["summary"]["f_right_angle_px"], "predicted_ratio": ev["summary"]["predicted_ratio"]},
    "history_D_load_only_m3": r3(u["main_case"]["D"]["load_only"]), "history_D_load_plus_pallets_m3": r3(u["main_case"]["D"]["load_plus_pallets"]),
    "mast_h1_mm": 3213, "mast_check_ratio_mast_over_roof_corrected": {k: round(v["ratio_mast_roof_corr"], 3) for k, v in mc["frames"].items()},
    "mast_check_tyre_scale_mast_mm": {k: round(v["mast_mm_tyre_scale"]) for k, v in mc["frames"].items()}, "mast_check_roof_mm_datasheet_2838": {k: round(v["roof_mm_tyre_scale"]) for k, v in mc["frames"].items()},
    "scenarios_load_only_m3": {{"A": "A one EUR pallet (excluded)", "B": "B two pallets, height from image", "B_crates": "B two pallets, height from crates", "C": "C length from clicks", "D": "D three pallets 2.4 x 1.2 m, measured height (history)", "E": "E six pallets 2.4 x 2.4 m, measured height (MAIN)"}[k]: r3(v["load_only"]) for k, v in u["main_case"].items()},
    "per_frame_height_m_truck_scale": {k: round(v["H_m"]["truck"], 3) for k, v in m.items()} | {k: round(v["H_left_m"], 3) for k, v in nf.items()},
    "per_frame_height_m_pallet_scale": {k: round(v["H_m"]["pallet144"], 3) for k, v in m.items()},
    "length_lower_bound_m_frame_1068": [round(nf["1068"]["Lx_lower_bound_low_m"], 2), round(nf["1068"]["Lx_lower_bound_m"], 2)],
    "pallet_checks": {"gap_pallet_vs_truck_eur144": {k: [round(x, 3) for x in v] for k, v in pc["a_gap_eur144"].items()},
                      "gap_if_drinks_pallet_166": {k: [round(x, 3) for x in v] for k, v in pc["b_gap_drinks166"].items()},
                      "pallet_ruler_click_spread": round(pc["pallet_ruler_click_spread"], 3),
                      "lengths_m": {k: [round(x, 2) for x in v] for k, v in pc["c_lengths_m"].items()},
                      "crate_shape_face_length_m": {"as_seen": [round(x, 2) for x in pc["d_crate_shape"]["face_length_m_as_seen"]], "turn_corrected": [round(x, 2) for x in pc["d_crate_shape"]["face_length_m_turn_corrected"]]}},
    "monte_carlo_runs": u["runs"], "ranges_assumed": u["ranges"],
    "main_scenario": "E (6 EUR pallets, 3 along x 2 across, 2.4 x 2.4 m, measured height); replaces D (1 pallet deep) after the end view",
}
json.dump(res, open("outputs/results.json", "w"), indent=1); print(json.dumps(res, indent=1))
