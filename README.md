# Forklift load volume from one video (work in progress)

**Problem.** In a public Linde video (https://www.youtube.com/watch?v=RCqa8Kojlw8, pass-by at about 21-22 s) a forklift drives past with a
load of stacked crates on pallets. Estimate the load volume in m³ from the video alone. This is a prototype; it is not finished (Step 5-6 still open).

> **Status: no final number yet.** Three cases are carried side by side (A, B, C). See "What the evidence says" below.

## Method in plain steps (so far)
1. Download the video (`yt-dlp`, not stored in the repo), pick the sharp frames of the pass (`src/extract_frames.py`).
2. Click corner points by hand on frames #1086, #1092, #1098 (`src/annotate.py`). #1092 was clicked twice to measure click error (mean 1.7 px, worst 9.8 px).
3. Get a scale (mm per pixel) from the truck datasheet: mast height 2888 mm over the pixels from mast top to the floor. This is the **main ruler**.
   The pallet height (144 mm on only about 30 px) is a **weak cross-check**: 1 px of error is about 3 %, the top edge is hard to see, and the measured spread from click error alone is
   about 15 % for the pallet scale against about 1 % for the truck scale.
4. Measure load height with the vertical scale (not affected by the turn of the truck). Measure the length of the long face with perspective (the nearer end looks taller;
   that tells how far the face is turned away). `src/measure.py`
5. Check the layer count and crate sizes (`src/crates.py`), then run a Monte Carlo with 10,000 runs (`src/uncertainty.py`).

## Cases
| Case | Meaning | Length x width |
|---|---|---|
| **B (main, by decision)** | two EUR pallets in a row | 2.4 m x 0.8 m |
| A | one EUR pallet | 1.2 m x 0.8 m |
| C | length as measured from the video | about 1.7 m x 0.8 m |

Width (depth into the picture) is **not visible** in this view. 0.8 m is an assumption; 1.2 m is shown as its own scenario.

## Results so far (load only, width 0.8 m, truck scale, pooled over 3 frames; see `outputs/uncertainty.json`)
| Case | Load only, m³ (median, 80 % range) | Load + pallets, m³ |
|---|---|---|
| B | 2.13 (1.94 - 2.32) | 2.41 (2.22 - 2.60) |
| A | 1.06 (0.97 - 1.15) | 1.19 (1.10 - 1.29) |
| C | 1.51 (1.27 - 1.77) | 1.70 (1.45 - 1.98) |

These ranges are **inside each case**. They do not include the question "which case is true". Different width (1.2 m): B 3.19, A 1.59, C 2.26 m³.
Using the weak pallet-height scale instead: B 2.56, A 1.27, C 2.24 m³.

## What the evidence says (honest summary)
* We count **4 crate layers**. With the datasheet crate height (290-300 mm) that is 1.16-1.20 m, which agrees with the truck-scale height (1.15-1.17 m).
* If the long face were 2.4 m (case B), the load would have to be **5.2-6.0 layers tall**; for 1.2 m (case A) only **2.6-3.0 layers**. Only a length of about 1.7-1.8 m (case C) matches 4 layers.
* Case B is still possible **if the crates in this video are taller than the datasheet crates** (about 350 mm) and the pallet-height scale is right. That is exactly what we could not verify.
* The crate **count** (8 crates along the lower rows) matches two pallets in a row only if the 300 mm side runs along the face. The 400 mm side along the face (3.2 m) fits the clicks worse.
* Perspective and the truck agree on a turn of about 22-25° and a focal length of about 1270-1390 px (frames #1086, #1092).

## Assumptions (every one of these is a guess or an unverified fact)
1. **Crate type is NOT verified for this video.** Sizes used come from other products: iplschoeller 3150001 (400 x 300 x 290 mm) and 3283001 (400 x 300 x 300 mm), both 20 x 0.5 L crates;
   Paderborner datasheets (crate 40 x 30 x 30 cm, 8 per layer, 5 layers, 161 cm with pallet, EUR pallet 1200 x 800). The crates in the video are green and may be a different type (for example taller 1 L crates).
2. The pallets are EUR pallets (1200 x 800 x 144 mm). No EPAL mark or block count could be confirmed in the video. A small tolerance of +-3 mm per pallet and a 0-30 mm gap between two pallets are assumed.
3. Load width (depth into the picture) is 0.8 m (alt. 1.2 m). Not visible.
4. Forklift model "Linde E80" comes from the video's own title card. Datasheet used: Linde E60/E80, series 1279 (rows 4.2 mast height lowered 2888 mm, 4.20 length to fork face 3503 mm,
   4.22 forks 1200 mm for the 600 mm load-centre version / 1800 mm for the 900 mm version, 4.24 carriage width 2180 mm). Which variant is in the video is **not known**. Fork spacing is not in the datasheet.
5. Truck scale error from different depths (mast vs. wheel): +-10 % (assumed). The pallet-height scale disagrees with it by 22-27 %, which is outside this band.
6. Camera: ideal pinhole, image centre as principal point, no lens distortion; focal length 800-1400 px (upper limit from the truck geometry; lower limit is a wide-angle guess).
7. The long face is a flat rectangle with equal vertical edges (the height ratio left/right of about 1.15-1.17 comes from perspective only).
8. Fill factor 0.90-1.00 (share of the bounding box that is filled). Click error: 2-5 px for sharp points, 10 px for blurry points.
9. Crate count: 4 layers (counted by two people), 8 crates along the lower rows (9 in the top row, partly hidden by the fork carriage).
10. Frame #1098: the "truck rear" click is a different feature than in the other frames; it is not used for volumes.

## Sources
* Linde E60/E80 datasheet (series 1279): https://www.linde-mh.com/media/Datasheets/EN_ds_e60_e80_1279_en_b_0224_view.pdf
* IPL Schoeller crate 3150001: https://www.iplschoeller.com/products/3150001-beverage-crate-20x50cl ; 3283001: https://www.iplschoeller.com/ch/produkte/3283001-beverage-crate-20x50cl
* Paderborner datasheets: https://paderborner-brauerei.de/wp-content/uploads/2025/08/2025_08_26_PB-Export_Datenblatt_20x05l_web.pdf and https://paderborner-brauerei.de/wp-content/uploads/2024/02/PB_Limo_Cola-Orange_DB_Fl_05lx20.pdf
* Video: https://www.youtube.com/watch?v=RCqa8Kojlw8 (frames at 21.72 s, 21.84 s, 21.96 s)

## Still open
Tests (Step 5), notebook and `results.json` (Step 6), "Where this would fail" list, pitch script, final self-review.
