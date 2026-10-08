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


def table_image(df, path, title, col_width=1.15, row_height=0.42, fmt="{:.2f}"):
    """Render a small DataFrame as a PNG table (for the 'image of the sample' requirement)."""
    cells = [[fmt.format(v) if isinstance(v, float) else str(v) for v in row] for row in df.itertuples(index=False)]
    fig_w = max(6, col_width * len(df.columns))
    fig, ax = plt.subplots(figsize=(fig_w, row_height * (len(df) + 2)))
    ax.axis("off")
    labels = [str(c).replace("_", "\n", 1) if len(str(c)) > 11 else str(c) for c in df.columns]
    tbl = ax.table(cellText=cells, colLabels=labels, loc="center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    tbl.scale(1, 1.35)
    for (r, _), cell in tbl.get_celld().items():
        cell.set_edgecolor(LINE)
        if r == 0:
            cell.set_height(cell.get_height() * 1.7)
            cell.set_facecolor("#1d1d25")
            cell.set_text_props(color=AMBER, weight="bold")
        else:
            cell.set_facecolor(PANEL)
            cell.set_text_props(color=TEXT)
    ax.set_title(title, loc="left", pad=8)
    save(fig, path)
