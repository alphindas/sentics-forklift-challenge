"""Click tool: mark corner points on a frame, save to JSON.

usage: python src/annotate.py frames/A_01092.jpg [--out outputs/points_run1.json] [--proposed outputs/proposed_points.json]

Order of clicks (the title bar always tells you the next one):
  pallet_BL pallet_BR pallet_TR pallet_TL   (front face of the pallet, B=bottom T=top)
  load_BL   load_BR   load_TR   load_TL     (front face of the load)
  face2_1 .. face2_4                        (second face, optional: press K to skip)
Keys:  u = undo last point   k = skip face 2   s = save   q = save and quit
Mouse: left click = place point,  scroll wheel = zoom at cursor,  right-drag = pan
Hollow circles = PROPOSED points (not verified) shown only as a hint. They are never saved.
Running it twice on the same frame (--out run1 / run2) lets uncertainty.py measure click error.
"""
import argparse, json, os
import matplotlib; matplotlib.use("QtAgg")   # needs PyQt5 (no tkinter on this machine)
import matplotlib.pyplot as plt, matplotlib.image as mpimg

NAMES = [f"{g}_{c}" for g in ("pallet", "load") for c in ("BL", "BR", "TR", "TL")] + [f"face2_{i}" for i in range(1, 5)]

ap = argparse.ArgumentParser(); ap.add_argument("frame"); ap.add_argument("--out", default="outputs/points.json"); ap.add_argument("--proposed")
a = ap.parse_args(); key = os.path.basename(a.frame)

data = json.load(open(a.out)) if os.path.exists(a.out) else {}
pts = dict(data.get(key, {}))                      # name -> [x, y]
proposed = json.load(open(a.proposed)).get(key, {}) if a.proposed else {}

skip_face2 = [False]
fig, ax = plt.subplots(figsize=(14, 8)); ax.imshow(mpimg.imread(a.frame)); artists = []; pan = {}

def next_name():
    return next((n for n in NAMES if n not in pts and not (skip_face2[0] and n.startswith("face2"))), None)

def title():
    nxt = next_name()
    ax.set_title(f"{key}   next: {nxt or 'done - press q'}   (u undo, k skip face2, s save, q quit)"); fig.canvas.draw_idle()

def redraw():
    for t in artists: t.remove()
    artists.clear()
    for n, (x, y) in proposed.items():                                   # hints
        artists.append(ax.plot(x, y, "o", mfc="none", mec="orange", ms=10)[0])
    for n, (x, y) in pts.items():                                        # my clicks
        artists.append(ax.plot(x, y, "+", color="red", ms=14, mew=1.5)[0]); artists.append(ax.text(x + 6, y - 6, n, color="red", fontsize=8))
    title()

def save():
    data[key] = pts; json.dump(data, open(a.out, "w"), indent=1); print("saved", a.out, len(pts), "points")

def on_click(e):
    if e.inaxes != ax or e.button != 1 or fig.canvas.toolbar.mode: return   # ignore clicks while a toolbar tool is active
    nxt = next_name()
    if nxt: pts[nxt] = [round(e.xdata, 1), round(e.ydata, 1)]; redraw()

def on_key(e):
    if e.key == "u" and pts: pts.pop(list(pts)[-1]); redraw()
    elif e.key == "k": skip_face2[0] = True; title()
    elif e.key == "s": save()
    elif e.key == "q": save(); plt.close(fig)

def on_scroll(e):
    if e.inaxes != ax: return
    f = 0.7 if e.button == "up" else 1 / 0.7; x, y = e.xdata, e.ydata
    (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
    ax.set_xlim(x - (x - x0) * f, x + (x1 - x) * f); ax.set_ylim(y - (y - y0) * f, y + (y1 - y) * f); fig.canvas.draw_idle()

def on_press(e):
    if e.button == 3 and e.inaxes == ax: pan.update(x=e.xdata, y=e.ydata)
def on_release(e): pan.clear()
def on_move(e):
    if pan and e.inaxes == ax:
        dx, dy = pan["x"] - e.xdata, pan["y"] - e.ydata
        ax.set_xlim([v + dx for v in ax.get_xlim()]); ax.set_ylim([v + dy for v in ax.get_ylim()]); fig.canvas.draw_idle()

for ev, fn in (("button_press_event", on_click), ("button_press_event", on_press), ("button_release_event", on_release),
               ("motion_notify_event", on_move), ("key_press_event", on_key), ("scroll_event", on_scroll)):
    fig.canvas.mpl_connect(ev, fn)
redraw(); plt.show()
