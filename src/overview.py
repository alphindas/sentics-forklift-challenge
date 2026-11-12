"""Make a coarse contact sheet (1 frame / 3 s) of the whole video to find the pass-by."""
import cv2, sys
video = sys.argv[1]; out = sys.argv[2]; step_s = float(sys.argv[3]) if len(sys.argv) > 3 else 3
cap = cv2.VideoCapture(video); fps = cap.get(cv2.CAP_PROP_FPS); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
tiles = []
for t in range(0, int(n / fps), int(step_s)):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps)); ok, f = cap.read()
    if not ok: break
    f = cv2.resize(f, (384, 216)); cv2.putText(f, f"{t}s", (5, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2); tiles.append(f)
cols = 6
while len(tiles) % cols: tiles.append(tiles[0] * 0)
rows = [cv2.hconcat(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
cv2.imwrite(out, cv2.vconcat(rows))
