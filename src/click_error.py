"""Click error between two independent click runs on the same frame (run1 vs run2).
usage: python src/click_error.py outputs/points_run1.json outputs/points_run2.json A_01092.jpg"""
import json, sys, numpy as np
p1, p2 = (json.load(open(f))[sys.argv[3]] for f in sys.argv[1:3])
rows = [(n, np.hypot(*(np.array(p1[n]) - np.array(p2[n])))) for n in p1 if p1[n] is not None and p2.get(n) is not None]
for n, e in rows: print(f"{n:24s} {e:5.1f} px")
e = np.array([r[1] for r in rows])
print(f"\nmean {e.mean():.1f} px | median {np.median(e):.1f} | worst {e.max():.1f} ({rows[int(e.argmax())][0]}) | n={len(e)}")
