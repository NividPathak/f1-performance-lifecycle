"""Milestone 2: Principal Component Analysis on driver-race rows.

Uses the 38 races that have FastF1 weather and tyre data, so each row carries
13 numeric measurements: qualifying, grid, result, pit strategy, tyres, and
track conditions. PCA needs numeric, unlabeled, standardized data, so labels
are set aside (they are only used afterwards to colour the plots).

Outputs
  data/milestone2/pca_input_labeled.csv   rows with their labels, for reference
  data/milestone2/pca_input_scaled.csv    the unlabeled standardized matrix PCA runs on
  data/milestone2/pca_scores.csv          first three principal component scores per row
  data/milestone2/pca_results.json        numbers quoted on the site
  assets/img/m2/pca_*.png                 figures
"""

import json

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

import plot_style as ps
from paths import CLEANED_CSV, M2_DATA, M2_IMG

plt = ps.plt
SEED = 42

# --- 1. Select rows and numeric columns --------------------------------------------

df = pd.read_csv(CLEANED_CSV)
df["race_laps"] = df.groupby(["season", "round"])["laps_completed"].transform("max")
df["laps_pct"] = df["laps_completed"] / df["race_laps"]
df["first_stop_pct"] = df["first_pitstop_lap"] / df["race_laps"]
df["positions_gained"] = df["grid"] - df["final_position_num"]

FEATURES = ["quali_position", "grid", "final_position_num", "positions_gained", "points", "laps_pct",
            "num_pitstops", "first_stop_pct", "avg_pitstop_duration_s", "num_compounds_used",
            "air_temp_mean", "track_temp_mean", "humidity_mean"]
LABELS = ["season", "round", "race_name", "driver_code", "constructor_name", "did_not_finish", "rainfall"]

data = df[df["air_temp_mean"].notna()].dropna(subset=FEATURES).reset_index(drop=True)
n_weather_rows = int(df["air_temp_mean"].notna().sum())

M2_DATA.mkdir(parents=True, exist_ok=True)
data[LABELS + FEATURES].round(4).to_csv(M2_DATA / "pca_input_labeled.csv", index=False)

scaler = StandardScaler()
X = scaler.fit_transform(data[FEATURES])
X_df = pd.DataFrame(X, columns=FEATURES).round(4)
X_df.to_csv(M2_DATA / "pca_input_scaled.csv", index=False)

before = data[["race_name", "driver_code", "did_not_finish"] + FEATURES[:7]].head(8).copy()
before["race_name"] = before["race_name"].str.replace(" Grand Prix", " GP")
ps.table_image(before, M2_IMG / "pca_sample_labeled.png",
               "Before: driver-race rows with labels, raw units", col_width=1.3)
ps.table_image(X_df.head(8), M2_IMG / "pca_sample_scaled.png",
               "After: 13 unlabeled numeric columns, standardized to mean 0 and sd 1", col_width=1.3)

# --- 2. Fit PCA with every component -----------------------------------------------

pca = PCA(random_state=SEED).fit(X)
ev_ratio = pca.explained_variance_ratio_
cum = np.cumsum(ev_ratio)
eigenvalues = pca.explained_variance_
n95 = int(np.searchsorted(cum, 0.95) + 1)
n_kaiser = int((eigenvalues > 1).sum())
scores = pca.transform(X)
loadings = pd.DataFrame(pca.components_.T, index=FEATURES, columns=[f"PC{i + 1}" for i in range(len(FEATURES))])

pd.concat([data[LABELS], pd.DataFrame(scores[:, :3], columns=["PC1", "PC2", "PC3"]).round(4)], axis=1) \
    .to_csv(M2_DATA / "pca_scores.csv", index=False)


SHORT = {"quali_position": "quali pos", "grid": "grid", "final_position_num": "finish pos",
         "positions_gained": "positions gained", "points": "points", "laps_pct": "laps completed %",
         "num_pitstops": "pit stops", "first_stop_pct": "first stop (% of race)",
         "avg_pitstop_duration_s": "pit lane time", "num_compounds_used": "compounds used",
         "air_temp_mean": "air temp", "track_temp_mean": "track temp", "humidity_mean": "humidity"}


