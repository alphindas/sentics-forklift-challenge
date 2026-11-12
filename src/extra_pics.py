"""Save the sharpest full-resolution frame (variance of Laplacian) within +-0.1 s of each requested time into extra_pics/.
usage: python src/extra_pics.py video.mp4 label:time_s [label:time_s ...]"""
import cv2, sys
cap = cv2.VideoCapture(sys.argv[1]); fps = cap.get(cv2.CAP_PROP_FPS)
for arg in sys.argv[2:]:
    lab, t = arg.split(":"); i0 = int(float(t) * fps); best = None
    for i in range(i0 - 5, i0 + 6):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i); ok, f = cap.read()
        if not ok: continue
        s = cv2.Laplacian(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
        if best is None or s > best[0]: best = (s, i, f)
    cv2.imwrite(f"extra_pics/{lab}_{best[1]:05d}.jpg", best[2], [cv2.IMWRITE_JPEG_QUALITY, 95]); print(lab, "frame", best[1], f"t={best[1]/fps:.2f}s sharp={best[0]:.0f}")
