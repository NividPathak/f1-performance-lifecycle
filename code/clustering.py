"""Milestone 2: k-means and hierarchical clustering of driver-season profiles.

Each row is one driver in one season (2021-2023), summarised from the cleaned
driver-race table. Clustering only works on unlabeled numeric data, so the
driver/team/season labels are set aside and used only to read the results.

Outputs
  data/milestone2/driver_season_profiles.csv    labeled profiles (for reference)
  data/milestone2/clustering_input_scaled.csv   the unlabeled, standardized matrix that gets clustered
  data/milestone2/clustering_assignments.csv    cluster labels per driver-season
  data/milestone2/clustering_results.json       numbers quoted on the site
  assets/img/m2/clu_*.png                       figures
"""

import json

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage
from scipy.spatial.distance import pdist
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_samples, silhouette_score
from sklearn.preprocessing import StandardScaler

import plot_style as ps
from paths import CLEANED_CSV, M2_DATA, M2_IMG

plt = ps.plt
SEED = 42
MIN_RACES = 8  # drop one-off stand-ins; their averages are too noisy

# --- 1. Build driver-season profiles ------------------------------------------------

df = pd.read_csv(CLEANED_CSV)
race_laps = df.groupby(["season", "round"])["laps_completed"].transform("max")
df["first_stop_pct"] = df["first_pitstop_lap"] / race_laps
df["positions_gained"] = np.where(df["did_not_finish"], np.nan, df["grid"] - df["final_position_num"])
df["podium"] = df["final_position_num"].le(3) & ~df["did_not_finish"]
df["grid_drop"] = df["grid"] - df["quali_position"]

g = df.groupby(["season", "driver_code", "driver_name"])
profiles = pd.DataFrame({
    "constructor": g["constructor_name"].agg(lambda s: s.mode().iloc[0]),
    "races": g.size(),
    "avg_grid": g["grid"].mean(),
    "avg_finish": g["final_position_num"].mean(),
    "avg_positions_gained": g["positions_gained"].mean(),
    "points_per_race": g["points"].mean(),
    "podium_rate": g["podium"].mean(),
    "points_finish_rate": g["did_finish_points"].mean(),
    "dnf_rate": g["did_not_finish"].mean(),
    "avg_pitstops": g["num_pitstops"].mean(),
    "avg_first_stop_pct": g["first_stop_pct"].mean(),
    "median_pit_time_s": g["avg_pitstop_duration_s"].median(),
    "avg_grid_drop": g["grid_drop"].mean(),
}).reset_index()
profiles = profiles[profiles["races"] >= MIN_RACES].reset_index(drop=True)
profiles["label"] = profiles["driver_code"] + " '" + profiles["season"].astype(str).str[2:]

FEATURES = ["avg_grid", "avg_finish", "avg_positions_gained", "points_per_race", "podium_rate",
            "points_finish_rate", "dnf_rate", "avg_pitstops", "avg_first_stop_pct",
            "median_pit_time_s", "avg_grid_drop"]

M2_DATA.mkdir(parents=True, exist_ok=True)
profiles.round(4).to_csv(M2_DATA / "driver_season_profiles.csv", index=False)

# --- 2. Unlabeled numeric matrix, standardized ---------------------------------------

X_raw = profiles[FEATURES]
X = StandardScaler().fit_transform(X_raw)
X_df = pd.DataFrame(X, columns=FEATURES).round(4)
X_df.to_csv(M2_DATA / "clustering_input_scaled.csv", index=False)

before = profiles[["label", "constructor"] + FEATURES[:6]].head(8).copy()
ps.table_image(before, M2_IMG / "clu_sample_labeled.png",
               "Before: driver-season profiles (labels + raw units)", col_width=1.3)
ps.table_image(X_df[FEATURES].head(8), M2_IMG / "clu_sample_scaled.png",
               "After: unlabeled, standardized numeric matrix (what k-means and hclust see)", col_width=1.45)

# --- 3. K-means for k = 2..10, silhouette + elbow -------------------------------------

ks = list(range(2, 11))
sil, inertia, km_models = [], [], {}
for k in ks:
    km = KMeans(n_clusters=k, n_init=50, random_state=SEED).fit(X)
    km_models[k] = km
    sil.append(silhouette_score(X, km.labels_))
    inertia.append(km.inertia_)
