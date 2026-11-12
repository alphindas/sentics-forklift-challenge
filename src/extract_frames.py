"""Score sharpness (variance of Laplacian) for every frame in a time window,
keep the N sharpest (at least `gap` frames apart) and save them + a contact sheet.
usage: python extract_frames.py video.mp4 tag start_s end_s [N]"""
import cv2, sys, os
video, tag = sys.argv[1], sys.argv[2]; a, b = float(sys.argv[3]), float(sys.argv[4]); N = int(sys.argv[5]) if len(sys.argv) > 5 else 10
cap = cv2.VideoCapture(video); fps = cap.get(cv2.CAP_PROP_FPS)
i0, i1 = int(a * fps), int(b * fps); scored = []
cap.set(cv2.CAP_PROP_POS_FRAMES, i0)
for i in range(i0, i1):
    ok, f = cap.read()
    if not ok: break
    g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
    scored.append((cv2.Laplacian(g, cv2.CV_64F).var(), i))
keep, gap = [], 5   # frames at 50 fps -> >= 0.1 s apart
for s, i in sorted(scored, reverse=True):
    if all(abs(i - j) >= gap for _, j in keep): keep.append((s, i))
    if len(keep) == N: break
keep.sort(key=lambda x: x[1]); tiles = []
for s, i in keep:
    cap.set(cv2.CAP_PROP_POS_FRAMES, i); ok, f = cap.read()
    cv2.imwrite(f"frames/{tag}_{i:05d}.jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 95])
    t = cv2.resize(f, (640, 360)); cv2.putText(t, f"#{i} t={i/fps:.2f}s sharp={s:.0f}", (5, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2); tiles.append(t)
    print(tag, i, f"{i/fps:.2f}s", round(s))
while len(tiles) % 2: tiles.append(tiles[0] * 0)
cv2.imwrite(f"outputs/contact_{tag}.jpg", cv2.vconcat([cv2.hconcat(tiles[k:k+2]) for k in range(0, len(tiles), 2)]))
