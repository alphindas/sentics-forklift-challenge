"""Click tool for the mast check: which mast does the truck have? Saves to outputs/points_mast.json.

usage: python src/annotate_mast.py frames/A_01092.jpg      (then A_01086.jpg, A_01098.jpg)
       python src/mast_check.py                             (computes the ratios from the saved clicks)

Order of clicks (the title bar always tells you the next one):
  mast_top        top of the mast CHANNEL (the steel profile), NOT the lamp on top of it
  mast_floor      floor directly below the mast top
  roof_top        top of the cabin roof (overhead guard), at one clear point
  roof_floor      floor directly below that roof point
  ftyre_top       front tyre, top of the rubber
  ftyre_bottom    front tyre, where it touches the floor
  rtyre_top       rear tyre, top of the rubber
  rtyre_bottom    rear tyre, where it touches the floor
Keys:  u = undo last point   n = next point is NOT VISIBLE (saved as null)   s = save   q = save and quit
Mouse: left click = place point,  scroll wheel = zoom at cursor,  right-drag = pan
Resume: if the frame is already in the file, its points are loaded and you continue with the next missing one.
Separate from annotate.py on purpose: annotate.py and its JSON files are not touched.
"""
import argparse, json, os, time
import matplotlib; matplotlib.use("QtAgg")   # needs PyQt5 (no tkinter on this machine)
import matplotlib.pyplot as plt, matplotlib.image as mpimg
for k in [k for k in plt.rcParams if k.startswith("keymap.")]: plt.rcParams[k] = []

NAMES = ["mast_top", "mast_floor", "roof_top", "roof_floor", "ftyre_top", "ftyre_bottom", "rtyre_top", "rtyre_bottom"]
HINT = {"mast_top": "top of mast CHANNEL, not the lamp", "mast_floor": "floor below mast top", "roof_top": "cabin roof top",
        "roof_floor": "floor below roof point", "ftyre_top": "front tyre top", "ftyre_bottom": "front tyre on floor",
        "rtyre_top": "rear tyre top", "rtyre_bottom": "rear tyre on floor"}

ap = argparse.ArgumentParser(); ap.add_argument("frame"); ap.add_argument("--out", default="outputs/points_mast.json")
a = ap.parse_args(); key = os.path.basename(a.frame)
data = json.load(open(a.out)) if os.path.exists(a.out) else {}
pts = dict(data.get(key, {}))
status = [""]
fig, ax = plt.subplots(figsize=(14, 8)); ax.imshow(mpimg.imread(a.frame)); artists = []; pan = {}

def next_name(): return next((n for n in NAMES if n not in pts), None)

def title():
    nxt = next_name()
    ax.set_title(f"{key}   next: {nxt + ' (' + HINT[nxt] + ')' if nxt else 'done - press q'}   [{status[0]}]\n"
                 "(click=place  u=undo  n=not visible  s=save  q=save+quit)"); fig.canvas.draw_idle()

def redraw():
    for t in artists: t.remove()
    artists.clear()
    for n, p in pts.items():
        if p is None: continue
        x, y = p
        artists.append(ax.plot(x, y, "+", color="red", ms=14, mew=1.5)[0]); artists.append(ax.text(x + 6, y - 6, n, color="red", fontsize=8))
    title()

def save():
    data[key] = pts
    json.dump(data, open(a.out + ".tmp", "w"), indent=1); os.replace(a.out + ".tmp", a.out)
    n_vis = sum(p is not None for p in pts.values()); status[0] = f"saved {time.strftime('%H:%M:%S')}: {n_vis} points, {len(pts) - n_vis} not visible"
    print(f"saved {a.out} ({status[0]})"); title()

def on_click(e):
    tb = fig.canvas.toolbar
    if e.inaxes != ax or e.button != 1 or (tb is not None and tb.mode != ""): return
    nxt = next_name()
    if nxt: pts[nxt] = [round(e.xdata, 1), round(e.ydata, 1)]; status[0] = ""; redraw()

def on_key(e):
    nxt = next_name()
    if e.key == "u" and pts: pts.pop(list(pts)[-1]); status[0] = "undone"; redraw()
    elif e.key == "n" and nxt: pts[nxt] = None; status[0] = f"{nxt} marked not visible"; redraw()
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
