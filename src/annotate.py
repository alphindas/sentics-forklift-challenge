"""Click tool: mark corner points on a frame, save to JSON.

usage: python src/annotate.py frames/A_01092.jpg [--out outputs/points_run1.json] [--proposed outputs/proposed_points.json]

Order of clicks (the title bar always tells you the next one):
  pallet_BL pallet_BR pallet_TR pallet_TL   (front face of the pallet, B=bottom T=top)
  load_BL   load_BR   load_TR   load_TL     (front face of the load)
  face2_1 .. face2_4                        (second face, optional: press K to skip)
  ref_truck_rear        rearmost point of the truck body (datasheet: rear -> fork face = 3503 mm)
  ref_carriage_face     front face of the fork carriage, at the ground end of the vertical plate
  ref_mast_top          top of the mast (datasheet: ground -> mast top = 2888 mm)
  ref_front_wheel_ground  where the front (drive) wheel touches the floor, below the mast
  load_end_right_ground right end of the pallet at floor level;  feet_leftmost / feet_rightmost: outer edges of the first/last pallet foot you can see
Keys:  u = undo last point   n = next point is NOT VISIBLE (saved as null)   k = face 2 not visible (only works when the next point is a face2 point)
       s = save now to --out   q = save and quit      (matplotlib's own shortcuts are switched off)
Resume: if --out already has this frame, its points are loaded and you continue with the next missing one.
Mouse: left click = place point,  scroll wheel = zoom at cursor,  right-drag = pan
Hollow circles = PROPOSED points (not verified) shown only as a hint. They are never saved.
Running it twice on the same frame (--out run1 / run2) lets uncertainty.py measure click error.
"""
import argparse, json, os, time
import matplotlib; matplotlib.use("QtAgg")   # needs PyQt5 (no tkinter on this machine)
import matplotlib.pyplot as plt, matplotlib.image as mpimg
for k in [k for k in plt.rcParams if k.startswith("keymap.")]: plt.rcParams[k] = []   # only our own keys should do anything

NAMES = [f"{g}_{c}" for g in ("pallet", "load") for c in ("BL", "BR", "TR", "TL")] + [f"face2_{i}" for i in range(1, 5)] \
    + ["ref_truck_rear", "ref_carriage_face", "ref_mast_top", "ref_front_wheel_ground", "load_end_right_ground", "feet_leftmost", "feet_rightmost"]

ap = argparse.ArgumentParser(); ap.add_argument("frame"); ap.add_argument("--out", default="outputs/points.json"); ap.add_argument("--proposed")
a = ap.parse_args(); key = os.path.basename(a.frame)

data = json.load(open(a.out)) if os.path.exists(a.out) else {}
pts = dict(data.get(key, {}))                      # name -> [x, y]
proposed = json.load(open(a.proposed)).get(key, {}) if a.proposed else {}

status = [""]
fig, ax = plt.subplots(figsize=(14, 8)); ax.imshow(mpimg.imread(a.frame)); artists = []; pan = {}

def next_name():
    return next((n for n in NAMES if n not in pts), None)       # a point stored as None counts as "not visible" = done

def title():
    nxt = next_name()
    ax.set_title(f"{key}   next: {nxt or 'done - press q'}   [{status[0]}]\n(click=place  u=undo  n=not visible  k=skip face2  s=save  q=save+quit)"); fig.canvas.draw_idle()

def redraw():
    for t in artists: t.remove()
    artists.clear()
    for n, (x, y) in proposed.items():                                   # hints
        artists.append(ax.plot(x, y, "o", mfc="none", mec="orange", ms=10)[0])
    for n, p in pts.items():                                             # my clicks (None = not visible)
        if p is None: continue
        x, y = p
        artists.append(ax.plot(x, y, "+", color="red", ms=14, mew=1.5)[0]); artists.append(ax.text(x + 6, y - 6, n, color="red", fontsize=8))
    title()

def save():
    data[key] = pts
    json.dump(data, open(a.out + ".tmp", "w"), indent=1); os.replace(a.out + ".tmp", a.out)   # write whole file, then swap
    n_vis = sum(p is not None for p in pts.values()); status[0] = f"saved {time.strftime('%H:%M:%S')}: {n_vis} points, {len(pts) - n_vis} not visible"
    print(f"saved {a.out} ({status[0]})"); title()

def on_click(e):
    tb = fig.canvas.toolbar
    if e.inaxes != ax or e.button != 1 or (tb is not None and tb.mode != ""): return   # ignore clicks while zoom/pan is on
    nxt = next_name()
    if nxt: pts[nxt] = [round(e.xdata, 1), round(e.ydata, 1)]; status[0] = ""; redraw()

def on_key(e):
    nxt = next_name()
    if e.key == "u" and pts: pts.pop(list(pts)[-1]); status[0] = "undone"; redraw()
    elif e.key == "n" and nxt: pts[nxt] = None; status[0] = f"{nxt} marked not visible"; redraw()
    elif e.key == "k":
        if nxt and nxt.startswith("face2"):
            for n in NAMES:
                if n.startswith("face2") and n not in pts: pts[n] = None
            status[0] = "face2 marked not visible"; redraw()
        else: status[0] = "k only works when the next point is a face2 point"; title()
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
