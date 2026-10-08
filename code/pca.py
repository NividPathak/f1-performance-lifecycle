# Milestone 2 - PCA
# PCA on driver-race rows from the races that have FastF1 weather + tyre data

import json

import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

import plot_style as ps
from paths import CLEANED_CSV, M2_DATA, M2_IMG
from sample_format import table_rows

plt = ps.plt
M2_DATA.mkdir(parents=True, exist_ok=True)

FEATURES = ["quali_position", "grid", "final_position_num", "positions_gained", "points", "laps_pct",
            "num_pitstops", "first_stop_pct", "avg_pitstop_duration_s", "num_compounds_used",
            "air_temp_mean", "track_temp_mean", "humidity_mean"]
LABELS = ["season", "round", "race_name", "driver_code", "constructor_name", "did_not_finish", "rainfall"]

SHORT = {"quali_position": "quali pos", "grid": "grid", "final_position_num": "finish pos",
         "positions_gained": "positions gained", "points": "points", "laps_pct": "laps completed %",
         "num_pitstops": "pit stops", "first_stop_pct": "first stop (% of race)",
         "avg_pitstop_duration_s": "pit lane time", "num_compounds_used": "compounds used",
         "air_temp_mean": "air temp", "track_temp_mean": "track temp", "humidity_mean": "humidity"}


# ---------- data prep ----------

df = pd.read_csv(CLEANED_CSV)
df["race_laps"] = df.groupby(["season", "round"])["laps_completed"].transform("max")
df["laps_pct"] = df["laps_completed"] / df["race_laps"]
df["first_stop_pct"] = df["first_pitstop_lap"] / df["race_laps"]
df["positions_gained"] = df["grid"] - df["final_position_num"]

# only races with weather data, and drop drivers who never pitted (no first stop / pit time)
data = df[df["air_temp_mean"].notna()]
print("rows with weather:", len(data))
data = data.dropna(subset=FEATURES).reset_index(drop=True)
print("rows used:", len(data), "races:", data.groupby(["season", "round"]).ngroups)
data[LABELS + FEATURES].round(4).to_csv(M2_DATA / "pca_input_labeled.csv", index=False)

X = StandardScaler().fit_transform(data[FEATURES])
X_df = pd.DataFrame(X, columns=FEATURES).round(4)
X_df.to_csv(M2_DATA / "pca_input_scaled.csv", index=False)

tables_file = M2_DATA / "sample_tables.json"
tables = {}
if tables_file.exists():
    tables = json.loads(tables_file.read_text())
tables["pca_labeled"] = table_rows(data[["season", "round", "driver_code", "constructor_name"] + FEATURES].head(8))
tables["pca_scaled"] = table_rows(X_df.head(8))
tables_file.write_text(json.dumps(tables, indent=1))


# ---------- PCA ----------

pca = PCA().fit(X)
eig = pca.explained_variance_
var = pca.explained_variance_ratio_
cum = np.cumsum(var)
n95 = np.searchsorted(cum, 0.95) + 1
scores = pca.transform(X)

pcs = [f"PC{i + 1}" for i in range(len(FEATURES))]
loadings = pd.DataFrame(pca.components_.T, index=FEATURES, columns=pcs)
corr = loadings * np.sqrt(eig)

print("eigenvalues:", np.round(eig, 2))
print("variance %:", np.round(var * 100, 1))
print("cumulative %:", np.round(cum * 100, 1))
print("PCs for 95%:", n95, " eigenvalue > 1:", (eig > 1).sum())
print(loadings.iloc[:, :5].round(2))

out = data[LABELS].copy()
out["PC1"] = scores[:, 0].round(4)
out["PC2"] = scores[:, 1].round(4)
out["PC3"] = scores[:, 2].round(4)
out.to_csv(M2_DATA / "pca_scores.csv", index=False)
print(out.groupby("rainfall")[["PC2", "PC3"]].mean().round(2))


