# Forklift load volume from one video (work in progress)

**Problem.** In a public Linde video (https://www.youtube.com/watch?v=RCqa8Kojlw8, pass-by at about 20-22 s) a forklift drives past with a
load of stacked crates on pallets. Estimate the load volume in m³ from the video alone. This is a prototype; it is not finished (tests, notebook, final review still open).

> **Status: no single final number.** Two scenarios (B and C) are carried side by side, neither is "main". The reason is one unverified fact:
> **the crate type in this video is NOT verified** (see Assumptions 1). Case A (one EUR pallet) is excluded by the clicks.

## Method in plain steps
1. Download the video (`yt-dlp`, not stored in the repo) and pick sharp frames of the pass (`src/extract_frames.py`).
2. Click corner points by hand on frames #1086, #1092, #1098 (`src/annotate.py`). #1092 was clicked twice to measure click error (mean 1.7 px, worst 9.8 px).
3. Scale (mm per pixel) from the truck datasheet: mast height 2888 mm over the pixels from mast top to the floor under the front wheel. This is the **height ruler**.
   The pallet height (144 mm on only about 30 px) is a **weak cross-check**: 1 px of error is about 3 %, the top edge is hard to see, and click error alone spreads the pallet-height
   scale by about 15 % against about 1 % for the truck scale. The two scales disagree by 22-27 % (pallet scale larger), which is the main open problem.
4. Load height = pixels x vertical scale. Length of the long face = pixels x scale **plus perspective**: the nearer end looks taller, the height ratio (1.15-1.17) tells how far the face is turned away
   (about 22-25°). The truck gives a focal length of at most about 1270-1390 px (its clicked length against the datasheet length). `src/measure.py`
5. Crate checks: count layers and crates, compare with real crate sizes (`src/crates.py`).
6. Monte Carlo, 10,000 runs, inputs: click error, scale bias, fill factor, pallet tolerance, focal length (`src/uncertainty.py`).

## The two scenarios (load only, width 0.8 m, 80 % range from the Monte Carlo, `outputs/uncertainty.json`)
| | **C: length from clicks + truck geometry** | **B: length from the crate count** |
|---|---|---|
| Long face | about 1.7 m (from pixels, truck scale, perspective) | 2.4 m (8 crates x 0.300 m = two EUR pallets in a row) |
| Height | 1.16 m (truck scale; = 4 layers x 290 mm) | 4 layers x 0.29-0.36 m = 1.16-1.44 m (crate height not measured) |
| Load only | **1.51 m³ (1.27 - 1.77)** | **2.37 m³ (2.15 - 2.59)** |
| Load + pallets | 1.70 m³ (1.45 - 1.98) | 2.65 m³ (2.43 - 2.87) |
| If width is 1.2 m | 2.26 m³ | 3.55 m³ |
| What supports it | truck datasheet distances, perspective, 290 mm crates exist (20 x 0.5 L, one 12 x 0.75 L) | 8 crates counted along the lower rows, 4 along 1200 mm = EUR pallet layout |
| What argues against it | 8-9 crates in 1.7 m means a crate side of only about 0.2 m | needs crates 390-420 mm per layer if the image scale is right; no catalogue crate is above 360 mm |

* **Case A, one EUR pallet (1.2 m): excluded.** The pallet long edge is about 14 times its height in the image (13.8-14.6 in all frames). A real 1200 x 144 mm face is 8.3, and turning the face away can only make that ratio smaller.
  It would also need a load only 2.6-3.0 layers tall. (If it were true: 1.06 m³, 0.97-1.15.)
* The old "B with truck-scale height" number (2.13 m³) is **not** shown as a scenario: it combines a 2.4 m length with a 290 mm crate height, which would be 5.2-6.0 layers. It is kept in `outputs/uncertainty.json` only for comparison.
* A possible middle case also exists: 8 crates of 266 mm = 2.13 m, which needs crates of about 345-385 mm (borderline against the tallest 12-bottle crates, 333-360 mm). Not carried as a scenario.
* **The two scenarios differ because the two scales differ.** In both, volume is roughly (face area) x width. The face area is about 2.0 m² with the truck scale and about 3.0 m² with the pallet scale.
* These ranges are **inside each scenario**. They do not include "which scenario is true" or the width (0.8 m vs 1.2 m, shown separately).

## Where the crate type came from (and did not)
* Stickers on the crates were cropped at full resolution and upscaled 6 times (`outputs/stickers_sheet.png`): they show paper labels with text lines and two barcodes. **Nothing is readable** (no brand, pack size or article number).
* The video's title card says "LINDE E80 IN DER GETRÄNKEINDUSTRIE, Carolinenbrunnen, Bielefeld"; a caption names Mineralquellen Wüllner GmbH & Co. KG. So the plant is known, the crate is not.
* No Carolinen datasheet with crate size was found. REWE product pages could not be read by script.
* Real crates that exist (manufacturer catalogue Delbrouck, read directly): 20 x 0.5 L 400x300x290-302; 12 x 0.75 L 400x266x310-333 and 400x300x291-360; 12 x 1 L 400x300x310-330 and 400x266x314; 12 x 0.7 L 375x266x305.
* A returnable GDB 0.75 L crate of another brand: 9 crates per layer, 4 layers, EUR pallet (Wasserhelden "Artikelpass"). Layers match our 4; the crate size is not given there.
* Blue crate pallet in the background (about 93 s, light blue, corner view, partly hidden by the truck): 5 layers, at least 6-7 columns on its long face. **Not conclusive** for a crate size.

## Assumptions (every one of these is a guess or an unverified fact)
1. **Crate type is NOT verified for this video.** Heights of 0.29-0.36 m are the range of real 20 x 0.5 L and 12-bottle crates (sources below), not a match for the video's crate.
2. The pallets are EUR pallets (1200 x 800 x 144 mm). No EPAL mark or block count could be confirmed. +-3 mm per pallet and a 0-30 mm gap between two pallets are assumed.
3. Load width (depth into the picture) is 0.8 m (alt. 1.2 m). Not visible in this view.
4. Forklift model "Linde E80" comes from the video's own title card. Datasheet: Linde E60/E80, series 1279 (4.2 mast height lowered 2888 mm; 4.20 length to fork face 3503 mm; 4.22 forks 1200 mm for the
   600 mm load-centre version, 1800 mm for the 900 mm version; 4.24 carriage width 2180 mm). Which variant is in the video is **not known**. Fork spacing is not in the datasheet.
