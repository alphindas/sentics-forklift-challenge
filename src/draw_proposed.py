"""Draw PROPOSED (unverified) points on a frame so a human can check them.
usage: python draw_proposed.py proposed.json frame.jpg out.jpg"""
import json, sys, cv2
pj, frame, out = sys.argv[1:4]
pts = json.load(open(pj))[frame.split("/")[-1]]
img = cv2.imread(frame)
for name, (x, y) in pts.items():
    col = (0, 255, 255) if name.startswith("pallet") else (255, 0, 255)
    cv2.circle(img, (x, y), 7, col, 2); cv2.putText(img, name, (x + 9, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 2)
for grp, col in (("pallet", (0, 255, 255)), ("load", (255, 0, 255))):
    q = [pts[f"{grp}_{c}"] for c in ("BL", "BR", "TR", "TL")]
    cv2.polylines(img, [__import__("numpy").array(q)], True, col, 1)
cv2.putText(img, "PROPOSED - NOT VERIFIED", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 0, 255), 3)
x0, y0, x1, y1 = 1000, 450, 1920, 1030
cv2.imwrite(out, img[y0:y1, x0:x1])