def draw_arrows(ax, vecs, color, min_len=0.12, scale=1.0):
    """Draw loading arrows; arrows pointing the same way share one label so text never piles up."""
    groups = []
    for f, (x, y) in vecs.items():
        ax.annotate("", (x * scale, y * scale), (0, 0), arrowprops=dict(arrowstyle="-|>", color=color, lw=1.6))
        length, ang = np.hypot(x, y), np.degrees(np.arctan2(y, x))
        if length < min_len:
            continue
        for g in groups:
            if abs((g["ang"] - ang + 180) % 360 - 180) < 9 and abs(g["len"] - length) < 0.25 * max(g["len"], length):
                g["names"].append(SHORT[f])
                break
        else:
            groups.append({"ang": ang, "len": length, "x": x, "y": y, "names": [SHORT[f]]})
    for g in groups:
        ha = "left" if g["x"] > 0.05 else "right" if g["x"] < -0.05 else "center"
        ax.text(g["x"] * scale * 1.06, g["y"] * scale * 1.06 + (0.04 * scale if g["y"] >= 0 else -0.04 * scale),
                " / ".join(g["names"]), color=color, fontsize=9, weight="bold", ha=ha, va="center",
                bbox=dict(boxstyle="round,pad=0.2", fc=ps.BG, ec="none", alpha=0.75))

# --- 3. Scree + cumulative variance ------------------------------------------------

idx = np.arange(1, len(FEATURES) + 1)
fig, ax = plt.subplots(figsize=(9, 4.4))
ax.bar(idx, ev_ratio * 100, color=ps.RED, alpha=0.9, label="variance explained by each PC")
ax2 = ax.twinx()
ax2.plot(idx, cum * 100, color=ps.ICE, marker="o", lw=2, label="cumulative")
ax2.axhline(95, color=ps.AMBER, ls="--", lw=1.2)
ax2.text(0.6, 97, "95% of variance", color=ps.AMBER, va="bottom", fontsize=9)
ax2.axvline(n95, color=ps.AMBER, ls=":", lw=1)
ax2.text(n95 + 0.15, 40, f"{n95} PCs reach 95%", color=ps.AMBER, fontsize=9.5)
ax2.set_ylim(0, 105)
ax2.grid(False)
ax2.tick_params(colors=ps.DIM)
for i, v in enumerate(ev_ratio[:4]):
    ax.text(i + 1, v * 100 - 1.6, f"{v:.0%}", ha="center", color="white", fontsize=9, weight="bold")
ax.set(title="Scree plot: how much variance each principal component keeps", xlabel="principal component",
       ylabel="% of variance", xticks=idx, ylim=(0, ev_ratio[0] * 100 * 1.18))
ax2.set_ylabel("cumulative %", color=ps.ICE)
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc="center right")
ps.save(fig, M2_IMG / "pca_scree.png")

# --- 4. Biplot: rows in PC1-PC2 space with loading arrows ---------------------------

finish_band = np.select([data["did_not_finish"], data["points"] > 0], ["did not finish", "scored points"], "finished, no points")
band_colors = {"scored points": ps.RED, "finished, no points": ps.ICE, "did not finish": ps.DIM}
fig, ax = plt.subplots(figsize=(9.5, 7.5))
for band, col in band_colors.items():
    m = finish_band == band
    ax.scatter(scores[m, 0], scores[m, 1], s=14, alpha=0.55, color=col, label=f"{band} (n={m.sum()})")
scale = np.abs(scores[:, :2]).max() * 0.85
draw_arrows(ax, {f: tuple(loadings.loc[f, ["PC1", "PC2"]]) for f in FEATURES}, ps.AMBER, min_len=0.15, scale=scale)
ax.set(title="Biplot: driver-races on PC1 and PC2, arrows show how each variable loads",
       xlabel=f"PC1 ({ev_ratio[0]:.0%} of variance)", ylabel=f"PC2 ({ev_ratio[1]:.0%})")
ax.legend(loc="lower left", markerscale=2)
ps.save(fig, M2_IMG / "pca_biplot.png")

# --- 5. Loadings heatmap -----------------------------------------------------------

show = loadings.iloc[:, :5]
fig, ax = plt.subplots(figsize=(7.5, 6.5))
im = ax.imshow(show.values, cmap="RdBu_r", vmin=-0.7, vmax=0.7, aspect="auto")
ax.set_xticks(range(show.shape[1]), [f"{c}\n{ev_ratio[i]:.0%}" for i, c in enumerate(show.columns)])
ax.set_yticks(range(len(FEATURES)), [f.replace("_", " ") for f in FEATURES])
for i in range(show.shape[0]):
    for j in range(show.shape[1]):
        v = show.values[i, j]
        ax.text(j, i, f"{v:+.2f}", ha="center", va="center", fontsize=8.5, color="white" if abs(v) > 0.45 else "#111")