def draw_arrows(ax, xy, color, min_len, scale=1.0):
    # arrows that point the same way get one shared label, otherwise the text piles up
    groups = []
    for f, (x, y) in xy.items():
        ax.annotate("", (x * scale, y * scale), (0, 0), arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6))
        length = np.hypot(x, y)
        angle = np.degrees(np.arctan2(y, x))
        if length < min_len:
            continue
        for grp in groups:
            same_dir = abs((grp["angle"] - angle + 180) % 360 - 180) < 9
            same_len = abs(grp["len"] - length) < 0.25 * max(grp["len"], length)
            if same_dir and same_len:
                grp["names"].append(SHORT[f])
                break
        else:
            groups.append({"angle": angle, "len": length, "x": x, "y": y, "names": [SHORT[f]]})
    for grp in groups:
        x, y = grp["x"] * scale * 1.06, grp["y"] * scale * 1.06
        y += 0.04 * scale if y >= 0 else -0.04 * scale
        ha = "left" if grp["x"] > 0.05 else ("right" if grp["x"] < -0.05 else "center")
        ax.text(x, y, " / ".join(grp["names"]), color=color, fontsize=9, weight="bold", ha=ha, va="center",
                bbox=dict(boxstyle="round,pad=0.2", fc=ps.BG, ec="none", alpha=0.75))


# ---------- scree plot ----------

idx = np.arange(1, len(FEATURES) + 1)
fig, ax = plt.subplots(figsize=(9, 4.4))
ax.bar(idx, var * 100, color=ps.RED, alpha=0.9, label="variance explained by each PC")
for i in range(4):
    ax.text(i + 1, var[i] * 100 - 1.6, f"{var[i]:.0%}", ha="center", color="white", fontsize=9, weight="bold")
ax.set(title="Scree plot: how much variance each principal component keeps", xlabel="principal component",
       ylabel="% of variance", xticks=idx, ylim=(0, var[0] * 118))
ax2 = ax.twinx()
ax2.plot(idx, cum * 100, color=ps.ICE, marker="o", lw=2, label="cumulative")
ax2.axhline(95, color=ps.AMBER, ls="--", lw=1.2)
ax2.text(0.6, 97, "95% of variance", color=ps.AMBER, va="bottom", fontsize=9)
ax2.axvline(n95, color=ps.AMBER, ls=":", lw=1)
ax2.text(n95 + 0.15, 40, f"{n95} PCs reach 95%", color=ps.AMBER, fontsize=9.5)
ax2.set_ylim(0, 105)
ax2.set_ylabel("cumulative %", color=ps.ICE)
ax2.grid(False)
ax2.tick_params(colors=ps.DIM)
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc="center right")
ps.save(fig, M2_IMG / "pca_scree.png")


# ---------- biplot (PC1 vs PC2), dots coloured by team ----------

team_colors = data["constructor_name"].map(ps.TEAM_COLORS).values
fig, ax = plt.subplots(figsize=(10.5, 7.5))
ax.scatter(scores[:, 0], scores[:, 1], s=16, c=team_colors, alpha=0.75, edgecolor="none")
scale = np.abs(scores[:, :2]).max() * 0.85
draw_arrows(ax, {f: (loadings.loc[f, "PC1"], loadings.loc[f, "PC2"]) for f in FEATURES}, ps.AMBER, 0.15, scale)
ax.set(title="Biplot: driver-races on PC1 and PC2, arrows show how each variable loads",
       xlabel=f"PC1 ({var[0]:.0%} of variance)", ylabel=f"PC2 ({var[1]:.0%})")
