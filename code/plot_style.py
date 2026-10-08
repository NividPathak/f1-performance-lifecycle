"""Shared matplotlib look so the Milestone 2 figures match the site's dark theme."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BG = "#0b0b0e"
PANEL = "#121217"
LINE = "#26262e"
TEXT = "#ececef"
DIM = "#9a9aa3"
RED = "#e10600"
AMBER = "#ffb020"
ICE = "#7fd4ff"
GREEN = "#3ddc84"
VIOLET = "#b58cff"
PALETTE = [RED, ICE, AMBER, GREEN, VIOLET, "#ff7ab6", "#c9c9cf", "#4f8cff"]

# Team colours from each team's latest livery. Alfa Romeo and AlphaTauri use the
# colours of the teams they became (Sauber, Racing Bulls). Alpine uses its pink so
# it doesn't blur with the three blues.
TEAM_COLORS = {
    "Red Bull": "#1f3fb0",
    "Ferrari": "#e8002d",
    "Mercedes": "#27f4d2",
    "McLaren": "#ff8000",
    "Aston Martin": "#229971",
    "Alpine F1 Team": "#ff87bc",
    "Williams": "#64c4ff",
    "AlphaTauri": "#f0f2ff",
    "Alfa Romeo": "#52e252",
    "Haas F1 Team": "#9c9fa2",
}
TEAM_ORDER = list(TEAM_COLORS)
TEAM_SHORT = {"Alpine F1 Team": "Alpine", "Haas F1 Team": "Haas"}


def team_legend(ax, **kw):
    """Legend with one dot per team, in a fixed order."""
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker="o", ls="", markersize=7, markerfacecolor=TEAM_COLORS[t],
                      markeredgecolor="white", markeredgewidth=0.5, label=TEAM_SHORT.get(t, t)) for t in TEAM_ORDER]
    return ax.legend(handles=handles, title="team", title_fontsize=9, fontsize=8.5, **kw)

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": PANEL,
    "savefig.facecolor": BG,
    "axes.edgecolor": LINE,
    "axes.labelcolor": TEXT,
    "axes.titlecolor": TEXT,
    "axes.titleweight": "bold",
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "axes.grid": True,
    "grid.color": LINE,
    "grid.linewidth": 0.7,
    "xtick.color": DIM,
    "ytick.color": DIM,
    "text.color": TEXT,
    "legend.facecolor": PANEL,
    "legend.edgecolor": LINE,
    "legend.labelcolor": TEXT,
    "font.family": "sans-serif",
    "font.size": 10.5,
    "axes.prop_cycle": plt.cycler(color=PALETTE),
})


def save(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("wrote", path.name)
