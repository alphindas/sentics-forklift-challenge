"""Draw a labelled pixel grid on (a crop of) a frame, so coordinates can be read by eye.
usage: python grid.py frame.jpg out.jpg x0 y0 x1 y1 [step]"""
import cv2, sys
fr, out = sys.argv[1:3]; x0, y0, x1, y1 = map(int, sys.argv[3:7]); st = int(sys.argv[7]) if len(sys.argv) > 7 else 100
img = cv2.imread(fr)
for x in range(x0 - x0 % st + st, x1, st):
    cv2.line(img, (x, y0), (x, y1), (255, 255, 255), 1); cv2.putText(img, str(x), (x + 2, y0 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
for y in range(y0 - y0 % st + st, y1, st):
    cv2.line(img, (x0, y), (x1, y), (255, 255, 255), 1); cv2.putText(img, str(y), (x0 + 2, y - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
cv2.imwrite(out, img[y0:y1, x0:x1])