ps.team_legend(ax, loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
ps.save(fig, M2_IMG / "pca_biplot.png")


# ---------- loadings heatmap ----------

top5 = loadings.iloc[:, :5]
fig, ax = plt.subplots(figsize=(7.5, 6.5))
im = ax.imshow(top5.values, cmap="RdBu_r", vmin=-0.7, vmax=0.7, aspect="auto")
ax.set_xticks(range(5), [f"PC{i + 1}\n{var[i]:.0%}" for i in range(5)])
ax.set_yticks(range(len(FEATURES)), [f.replace("_", " ") for f in FEATURES])
for i in range(len(FEATURES)):
    for j in range(5):
        v = top5.values[i, j]
        ax.text(j, i, f"{v:+.2f}", ha="center", va="center", fontsize=8.5, color="white" if abs(v) > 0.45 else "#111")
ax.set_title("Loadings (eigenvector entries) for the first five PCs")
ax.grid(False)
fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
ps.save(fig, M2_IMG / "pca_loadings.png")


# ---------- 3d plot, team colours, triangles = rain ----------

wet = data["rainfall"].astype(bool).values
fig = plt.figure(figsize=(10.5, 7.5))
ax = fig.add_subplot(projection="3d")
ax.set_facecolor(ps.PANEL)
ax.scatter(scores[~wet, 0], scores[~wet, 1], scores[~wet, 2], s=12, c=team_colors[~wet], alpha=0.7, marker="o")
ax.scatter(scores[wet, 0], scores[wet, 1], scores[wet, 2], s=30, c=team_colors[wet], alpha=0.95, marker="^",
           edgecolor="white", lw=0.4)
ax.set_xlabel(f"PC1 ({var[0]:.0%})")
ax.set_ylabel(f"PC2 ({var[1]:.0%})")
ax.set_zlabel(f"PC3 ({var[2]:.0%})")
for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
    axis.set_pane_color((0.07, 0.07, 0.09, 1))
    axis.label.set_color(ps.TEXT)
ax.tick_params(colors=ps.DIM)
ax.set_title(f"First three PCs together keep {cum[2]:.0%} of the variance")
ax.view_init(elev=22, azim=-58)
leg = ps.team_legend(ax, loc="upper left", bbox_to_anchor=(1.12, 0.95))
ax.add_artist(leg)
shapes = [Line2D([], [], marker="o", ls="", color=ps.DIM, label=f"dry race (n={(~wet).sum()})"),
          Line2D([], [], marker="^", ls="", color=ps.DIM, markeredgecolor="white", label=f"rain during race (n={wet.sum()})")]
ax.legend(handles=shapes, loc="lower left", bbox_to_anchor=(1.12, 0.1), fontsize=8.5)
ps.save(fig, M2_IMG / "pca_3d.png")


# ---------- correlation circles ----------

fig, axes = plt.subplots(1, 2, figsize=(15, 6.8))
for ax, (a, b) in zip(axes, [("PC1", "PC2"), ("PC3", "PC4")]):
    ax.add_patch(plt.Circle((0, 0), 1, fill=False, color=ps.DIM, lw=1))
    draw_arrows(ax, {f: (corr.loc[f, a], corr.loc[f, b]) for f in FEATURES}, ps.ICE, 0.3)
    ia, ib = int(a[2:]) - 1, int(b[2:]) - 1
    ax.set(xlim=(-1.75, 1.75), ylim=(-1.3, 1.3), aspect="equal", title=f"Correlation circle, {a} vs {b}",
           xlabel=f"correlation with {a} ({var[ia]:.0%})", ylabel=f"correlation with {b} ({var[ib]:.0%})")
ps.save(fig, M2_IMG / "pca_corr_circle.png")


# ---------- diagrams for the overview section ----------

rng = np.random.default_rng(3)
toy = rng.multivariate_normal([0, 0], [[3, 2.2], [2.2, 2.2]], 300)
tp = PCA().fit(toy)
fig, ax = plt.subplots(figsize=(6.4, 5.6))
ax.scatter(toy[:, 0], toy[:, 1], s=12, alpha=0.5, color=ps.DIM)
for i, col in enumerate([ps.RED, ps.ICE]):
    end = tp.components_[i] * 2 * np.sqrt(tp.explained_variance_[i])
    ax.annotate("", end, (0, 0), arrowprops=dict(arrowstyle="-|>", color=col, lw=3))
    ax.text(end[0] * 1.15, end[1] * 1.15, f"PC{i + 1}\neigenvalue {tp.explained_variance_[i]:.1f}",
            color=col, ha="center", fontsize=9.5, weight="bold")
ax.set(aspect="equal", title="Eigenvectors give directions,\neigenvalues give the spread along them", xlabel="x1", ylabel="x2")
ps.save(fig, M2_IMG / "pca_concept_eigen.png")

dims = [2, 5, 10, 20, 50, 100, 300, 1000]
ratio = []
for d in dims:
    pts = rng.random((400, d))
    dist = np.linalg.norm(pts[1:] - pts[0], axis=1)
    ratio.append((dist.max() - dist.min()) / dist.min())
fig, ax = plt.subplots(figsize=(6.6, 4.6))
ax.plot(dims, ratio, marker="o", color=ps.RED, lw=2)
ax.set(xscale="log", yscale="log", title="Curse of dimensionality: distances stop being informative",
       xlabel="number of dimensions", ylabel="(farthest - nearest) / nearest distance")
ax.text(dims[3], ratio[1], "in high dimensions every point is\nroughly as far away as every other", color=ps.DIM, fontsize=9)
ps.save(fig, M2_IMG / "pca_concept_curse.png")
