# Forklift load volume from one video

**Problem.** In a public Linde video (https://www.youtube.com/watch?v=RCqa8Kojlw8, pass-by at about 20-22 s) a forklift drives past with a
load of stacked crates on pallets. Estimate the load volume in m³ from the video alone. This is a prototype.

**Run it:** `pip install -r requirements.txt`, then open `notebook.ipynb` and run all cells (or `python src/mast_check.py`, `python src/measure.py`, `python src/new_frames.py`, `python src/uncertainty.py`, `python src/pallet_checks.py`, `python src/make_results.py`; tests: `python -m pytest tests -q`). Final numbers: `outputs/results.json`.

## Result (short)
* **Most likely scenario D (3 EUR pallets in a row, 2.4 x 1.2 m, 4 layers, measured height 1.40 m): about 3.9 m³ of load (80 % range 3.5-4.2 m³ inside D).** Load plus pallets about 4.3 m³ (4.0-4.7).
* **If 3 EUR pallets: 3.5-4.2 m³.** If the load is longer than 2.4 m (some checks point to 2.5-3.2 m, see "Pallet checks"), the volume is higher. If there are fewer pallets, it is lower, but B and C don't fit the crate counts well, so I don't have a clean lower number I trust. A (1.28) is excluded.
* **The height ruler was fixed:** the truck has the 3213 mm mast, not the 2888 mm one (checked against the cabin roof and the tyres, see "Which mast?"). With it, the truck ruler and the pallet ruler agree within 2-8 % (before: 22-27 % apart).
* **What decides it:** the number and type of pallets (3 EUR pallets = 2.4 m; 3 drinks-industry pallets would be 3.0-3.3 m), the hidden depth (1.2 m assumed), and the fork length (D needs a third pallet beyond 1200/1800 mm forks). None of these is verified from the video alone. The crate type is unknown.
* The ranges inside a scenario are about ±9 %; the choice of scenario is the bigger uncertainty (see "Two kinds of uncertainty").

> **Status: D is the most likely scenario, but it is not proven.** B and C are kept in the tables for comparison. The reason D is not proven is two unverified facts:
> **the crate type and the pallet layout (number and type of pallets) in this video are NOT verified** (see Assumptions 1 and 2). Case A (one EUR pallet) is excluded.

## Method in plain steps
1. Download the video (`yt-dlp`, not stored in the repo) and pick sharp frames of the pass (`src/extract_frames.py`).
2. Click corner points by hand on frames #1086, #1092, #1098 (`src/annotate.py`). #1092 was clicked twice to measure click error (mean 1.7 px, worst 9.8 px).
3. Scale (mm per pixel) from the truck datasheet: mast height **3213 mm** (the mast in the video, see "Which mast?") over the pixels from the mast top to the floor directly below the mast. This is the **height ruler**.
   The old floor point (under the front wheel) is 1.3-2.0 % longer in pixels; it is kept as the low end of the range (`src/measure.py`, `truck_scale()`).
   The pallet height (144 mm on only about 30 px) is a **second, weaker ruler**: 1 px of error is about 3 %, the top edge is hard to see, and click error alone spreads it by about 29 % (80 % half-range in the
   Monte Carlo click model) against about 1 % for the truck ruler. An earlier version of this README said "about 15 %"; that number could not be reproduced from the code. With the 3213 mm mast the two rulers agree within 2-8 %.
4. Load height = pixels x vertical scale. Length of the long face = pixels x scale **plus perspective**: the nearer end looks taller, the height ratio (1.15-1.17) tells how far the face is turned away
   (about 22-25°). The truck gives a focal length of at most about 1270-1390 px (its clicked length against the datasheet length). `src/measure.py`
5. Crate checks: count layers and crates, compare with real crate sizes (`src/crates.py`).
6. Monte Carlo, 10,000 runs, inputs: click error, scale bias (incl. which floor point), fill factor, pallet tolerance, focal length (`src/uncertainty.py`).
7. Mast check (`src/mast_check.py`) and pallet checks (`src/pallet_checks.py`), see the sections below.

## Which mast? Checked from the video
The datasheet's headline 2888 mm is one of the two **shortest** masts. The mast table lists lowered heights 2863/2888/3013/3213/3363/3563/3963 mm; the cabin roof (overhead guard) is 2838 mm and the tyres are 315/70-15 (about 822 mm).
I clicked the mast top (the steel channel, not the lamp), the cabin roof, both tyres and the floor below each point in #1086, #1092 and #1098 (`src/annotate_mast.py`, `outputs/points_mast.json`).
The two tyres have the same real size, so their pixel sizes give the perspective along the truck; `src/mast_check.py` corrects the heights with it.

| Frame | Mast/roof, raw | Mast/roof, perspective-corrected (80 % for ±3 px clicks) | Mast from tyre scale | Roof from tyre scale (datasheet 2838) |
|---|---|---|---|---|
| #1086 | 1.053 | 1.128 (1.106-1.150) | 3164 mm | 2806 mm (-1.1 %) |
| #1092 | 1.058 | 1.130 (1.109-1.151) | 3191 mm | 2825 mm (-0.5 %) |
| #1098 | 1.043 | 1.130 (1.108-1.154) | 3177 mm | 2811 mm (-0.9 %) |

The datasheet ratio for the 3213 mm mast is 1.132. The neighbours are clearly outside the range: 3013 mm (1.062) and 3363 mm (1.185); 2888 mm (1.018) is far off. The tyre scale gives the same answer on its own
(80 % ranges 3073-3284 mm), and it puts the roof within about 1 % of the datasheet. **So the truck has the 3213 mm mast, and the 2888 mm used before was the wrong one:** it made every image height and length about 10-12 % too small.

## How Michael's hint (EUR pallet) is used
* **Length:** 3 pallets with the 800 mm side along the face = 3 x 0.8 m = **2.4 m** (scenario D).
* **Depth:** the 1200 mm side across the forks = **1.2 m** (not visible in the video, assumed).
* **Height:** the 144 mm pallet height is a **second height ruler**, independent of the truck. With the 3213 mm mast it agrees with the truck ruler within 2-8 %.
* **Why one pallet is excluded:** the load shows 9 crate columns, 3 labels about 3 columns apart, and about 9 pallet feet with two double feet where pallets meet (`outputs/A_00999_counts.jpg`).
  The pallet face is about 14 times as long as it is tall in the image; one EUR pallet (1200 x 144 mm) would be 8.3.

## Scenarios (width and crate type are not certain; D is the most likely)
Load-only volume, 80 % range from the Monte Carlo (`outputs/uncertainty.json`). Frames #1086/#1092/#1098 (clicked), pooled. Heights use the **left-end** height with the truck ruler
(3213 mm mast): 1.41 m in all three frames (1.38-1.39 m with the old floor point), i.e. 4 layers of about 345-353 mm.

| | A: 1 EUR pallet | B: 2 pallets in a row (8 crates x 300 mm) | C: length from clicks | D: 3 pallets, 800 mm side along the forks |
|---|---|---|---|---|
| Length x width | 1.2 x 0.8 m | 2.4 x 0.8 m | about 2.1 x 0.8 m (1.89-2.25) | 2.4 x 1.2 m |
| Height | 1.40 m (image) | 4 x 0.29-0.36 m (catalogue) | 1.40 m (image) | **1.40 m (image, measured)** |
| Load only | 1.28 (1.16-1.39) | 2.37 (2.15-2.59) | 2.20 (1.84-2.59) | **3.87 (3.53-4.23)** |
| Load + pallets | 1.41 | 2.65 | 2.44 | 4.29 (3.95-4.65) |
| Width 1.2 m instead of 0.8 m | 1.91 | 3.55 | 3.30 | (already 1.2 m) |

D's height used to be a catalogue crate height (4 x 310-333 mm). It is now the measured height, with the same fill factor and Monte Carlo as A and C. The old second estimate "108 crates x catalogue crate volume"
is removed: the measured 345-353 mm per layer does not match that crate, so the crate type is unknown again. With the pallet ruler instead of the truck ruler, D would be 4.13 m³ (80 %: 3.28-5.70; the pallet ruler is the weak one).

### New clicks: frames #1062 and #1068 (`src/new_frames.py`, `outputs/new_frames.json`)
The right end of the load is cut off by the frame edge in both, so only the left-end height and a length lower bound can be measured. Frame #999 was skipped for the same reason.
* **Height (truck ruler, left end):** #1062 1.46 m, #1068 1.45 m (per layer 366 / 362 mm), against 1.41 m in #1086/#1092/#1098. These two frames have no "floor below the mast" click, so they use the old floor point
  corrected by the mean difference (1.7 %); with the old floor point alone they give 1.44 / 1.43 m. All 5 frames: 1.41-1.46 m, mean 1.43 m (spread 4 %). The Monte Carlo uses only the three main frames.
* **Length:** in #1068 the top edge is at least 597 px long (clicked right end at x = 1903, at the frame edge), which is at least **2.18-2.21 m** at the left-end scale (±15 % for the unknown depth of the right end).
  This is a lower bound only: C (2.07 m) is just below it, and it does not separate B from D (both 2.4 m). D's length (3 x 0.8 m) comes from the counts and is unchanged.
* The near-frontal frame did not give a ratio (right-end clicks missing), so the turn angle is still from #1086-#1098.

### Two kinds of uncertainty (do not mix them)
**(a) Inside one scenario.** The Monte Carlo ranges above (for D: 3.53-4.23 m³, about ±9 %) only cover click error, scale bias (±10 % plus the choice of floor point), fill factor, pallet tolerance, gap and focal length.
They assume that the scenario itself is right. They are the *smaller* uncertainty. For D the biggest single input is the assumed ±10 % scale bias (8 %), then the fill factor (4 %).

**(b) Which scenario is right.** This is the *large* one and the Monte Carlo does not cover it: the load-only medians run from 2.20 (C) over 2.37 (B) to 3.87 m³ (D), a factor of about 1.8 between the ends,
and A (1.28) is excluded. It depends on facts that are not verified: how many pallets are on the forks and which type (EUR or drinks-industry), and the load depth (0.8 or 1.2 m). Today the evidence favours D, but D still has open problems
(the fork tips, and some checks say the load is longer than 2.4 m; see the consistency table and "Pallet checks"). "They carry several pallets together" is **likely** (blue-load seam, 5-tine carriage at 52 s, see Assumption 14) but **unverified**; Carolinen could not be asked.
So D's range must not be quoted as the whole uncertainty. The honest statement today is: "If 3 EUR pallets: 3.5-4.2 m³. If the load is longer than 2.4 m, it is more. If there are fewer pallets, it could be lower, but B and C don't fit the crate counts well, so I don't have a clean lower number I trust."

### Consistency table (what each scenario has to explain)
Facts read from the frames: **9 crate columns on every row** (frame #999, where the left end and the top row's right end are visible; annotated in `outputs/A_00999_counts.jpg`), **4 layers**, **3 white labels, one per 3 columns** (spacing 3.1, 3.3, 3.0 columns in #999; 3.2 in #1008; 3.0 in #1092),
**about 9 pallet feet** in 3 groups of 3 (8 clearly seen in #999 plus one at the frame edge; two pairs of feet side by side where two pallets would meet).

| Test | A | B | C | D |
|---|---|---|---|---|
| 9 columns, 3 labels, 9 feet | no | no (expects 8 columns, 2 labels, 6 feet) | not tested | **yes** |
| Length vs measured (clicked frames #1086-#1098: 1.92-2.31 m, both rulers; #1068: at least 2.18-2.21 m; #999, points estimated by eye: 2.45-2.56 m pallet ruler, 2.94-3.08 m truck ruler) | no (1.2 m) | 2.4 m: 4-20 % longer than the clicked frames, fits #999 pallet ruler, 20-25 % shorter than #999 truck ruler | 2.07 m: fits the clicked frames, just below the #1068 lower bound, 15-30 % short for #999 | same as B |
| Height measured 1.38-1.46 m (4 layers = 345-366 mm per layer) | measured | 4 x 290-360 mm = 1.16-1.44 m: only the top of the range fits | measured | measured (no crate assumption any more) |
| Crate shape: cell width/height 0.81-0.91 (apparent, from window pitch) x measured layer height = crate width 279-322 mm as seen, 301-355 mm corrected for the 22-25 deg turn | - | 300 mm crate fits the width, but B needs 8 columns | - | 9 columns on 3 x 800 mm need a 266 mm crate: **does not fit**; 9 x 301-355 mm = 2.7-3.2 m |
| Fork tips (datasheet 1200 or 1800 mm) | fits | 2.4 m deep: overhangs 1.2 / 0.6 m | 2.1 m: overhangs 1800 mm forks by about 0.3 m | same as B: pallet 3 hangs 1.2 m (1200 mm forks) or 0.6 m (1800 mm forks) beyond the tips |
| A real crate of this size exists (catalogue), but it is not confirmed to be the crate in this video. | - | 300 mm side: 20 x 0.5 L (290-302 mm tall: below the measured layer height) | no crate with a 230 mm side (9 x 0.23 = 2.07 m) | 400 x 266 (12 x 0.75 L) is 310-333 mm tall: below the measured 345-353 mm. **Crate type unknown** |

**What survives.** A is excluded (counts and length). B as defined does not survive the counts (it needs 8 columns, not 9). C fits the clicked frames' length but is just below the #1068 lower bound and conflicts with the counts and with #999.
D fits the counts, and its height is now measured. Length: the clicked frames give 1.92-2.31 m (4-20 % short of 2.4 m), #999 (points estimated by eye) gives 2.45-3.08 m, and the crate-shape check gives 2.5-3.2 m, so 2.4 m sits in the middle but is not confirmed;
**the load could be somewhat longer than 2.4 m.** No catalogue crate matches 9 columns of 266 mm and a 345-353 mm layer, so the crate type is unknown. D has to explain why the third pallet hangs over the fork tips.
The datasheet lists no fork longer than 1800 mm for the E80 but mentions "hook-on and integrated attachments" without sizes, so a longer reach is possible but unverified. Any length that fits the #1068 lower bound (at least 2.18 m) overhangs 1800 mm forks, so the fork problem is not special to D. D is the most likely scenario, but it is not proven.

* **Same load, two views.** In #999 the right end is nearer (edge height ratio 0.80); in #1092 the left end is nearer (1.17). The truck swings during the pass. With the pallet-height ruler the two frames give 2.45-2.56 m and 2.05-2.20 m
  (about 15 % apart); with the truck ruler 2.94-3.08 m and 1.99-2.17 m (about 40 % apart). The two views do not agree, so the length is the least certain measurement. #999 values come from points **estimated by eye, not clicked**.

### Pallet checks (`src/pallet_checks.py`, `outputs/pallet_checks.json`)
* **(a) Truck ruler vs pallet ruler (EUR, 144 mm):** pallet ruler larger by +6 / +2 / +6 % in #1086 / #1092 / #1098 (+8 / +3 / +8 % with the old floor point). That is well inside the pallet ruler's own click spread (about 29 %). Before the mast fix the gap was 22-27 %.
* **(b) If the pallets were 166 mm drinks-industry pallets:** the gap would be +17 to +25 %. That is still inside the pallet ruler's click spread, so it does not exclude drinks pallets, but the 144 mm EUR pallet fits 3-4 times better.
* **(c) Length of the long face, all estimates with the 3213 mm mast:** clicked frames #1086 / #1092 / #1098: truck ruler 2.04-2.19 / 1.99-2.17 / 1.92-2.14 m, pallet ruler 2.20-2.31 / 2.05-2.20 / 2.08-2.27 m; #1068 at least 2.18-2.21 m;
  #999 (points estimated by eye): pallet ruler 2.45-2.56 m, truck ruler 2.94-3.08 m.
* **(d) Crate shape:** cell width/height 0.81-0.91 x layer height 345-353 mm = crate width 279-322 mm as seen (301-355 mm corrected for the 22-25 deg turn); x 9 columns = 2.51-2.89 m (2.71-3.19 m corrected).
* **Compared with 2.4 m (3 EUR pallets) and 3.0-3.3 m (3 drinks pallets, 1000 x 1200 or 1100 x 1070 mm):** the clicked frames are below 2.4 m, #999's pallet ruler is close to 2.4 m, and #999's truck ruler and the crate shape point to 2.5-3.2 m, which overlaps the drinks-pallet length.
  **Warning: the load could be somewhat longer than 2.4 m.** With the same depth, a 3.0-3.3 m load would have 25-38 % more volume than D. D's 2.4 m is kept because it comes from the counts and the EUR pallet hint, and the clicked frames do not support a longer load.
* Case A is excluded: the pallet long edge is about 14 times its height in the image (a 1200 x 144 mm face would be 8.3).

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
   The German drinks industry also uses its own pallets (1100 x 1070 or 1000 x 1200 mm, 166 mm tall). The pallet checks: the 144 mm height fits the truck ruler within 2-8 %, a 166 mm pallet would be 17-25 % off (still inside the pallet ruler's click spread);
   the crate shape and #999 point to a 2.5-3.2 m load, which would fit 3 drinks pallets (3.0-3.3 m) better than 3 EUR pallets (2.4 m); the clicked frames point to less than 2.4 m. So the pallet type is not settled.
3. Load width 0.8 m for A, B, C; 1.2 m for D (follows from 3 pallets turned with the 800 mm side along the forks). Not visible in the video.
4. Forklift model "Linde E80" comes from the video's own title card. Datasheet: Linde E60/E80, series 1279 (4.2 mast height lowered: 2888 mm in the main table, one of the two shortest masts; mast table 2863-3963 mm; **the video's truck has the 3213 mm mast**, see "Which mast?"; h6 cabin roof 2838 mm; tyres 315/70-15; 4.20 length to fork face 3503 mm; 4.22 forks 1200 mm for the
   600 mm load-centre version, 1800 mm for the 900 mm version; 4.24 carriage width 2180 mm). Which fork length is in the video is **not known**. Fork spacing is not in the datasheet.
5. Truck ruler error from different depths (mast vs. load): +-10 % (assumed), plus the choice of floor point (below the mast, or under the front wheel: 1.3-2.0 %). With the 3213 mm mast the pallet ruler agrees within 2-8 %, inside this band.
6. Camera: ideal pinhole, image centre as principal point, no lens distortion; focal length 800-1400 px (upper limit from the truck geometry, lower limit a wide-angle guess).
7. The long face is a flat rectangle with equal vertical edges (the height ratio left/right comes from perspective only).
8. Fill factor 0.90-1.00 (share of the bounding box that is filled). Click error: 2-5 px for sharp points, 10 px for blurry points.
9. Crate count: 4 layers (counted by two people, re-checked on a close crop). 9 columns, counted in #999: the top row shows both ends (right end at the frame edge for the lower rows and pallet). In #1086-#1098 only 8 are visible because the left column is behind the fork carriage. Annotated counts: `outputs/A_00999_counts.jpg` (`src/annotate_counts.py`).
10. Frame #1098: the "truck rear" click is a different feature than in the other frames; it is not used for volumes.
11. Frames #1086-#1098 are only 0.1-0.24 s apart; their errors are correlated. Frame #999 (19.98 s) shows nearly the whole face (lower right at the frame edge) from the other side of the turn; its corner points were **estimated by eye, not clicked**, and are not verified (`src/early_frames.py`).
12. Extra frames used (not stored in the repo, see timestamps): green-crate close-up 16.0-17.5 s; blue-crate loads 115.4 s, 117.1 s, 138.5-139.6 s, 140-142 s; early pass 19.7-20.3 s. In the close-up the bottle labels read "Carolinen naturelle".
13. Blue-crate loads (Carolinen crates, 5 layers) show a seam in the middle of the pallet and 3 crates per pallet along a face, with 6 crates across in the front view. This suggests the plant carries several pallets together, but it does not fix the crate size.
14. **Empty forks found (video 51-52 s, frames 02575-02625 in `extra_pics/`):** a Linde truck of the same family with a very wide carriage and **5 fork tines** (so a multi-pallet fork is in use at this plant).
   It is an oblique view and probably a different truck, so it does not prove the pass-by truck has the same forks. Fork length cannot be read from this shot: the tines point partly towards the camera, and with the unknown turn
   angle the image gives only the relation length = 1.4 m / tan(angle between the forks and the camera direction), from about 290 px of sideways tine extent against about 445 px of carriage width (2180 mm datasheet). No second view with a visible fork tip at the far end of the pass-by load was found.
15. **Crate type is unknown.** D used to take its height from a catalogue crate (Delbrouck, 12 x 0.75 L, 400 x 266 x 310-333 mm). With the 3213 mm mast the measured layer height is 345-353 mm, which does not match that crate, so D now uses the measured height and the crate is unknown.
16. **Mast:** 3213 mm, checked from the video (mast/roof ratio and tyres, `src/mast_check.py`). The truck ruler uses the floor directly below the mast; the old floor point under the front wheel is the low end of the range.

## Sources
* Linde E60/E80 datasheet (series 1279): https://www.linde-mh.com/media/Datasheets/EN_ds_e60_e80_1279_en_b_0224_view.pdf
* IPL Schoeller crates 3150001 (400x300x290) and 3283001 (400x300x300): https://www.iplschoeller.com/products/3150001-beverage-crate-20x50cl , https://www.iplschoeller.com/ch/produkte/3283001-beverage-crate-20x50cl
* Delbrouck crate catalogue: https://www.delbrouck.de/en/getraenkekaesten/
* Paderborner datasheets (20 x 0.5 L crate 40x30x30 cm, 8 per layer, 5 layers, 161 cm with pallet): https://paderborner-brauerei.de/wp-content/uploads/2025/08/2025_08_26_PB-Export_Datenblatt_20x05l_web.pdf , https://paderborner-brauerei.de/wp-content/uploads/2024/02/PB_Limo_Cola-Orange_DB_Fl_05lx20.pdf
* Wasserhelden Artikelpass (0.75 L GDB crate, 9 per layer, 4 layers): https://produktinfo.blauer-engel.de/uploads/pdf_uploads/Artikelpass%20Wasserhelden_ohne%20Preise.pdf
* Video: https://www.youtube.com/watch?v=RCqa8Kojlw8 (frames at 21.72 s, 21.84 s, 21.96 s; frame #999 at 19.98 s)

## Where this method would fail
* **Load is not a box** (gaps, overhang, shrink-wrap, a half-empty top layer): the box volume is then too high; the fill factor 0.90-1.00 is a guess.
* **Hidden or non-EUR pallet**, or a different pallet height than 144 mm: the pallet ruler breaks (it is already the weak ruler, about 30 px). A 166 mm drinks pallet would shift it by 15 %, and 3 drinks pallets would make the load 3.0-3.3 m long instead of 2.4 m.
* **Wrong datasheet variant:** the 2888 mm mast (one of the two shortest) made every height and length about 10-12 % too small. It was caught by checking the mast against the cabin roof and the tyres.
* **Depth (load width) is a guess** (0.8 or 1.2 m, not visible from the side). This alone changes the volume by 50 %.
* **Wrong number of pallets / crate type** (the main open point here): the volume scales with length.
* **Steep or unknown camera angle, lens distortion:** one-camera perspective is simplified (pinhole, no distortion); a wide-angle lens bends the edges. Focal length is only bounded (800-1400 px).
* **Truck ruler at different depths** (mast vs. load): up to about 10 % assumed; the two views (#999 vs #1092) still disagree by about 40 % on the length.
* **Motion blur and cut-off frames:** click error 2-10 px; the right end of the load was out of frame in several frames.
* **Next steps:** a second camera or a depth sensor (gives width and true length directly), a frame with the pallets and fork tips visible, a known reference object in the load plane, a crate datasheet from the plant.

## Still open
Frames #999 and #1014 were not clicked (the right end is cut off), so the #999 points in `src/early_frames.py` stay **estimated by eye, not clicked**, and unverified. Crate type, number and type of pallets, the hidden depth and the fork length of the pass-by truck are not verified (the plant could not be asked). #1062/#1068 have no "floor below the mast" click; they use a mean correction.