5. Truck scale error from different depths (mast vs. wheel): +-10 % (assumed). The pallet-height scale disagrees by 22-27 %, outside this band, so that gap is carried as the two scenarios.
6. Camera: ideal pinhole, image centre as principal point, no lens distortion; focal length 800-1400 px (upper limit from the truck geometry, lower limit a wide-angle guess).
7. The long face is a flat rectangle with equal vertical edges (the height ratio left/right comes from perspective only).
8. Fill factor 0.90-1.00 (share of the bounding box that is filled). Click error: 2-5 px for sharp points, 10 px for blurry points.
9. Crate count: 4 layers (counted by two people, re-checked on a close crop), 8 crates along the lower rows (9 in the top row, left end hidden by the fork carriage).
10. Frame #1098: the "truck rear" click is a different feature than in the other frames; it is not used for volumes.
11. Frames #1086-#1098 are only 0.1-0.24 s apart; their errors are correlated. Earlier frames (#995-#1015, about 19.9-20.4 s) show the face closer to side-on and look better; they are not clicked yet.

## Sources
* Linde E60/E80 datasheet (series 1279): https://www.linde-mh.com/media/Datasheets/EN_ds_e60_e80_1279_en_b_0224_view.pdf
* IPL Schoeller crates 3150001 (400x300x290) and 3283001 (400x300x300): https://www.iplschoeller.com/products/3150001-beverage-crate-20x50cl , https://www.iplschoeller.com/ch/produkte/3283001-beverage-crate-20x50cl
* Delbrouck crate catalogue: https://www.delbrouck.de/en/getraenkekaesten/
* Paderborner datasheets (20 x 0.5 L crate 40x30x30 cm, 8 per layer, 5 layers, 161 cm with pallet): https://paderborner-brauerei.de/wp-content/uploads/2025/08/2025_08_26_PB-Export_Datenblatt_20x05l_web.pdf , https://paderborner-brauerei.de/wp-content/uploads/2024/02/PB_Limo_Cola-Orange_DB_Fl_05lx20.pdf
* Wasserhelden Artikelpass (0.75 L GDB crate, 9 per layer, 4 layers): https://produktinfo.blauer-engel.de/uploads/pdf_uploads/Artikelpass%20Wasserhelden_ohne%20Preise.pdf
* Video: https://www.youtube.com/watch?v=RCqa8Kojlw8 (frames at 21.72 s, 21.84 s, 21.96 s)

## Still open
Tests (Step 5), notebook and `results.json` (Step 6), "Where this would fail" list, pitch script, final self-review.
