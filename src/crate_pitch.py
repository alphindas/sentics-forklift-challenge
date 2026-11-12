"""Measure the crate pitch from the big dark hand-hold windows of the green crates.
Each crate shows one big dark window; neighbouring crates in a row are one crate width apart, in a column one layer apart.
usage: python src/crate_pitch.py frame.jpg x0 y0 x1 y1   (box = face region)"""
import cv2, sys, numpy as np
fr = sys.argv[1]; x0, y0, x1, y1 = map(int, sys.argv[2:6])
f = cv2.imread(fr); roi = f[y0:y1, x0:x1]; hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
dark = ((hsv[..., 2] < 70)).astype(np.uint8); dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, lab, st, cen = cv2.connectedComponentsWithStats(dark)
areas = np.array([st[k][4] for k in range(1, n)]); big = np.percentile(areas, 90)
blobs = [(cen[k][0] + x0, cen[k][1] + y0, st[k][4], st[k][2], st[k][3]) for k in range(1, n) if st[k][4] > 0.5 * big and st[k][2] < 140 and st[k][3] < 120]
# group into layers by y (fit a line y = a x + b to the whole face first, then cluster the residuals)
b = np.array(blobs); A = np.polyfit(b[:, 0], b[:, 1], 1)
vis = f.copy()
for x, y, a_, w, h in blobs: cv2.circle(vis, (int(x), int(y)), 6, (0, 0, 255), -1)
cv2.imwrite(fr.replace(".jpg", "_blobs.jpg").replace("extra_pics/", "outputs/"), vis[y0:y1, x0:x1])
print(f"{len(blobs)} big dark windows; area limit {0.5*big:.0f}")
for x, y, a_, w, h in sorted(blobs): print(f"  x={x:7.1f} y={y:6.1f} w={w:3d} h={h:3d} area={a_}")