ax.set_title("Loadings (eigenvector entries) for the first five PCs")
ax.grid(False)
fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
ps.save(fig, M2_IMG / "pca_loadings.png")

# --- 6. 3-D projection, coloured by conditions ------------------------------------

fig = plt.figure(figsize=(9, 7))
ax = fig.add_subplot(projection="3d")
ax.set_facecolor(ps.PANEL)
wet = data["rainfall"].astype(bool).values
for m, col, lab in [(~wet, ps.ICE, f"dry race (n={(~wet).sum()})"), (wet, ps.RED, f"rain during race (n={wet.sum()})")]:
    ax.scatter(scores[m, 0], scores[m, 1], scores[m, 2], s=10, alpha=0.6, color=col, label=lab)
ax.set_xlabel(f"PC1 ({ev_ratio[0]:.0%})")
ax.set_ylabel(f"PC2 ({ev_ratio[1]:.0%})")
ax.set_zlabel(f"PC3 ({ev_ratio[2]:.0%})")
for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis.set_pane_color((0.07, 0.07, 0.09, 1))
    axis.label.set_color(ps.TEXT)
ax.tick_params(colors=ps.DIM)
ax.set_title(f"First three PCs together keep {cum[2]:.0%} of the variance")
ax.legend(loc="upper left")
ax.view_init(elev=22, azim=-58)
ps.save(fig, M2_IMG / "pca_3d.png")

# --- 7. Correlation circles: how each variable correlates with the PCs ---------------

corr = loadings * np.sqrt(eigenvalues)  # loading x sqrt(eigenvalue) = correlation with the PC
fig, axes = plt.subplots(1, 2, figsize=(15, 6.8))
for ax, (a, b) in zip(axes, [("PC1", "PC2"), ("PC3", "PC4")]):
    ax.add_patch(plt.Circle((0, 0), 1, fill=False, color=ps.DIM, lw=1))
    draw_arrows(ax, {f: tuple(corr.loc[f, [a, b]]) for f in FEATURES}, ps.ICE, min_len=0.3)
    ia, ib = int(a[2:]) - 1, int(b[2:]) - 1
    ax.set(xlim=(-1.75, 1.75), ylim=(-1.3, 1.3), aspect="equal", title=f"Correlation circle, {a} vs {b}",
           xlabel=f"correlation with {a} ({ev_ratio[ia]:.0%})", ylabel=f"correlation with {b} ({ev_ratio[ib]:.0%})")
ps.save(fig, M2_IMG / "pca_corr_circle.png")

# --- 8. Overview diagrams (concept images) -----------------------------------------

rng = np.random.default_rng(3)
toy = rng.multivariate_normal([0, 0], [[3, 2.2], [2.2, 2.2]], 300)
tp = PCA().fit(toy)
fig, ax = plt.subplots(figsize=(6.4, 5.6))
ax.scatter(*toy.T, s=12, alpha=0.5, color=ps.DIM)
for vec, val, col, name in zip(tp.components_, tp.explained_variance_, [ps.RED, ps.ICE], ["PC1", "PC2"]):
    end = vec * 2 * np.sqrt(val)
    ax.annotate("", end, (0, 0), arrowprops=dict(arrowstyle="-|>", color=col, lw=3))
    ax.text(*(end * 1.15), f"{name}\neigenvalue {val:.1f}", color=col, ha="center", fontsize=9.5, weight="bold")
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
ax.text(dims[3], ratio[1], "in high dimensions every point is\nroughly as far away as every other",
        color=ps.DIM, fontsize=9)
ps.save(fig, M2_IMG / "pca_concept_curse.png")

# --- 9. Numbers for the write-up ---------------------------------------------------

summary = {
    "n_rows": len(data), "n_weather_rows": n_weather_rows, "n_races": int(data.groupby(["season", "round"]).ngroups),
    "features": FEATURES, "eigenvalues": eigenvalues.round(4).tolist(), "variance_ratio": ev_ratio.round(4).tolist(),
    "cumulative": cum.round(4).tolist(), "n_for_95": n95, "n_kaiser": n_kaiser,
    "var_2d": float(cum[1]), "var_3d": float(cum[2]),
    "loadings": loadings.iloc[:, :4].round(3).to_dict(),
}
(M2_DATA / "pca_results.json").write_text(json.dumps(summary, indent=2))
print(json.dumps({k: summary[k] for k in ["n_rows", "n_races", "n_for_95", "n_kaiser", "var_2d", "var_3d"]}, indent=1))
print("eigenvalues", summary["eigenvalues"])
print(loadings.iloc[:, :4].round(2))