best_k = ks[int(np.argmax(sil))]

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].plot(ks, sil, marker="o", color=ps.RED, lw=2)
axes[0].scatter([best_k], [max(sil)], s=160, facecolors="none", edgecolors=ps.AMBER, lw=2, zorder=5)
axes[0].annotate(f"best k = {best_k}", (best_k, max(sil)), xytext=(12, -4), textcoords="offset points", color=ps.AMBER)
axes[0].set(title="Average silhouette by k", xlabel="k (number of clusters)", ylabel="mean silhouette")
total_ss = float(((X - X.mean(axis=0)) ** 2).sum())  # inertia at k = 1
axes[1].plot([1] + ks, [total_ss] + inertia, marker="o", color=ps.ICE, lw=2)
axes[1].set_xticks([1] + ks)
axes[1].set(title="Elbow: within-cluster sum of squares", xlabel="k", ylabel="inertia")
ps.save(fig, M2_IMG / "clu_silhouette_elbow.png")

def name_clusters(labels):
    """Order clusters by average points per race so cluster 1 is always the strongest."""
    order = profiles.assign(c=labels).groupby("c")["points_per_race"].mean().sort_values(ascending=False).index
    remap = {old: new for new, old in enumerate(order)}
    return np.array([remap[l] for l in labels])


km_labels = {k: name_clusters(km_models[k].labels_) for k in ks}

# Per-sample silhouette plots for the three k values we compare
COMPARE_K = [2, 3, 4]
fig, axes = plt.subplots(1, len(COMPARE_K), figsize=(4.2 * len(COMPARE_K), 4.6), sharey=False)
for ax, k in zip(axes, COMPARE_K):
    labels = km_labels[k]
    s_vals = silhouette_samples(X, labels)
    y = 0
    for c in range(k):
        vals = np.sort(s_vals[labels == c])
        ax.fill_betweenx(np.arange(y, y + len(vals)), 0, vals, color=ps.PALETTE[c], alpha=0.9)
        ax.text(-0.08, y + len(vals) / 2, str(c + 1), color=ps.DIM, va="center")
        y += len(vals) + 3
    ax.axvline(s_vals.mean(), color=ps.AMBER, ls="--", lw=1.4)
    ax.set(title=f"k = {k}   (mean {s_vals.mean():.2f})", xlabel="silhouette coefficient", yticks=[])
    ax.set_xlim(-0.2, 0.8)
ps.save(fig, M2_IMG / "clu_silhouette_profiles.png")

# --- 4. K-means clusters drawn on a 2-D PCA projection --------------------------------

pca2 = PCA(n_components=2, random_state=SEED).fit(X)
P = pca2.transform(X)
ev = pca2.explained_variance_ratio_



fig, axes = plt.subplots(1, len(COMPARE_K), figsize=(5.2 * len(COMPARE_K), 4.8))
highlight = {"VER '23", "HAM '21", "ALO '23", "LAT '22", "SAR '23", "STR '22"}
for ax, k in zip(axes, COMPARE_K):
    lab = km_labels[k]
    for c in range(k):
        m = lab == c
        ax.scatter(P[m, 0], P[m, 1], s=46, color=ps.PALETTE[c], edgecolor=ps.BG, lw=0.6, label=f"cluster {c + 1}")
    centers = pca2.transform(km_models[k].cluster_centers_)
    ax.scatter(centers[:, 0], centers[:, 1], marker="X", s=170, color="white", edgecolor=ps.BG, lw=1, zorder=5)
    for i, txt in enumerate(profiles["label"]):
        if txt in highlight:
            ax.annotate(txt, (P[i, 0], P[i, 1]), xytext=(4, 4), textcoords="offset points", fontsize=7.5, color=ps.DIM)
    ax.set(title=f"k-means, k = {k}", xlabel=f"PC1 ({ev[0]:.0%} of variance)", ylabel=f"PC2 ({ev[1]:.0%})")
    ax.legend(fontsize=8, loc="best")
ps.save(fig, M2_IMG / "clu_kmeans_pca.png")

# --- 5. Hierarchical clustering with cosine distance ----------------------------------

D = pdist(X, metric="cosine")
Z = linkage(D, method="average")

# hclust suggestion: biggest jump between consecutive merge heights (top of the tree)
heights = Z[:, 2]
gaps = np.diff(heights)
top = gaps[-9:]  # only look at cuts that leave 2..10 clusters
hc_gap_k = int(np.argmax(top[::-1]) + 2)
hc_sil = {k: silhouette_score(X, fcluster(Z, k, criterion="maxclust"), metric="cosine") for k in ks}
hc_sil_k = max(hc_sil, key=hc_sil.get)
HC_K = hc_gap_k
hc_labels = name_clusters(fcluster(Z, HC_K, criterion="maxclust") - 1)
cut_height = (heights[-HC_K] + heights[-HC_K + 1]) / 2

