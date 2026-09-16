"""Generate a simple, original, non-trademarked illustrative graphic for the
Introduction tab: a stylized race circuit with a starting grid, built purely
from matplotlib shapes (no logos, liveries, or real team/driver imagery)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path
import numpy as np

from paths import IMG

fig, ax = plt.subplots(figsize=(9, 5.5))
ax.set_facecolor("#f4f4f6")
fig.patch.set_facecolor("#f4f4f6")

# Stylized closed-loop circuit path
t = np.linspace(0, 2 * np.pi, 400)
x = 6 * np.cos(t) + 1.5 * np.cos(3 * t)
y = 3.2 * np.sin(t) + 0.8 * np.sin(2 * t)
ax.plot(x, y, color="#15151e", linewidth=14, solid_capstyle="round", zorder=1)
ax.plot(x, y, color="#ffffff", linewidth=9, solid_capstyle="round", zorder=2)
ax.plot(x, y, color="#15151e", linewidth=1.5, linestyle=(0, (3, 4)), zorder=3)

# Start/finish straight with checkered marker
sx, sy = x[0], y[0]
ax.scatter([sx], [sy], s=260, marker="s", facecolor="white", edgecolor="black", linewidth=1.5, zorder=4)
for i in range(4):
    for j in range(2):
        if (i + j) % 2 == 0:
            ax.add_patch(mpatches.Rectangle((sx - 0.5 + i * 0.25, sy - 0.15 + j * 0.15),
                                             0.25, 0.15, facecolor="black", zorder=5))

# Starting grid dots (two staggered columns, generic, no team colors/logos,
# alternating flat red and black, no gradient)
grid_x = sx - 1.3
for i in range(10):
    col_offset = 0.18 if i % 2 == 0 else 0.0
    gx = grid_x - (i * 0.32)
    gy = sy - 0.55 - col_offset
    dot_color = "#e10600" if i % 2 == 0 else "#15151e"
    ax.scatter([gx], [gy], s=70, color=dot_color, zorder=4)

ax.set_xlim(-9, 9)
ax.set_ylim(-5.5, 5.5)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("A Formula 1 race weekend: starting grid, circuit, and strategy calls\ncombine to decide the finishing order",
              fontsize=12, color="#15151e", pad=14)

fig.tight_layout()
fig.savefig(IMG / "intro_illustration.png", dpi=170, bbox_inches="tight", facecolor=fig.get_facecolor())
print("saved assets/img/intro_illustration.png")
