"""Export the Bahrain International Circuit layout for the Introduction tab's
track map. Uses the position data from the fastest lap of the 2023 Bahrain
Grand Prix (FastF1), rotated the same way the official track map is, plus the
official corner numbers. Writes data/track_bahrain.json.
"""
import json

import fastf1
import numpy as np

from paths import DATA, FASTF1_CACHE

FASTF1_CACHE.mkdir(exist_ok=True)
fastf1.Cache.enable_cache(str(FASTF1_CACHE))


def rotate(xy, angle):
    rot = np.array([[np.cos(angle), np.sin(angle)], [-np.sin(angle), np.cos(angle)]])
    return xy @ rot


session = fastf1.get_session(2023, "Bahrain", "R")
session.load(laps=True, telemetry=True, weather=False, messages=False)
lap = session.laps.pick_fastest()
pos = lap.get_pos_data()
info = session.get_circuit_info()
angle = info.rotation / 180 * np.pi

track = rotate(pos[["X", "Y"]].to_numpy(), angle)
corners = rotate(info.corners[["X", "Y"]].to_numpy(), angle)

# SVG y grows downward, so flip y, then scale everything into a 1000-wide box.
track[:, 1] *= -1
corners[:, 1] *= -1
lo = track.min(axis=0)
scale = 1000 / (track.max(axis=0) - lo).max()
pad = 40
track = (track - lo) * scale + pad
corners = (corners - lo) * scale + pad
width, height = track.max(axis=0) + pad

# Thin the points so the SVG path stays small, then close the loop.
step = max(1, len(track) // 300)
pts = track[::step]
path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"

out = {
    "circuit": "Bahrain International Circuit",
    "source": f"FastF1, {session.event['EventName']} {session.event.year}, fastest lap ({lap['Driver']})",
    "width": round(float(width), 1),
    "height": round(float(height), 1),
    "path": path,
    "start": [round(float(v), 1) for v in pts[0]],
    "corners": [
        {"n": int(n), "x": round(float(x), 1), "y": round(float(y), 1)}
        for n, (x, y) in zip(info.corners["Number"], corners)
    ],
}
with open(DATA / "track_bahrain.json", "w") as f:
    json.dump(out, f)
print("wrote data/track_bahrain.json with", len(pts), "points and", len(out["corners"]), "corners")