fig, ax = plt.subplots(figsize=(15, 6))
dendrogram(Z, labels=profiles["label"].tolist(), color_threshold=cut_height, above_threshold_color=ps.DIM,
           leaf_font_size=7.5, ax=ax)
ax.axhline(cut_height, color=ps.AMBER, ls="--", lw=1.2)
ax.text(ax.get_xlim()[1], cut_height, f"  cut -> {HC_K} clusters", color=ps.AMBER, va="bottom", ha="right")
ax.set(title="Hierarchical clustering of driver-seasons (cosine distance, average linkage)", ylabel="cosine distance")
ax.grid(axis="x", visible=False)
for t in ax.get_xticklabels():
    t.set_color(ps.TEXT)
ps.save(fig, M2_IMG / "clu_dendrogram.png")

fig, ax = plt.subplots(figsize=(6.5, 4))
ax.plot(list(hc_sil), list(hc_sil.values()), marker="o", color=ps.VIOLET, lw=2, label="hclust (cosine)")
ax.plot(ks, sil, marker="o", color=ps.RED, lw=2, alpha=0.7, label="k-means (euclidean)")
ax.set(title="Silhouette by number of clusters", xlabel="k", ylabel="mean silhouette")
ax.legend()
ps.save(fig, M2_IMG / "clu_hc_vs_km_silhouette.png")

# --- 6. Compare hclust with k-means ---------------------------------------------------

ari = {k: adjusted_rand_score(km_labels[k], fcluster(Z, k, criterion="maxclust")) for k in COMPARE_K}
hc_sizes = {k: np.bincount(fcluster(Z, k, criterion="maxclust")).tolist()[1:] for k in COMPARE_K}
crosstabs = {}
fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), gridspec_kw={"width_ratios": [2, 4]})
for ax, k in zip(axes, [2, 4]):
    hk = name_clusters(fcluster(Z, k, criterion="maxclust") - 1)
    ct = pd.crosstab(pd.Series(km_labels[k] + 1, name="k-means"), pd.Series(hk + 1, name="hclust"))
    crosstabs[k] = ct
    ax.imshow(ct.values, cmap="Reds", vmin=0)
    for i in range(ct.shape[0]):
        for j in range(ct.shape[1]):
            v = ct.values[i, j]
            ax.text(j, i, v, ha="center", va="center", weight="bold",
                    color="white" if v > ct.values.max() / 2 else "#222")
    ax.set_xticks(range(ct.shape[1]), [f"H{c}" for c in ct.columns])
    ax.set_yticks(range(ct.shape[0]), [f"K{c}" for c in ct.index])
    ax.set(title=f"k = {k}  (ARI {adjusted_rand_score(km_labels[k], hk):.2f})", xlabel="hclust cluster", ylabel="k-means cluster")
    ax.grid(False)
ct = crosstabs[2]
ps.save(fig, M2_IMG / "clu_crosstab.png")

# --- 7. What each cluster looks like (best-k k-means) ---------------------------------

# Silhouette prefers k=2, but k=4 is the most readable split for racing, so profile that one.
final_k = 4
profiles["kmeans_cluster"] = km_labels[final_k] + 1
profiles["hclust_cluster"] = hc_labels + 1
for k in COMPARE_K:
    profiles[f"kmeans_k{k}"] = km_labels[k] + 1

centroids = profiles.groupby("kmeans_cluster")[FEATURES].mean()
z = (centroids - X_raw.mean()) / X_raw.std()
fig, ax = plt.subplots(figsize=(11, 0.75 * final_k + 2.2))
im = ax.imshow(z.values, cmap="RdBu_r", vmin=-2, vmax=2, aspect="auto")
ax.set_xticks(range(len(FEATURES)), [f.replace("_", " ") for f in FEATURES], rotation=30, ha="right")
ax.set_yticks(range(final_k), [f"Cluster {c} (n={int((profiles.kmeans_cluster == c).sum())})" for c in centroids.index])
for i in range(z.shape[0]):
    for j in range(z.shape[1]):
        ax.text(j, i, f"{centroids.values[i, j]:.2f}", ha="center", va="center", fontsize=8,
                color="white" if abs(z.values[i, j]) > 1.1 else "black")
