"""Contact sheet of one time window: python window.py video out.jpg start_s end_s step_s"""
import cv2, sys
video, out = sys.argv[1], sys.argv[2]; a, b, st = map(float, sys.argv[3:6])
cap = cv2.VideoCapture(video); fps = cap.get(cv2.CAP_PROP_FPS); tiles = []; t = a
while t < b:
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps)); ok, f = cap.read()
    if not ok: break
    f = cv2.resize(f, (480, 270)); cv2.putText(f, f"{t:.1f}s", (5, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2); tiles.append(f); t += st
cols = 4
while len(tiles) % cols: tiles.append(tiles[0] * 0)
cv2.imwrite(out, cv2.vconcat([cv2.hconcat(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]))