ax.set_title(f"Cluster centroids, k = {final_k} (colour = z-score, number = raw average)")
ax.grid(False)
fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01)
ps.save(fig, M2_IMG / "clu_centroids.png")

profiles[["season", "driver_code", "driver_name", "constructor", "label", "kmeans_cluster", "hclust_cluster"]
         + [f"kmeans_k{k}" for k in COMPARE_K]].to_csv(M2_DATA / "clustering_assignments.csv", index=False)

# --- 8. Overview diagrams (concept images, synthetic data) ----------------------------

rng = np.random.default_rng(7)
blobs = np.vstack([rng.normal(c, 0.55, (25, 2)) for c in [(0, 0), (4, 1), (2, 4)]])
toy_km = KMeans(3, n_init=10, random_state=SEED).fit(blobs)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
for c in range(3):
    axes[0].scatter(*blobs[toy_km.labels_ == c].T, s=30, color=ps.PALETTE[c])
axes[0].scatter(*toy_km.cluster_centers_.T, marker="X", s=200, color="white", edgecolor=ps.BG)
axes[0].set(title="Partitional (k-means)\npick k, assign each point to the nearest centroid", xticks=[], yticks=[])
toy_Z = linkage(blobs[::3], "average")
dendrogram(toy_Z, ax=axes[1], no_labels=True, color_threshold=(toy_Z[-2, 2] + toy_Z[-3, 2]) / 2, above_threshold_color=ps.DIM)
axes[1].set(title="Hierarchical (agglomerative)\nmerge the closest groups into a tree", ylabel="merge distance")
axes[1].grid(axis="x", visible=False)
ps.save(fig, M2_IMG / "clu_concept_partitional_vs_hier.png")

fig, ax = plt.subplots(figsize=(6, 5))
a, b = np.array([4.0, 1.0]), np.array([1.6, 0.5])
c = np.array([1.2, 3.6])
for v, col, name in [(a, ps.RED, "A"), (b, ps.ICE, "B"), (c, ps.AMBER, "C")]:
    ax.annotate("", v, (0, 0), arrowprops=dict(arrowstyle="-|>", color=col, lw=2.4))
    ax.text(*(v + 0.12), name, color=col, weight="bold", fontsize=13)
ax.plot(*zip(a, b), ls=":", color=ps.DIM)
ax.text(2.4, 1.15, "euclidean A-B is long", color=ps.DIM, fontsize=9.5)
ax.text(1.9, 0.12, "but the angle A-B is tiny,\nso cosine distance is ~0", color=ps.ICE, fontsize=9.5)
ax.text(1.3, 2.4, "angle A-C is wide:\ncosine distance is large", color=ps.AMBER, fontsize=9.5)
ax.set(xlim=(-0.2, 4.8), ylim=(-0.2, 4.2), title="Euclidean vs cosine distance", xticks=[], yticks=[])
ps.save(fig, M2_IMG / "clu_concept_cosine.png")

# --- 9. Numbers for the write-up ------------------------------------------------------

summary = {
    "n_profiles": len(profiles), "features": FEATURES, "min_races": MIN_RACES,
    "silhouette_kmeans": dict(zip(ks, map(float, sil))), "best_k": best_k,
    "compare_k": COMPARE_K, "hclust_gap_k": hc_gap_k, "hclust_silhouette": {k: float(v) for k, v in hc_sil.items()},
    "hclust_silhouette_best_k": hc_sil_k, "ari": {k: float(v) for k, v in ari.items()},
    "crosstab": ct.to_dict(), "crosstab_k4": crosstabs[4].to_dict(), "hclust_sizes": hc_sizes, "pca2_var": ev.tolist(),
    "clusters": {int(c): sorted(profiles.loc[profiles.kmeans_cluster == c, "label"]) for c in centroids.index},
    "hclusters": {int(c): sorted(profiles.loc[profiles.hclust_cluster == c, "label"]) for c in sorted(profiles.hclust_cluster.unique())},
    "centroids": centroids.round(3).to_dict(orient="index"),
    **{f"clusters_k{k}": {int(c): sorted(profiles.loc[profiles[f'kmeans_k{k}'] == c, 'label'])
                          for c in sorted(profiles[f'kmeans_k{k}'].unique())} for k in COMPARE_K},
}
(M2_DATA / "clustering_results.json").write_text(json.dumps(summary, indent=2, default=str))
print(json.dumps({k: summary[k] for k in ["n_profiles", "best_k", "compare_k", "hclust_gap_k", "hclust_silhouette_best_k", "ari"]}, indent=1))
