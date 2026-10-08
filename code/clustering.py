# Milestone 2 - clustering
# k-means and hierarchical clustering (cosine) on driver-season profiles

import json

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_samples, silhouette_score
from sklearn.preprocessing import StandardScaler

import plot_style as ps
from paths import CLEANED_CSV, M2_DATA, M2_IMG
from sample_format import table_rows

plt = ps.plt
M2_DATA.mkdir(parents=True, exist_ok=True)

FEATURES = ["avg_grid", "avg_finish", "avg_positions_gained", "points_per_race", "podium_rate",
            "points_finish_rate", "dnf_rate", "avg_pitstops", "avg_first_stop_pct",
            "median_pit_time_s", "avg_grid_drop"]


# ---------- build one row per driver per season ----------

df = pd.read_csv(CLEANED_CSV)
race_laps = df.groupby(["season", "round"])["laps_completed"].transform("max")
df["first_stop_pct"] = df["first_pitstop_lap"] / race_laps
df["positions_gained"] = np.where(df["did_not_finish"], np.nan, df["grid"] - df["final_position_num"])
df["podium"] = (df["final_position_num"] <= 3) & ~df["did_not_finish"]
df["grid_drop"] = df["grid"] - df["quali_position"]

g = df.groupby(["season", "driver_code", "driver_name"])
profiles = pd.DataFrame({
    "constructor_name": g["constructor_name"].agg(lambda s: s.mode()[0]),
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

# stand-in drivers with only a few races make the averages noisy so drop them
profiles = profiles[profiles["races"] >= 8].reset_index(drop=True)
profiles["label"] = profiles["driver_code"] + " '" + profiles["season"].astype(str).str[2:]
profiles.round(4).to_csv(M2_DATA / "driver_season_profiles.csv", index=False)

# clustering only gets numbers, no labels. scale so every column counts the same
X = StandardScaler().fit_transform(profiles[FEATURES])
X_df = pd.DataFrame(X, columns=FEATURES).round(4)
X_df.to_csv(M2_DATA / "clustering_input_scaled.csv", index=False)

# sample rows for the tables on the site
tables_file = M2_DATA / "sample_tables.json"
tables = {}
if tables_file.exists():
    tables = json.loads(tables_file.read_text())
tables["clustering_labeled"] = table_rows(profiles[["season", "driver_code", "constructor_name", "races"] + FEATURES].head(8))
tables["clustering_scaled"] = table_rows(X_df.head(8))
tables_file.write_text(json.dumps(tables, indent=1))


# ---------- k-means for k = 2 to 10 ----------

ks = list(range(2, 11))
models = {}
sil = []
inertia = []
for k in ks:
    km = KMeans(n_clusters=k, n_init=50, random_state=42).fit(X)
    models[k] = km
    sil.append(silhouette_score(X, km.labels_))
    inertia.append(km.inertia_)
best_k = ks[np.argmax(sil)]
print("silhouette:", dict(zip(ks, np.round(sil, 3))))
print("best k:", best_k)


def order_clusters(labels):
    # renumber so cluster 1 has the most points per race, cluster 2 the next etc
    means = profiles.assign(c=labels).groupby("c")["points_per_race"].mean()
    order = list(means.sort_values(ascending=False).index)
    return np.array([order.index(l) for l in labels])


km_labels = {}
for k in ks:
    km_labels[k] = order_clusters(models[k].labels_)

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].plot(ks, sil, marker="o", color=ps.RED, lw=2)
axes[0].scatter([best_k], [max(sil)], s=160, facecolors="none", edgecolors=ps.AMBER, lw=2, zorder=5)
axes[0].annotate(f"best k = {best_k}", (best_k, max(sil)), xytext=(12, -4), textcoords="offset points", color=ps.AMBER)
axes[0].set(title="Average silhouette by k", xlabel="k (number of clusters)", ylabel="mean silhouette")
total_ss = ((X - X.mean(axis=0)) ** 2).sum()
axes[1].plot([1] + ks, [total_ss] + inertia, marker="o", color=ps.ICE, lw=2)
axes[1].set_xticks([1] + ks)
axes[1].set(title="Elbow: within-cluster sum of squares", xlabel="k", ylabel="inertia")
ps.save(fig, M2_IMG / "clu_silhouette_elbow.png")

compare = [2, 3, 4]

fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.6))
for ax, k in zip(axes, compare):
    labels = km_labels[k]
    s = silhouette_samples(X, labels)
    y = 0
    for c in range(k):
        vals = np.sort(s[labels == c])
        ax.fill_betweenx(np.arange(y, y + len(vals)), 0, vals, color=ps.PALETTE[c], alpha=0.9)
        ax.text(-0.08, y + len(vals) / 2, str(c + 1), color=ps.DIM, va="center")
        y += len(vals) + 3
    ax.axvline(s.mean(), color=ps.AMBER, ls="--", lw=1.4)
    ax.set(title=f"k = {k}   (mean {s.mean():.2f})", xlabel="silhouette coefficient", yticks=[], xlim=(-0.2, 0.8))
ps.save(fig, M2_IMG / "clu_silhouette_profiles.png")

# 2d pca just to be able to plot the clusters
pca2 = PCA(n_components=2).fit(X)
P = pca2.transform(X)
ev = pca2.explained_variance_ratio_
team_colors = profiles["constructor_name"].map(ps.TEAM_COLORS)
show_names = ["VER '23", "HAM '21", "ALO '23", "LAT '22", "SAR '23", "STR '22"]

fig, axes = plt.subplots(1, 3, figsize=(16.2, 5.2))
for ax, k in zip(axes, compare):
    labels = km_labels[k]
    for c in range(k):
        pts = P[labels == c]
        hull = pts[ConvexHull(pts).vertices]
        ax.fill(hull[:, 0], hull[:, 1], color=ps.PALETTE[c], alpha=0.13, zorder=1)
        closed = np.vstack([hull, hull[:1]])
        ax.plot(closed[:, 0], closed[:, 1], color=ps.PALETTE[c], lw=1.4, ls="--", zorder=2)
        top = pts[pts[:, 1].argmax()]
        ax.text(top[0], top[1] + 0.42, str(c + 1), color=ps.PALETTE[c], fontsize=12, weight="bold", ha="center",
                va="center", zorder=4, bbox=dict(boxstyle="circle,pad=0.25", fc=ps.BG, ec=ps.PALETTE[c], lw=1.4))
    ax.scatter(P[:, 0], P[:, 1], s=46, c=team_colors, edgecolor="white", lw=0.5, zorder=3)
    for i, name in enumerate(profiles["label"]):
        if name in show_names:
            ax.annotate(name, (P[i, 0], P[i, 1]), xytext=(4, 4), textcoords="offset points", fontsize=7.5, color=ps.DIM, zorder=5)
    ax.set(title=f"k-means, k = {k}", xlabel=f"PC1 ({ev[0]:.0%} of variance)", ylabel=f"PC2 ({ev[1]:.0%})")
    ax.set_ylim(top=P[:, 1].max() + 0.9)
ps.team_legend(axes[-1], loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)
ps.save(fig, M2_IMG / "clu_kmeans_pca.png")


# ---------- hierarchical clustering with cosine distance ----------

D = pdist(X, metric="cosine")
Z = linkage(D, method="average")

# biggest jump in merge height near the top of the tree = where to cut
heights = Z[:, 2]
jumps = np.diff(heights)[-9:][::-1]
hc_k = int(np.argmax(jumps)) + 2
cut = (heights[-hc_k] + heights[-hc_k + 1]) / 2
print("hclust suggests k =", hc_k)

hc_sil = []
for k in ks:
    hc_sil.append(silhouette_score(X, fcluster(Z, k, criterion="maxclust"), metric="cosine"))
print("hclust silhouette:", dict(zip(ks, np.round(hc_sil, 3))))

fig, ax = plt.subplots(figsize=(15, 6.4))
dn = dendrogram(Z, labels=list(profiles["label"]), color_threshold=cut, above_threshold_color=ps.DIM,
                leaf_font_size=7.5, ax=ax)
team_of = dict(zip(profiles["label"], profiles["constructor_name"]))
leaf_x = 5 + 10 * np.arange(len(dn["ivl"]))
leaf_colors = [ps.TEAM_COLORS[team_of[name]] for name in dn["ivl"]]
ax.scatter(leaf_x, [-0.035] * len(leaf_x), c=leaf_colors, s=34, edgecolor="white", lw=0.5, clip_on=False, zorder=5)
ax.set_ylim(bottom=-0.07)
ax.axhline(cut, color=ps.AMBER, ls="--", lw=1.2)
ax.text(ax.get_xlim()[1], cut, f"cut -> {hc_k} clusters", color=ps.AMBER, va="bottom", ha="right")
ax.set(title="Hierarchical clustering of driver-seasons (cosine distance, average linkage)", ylabel="cosine distance")
ax.grid(axis="x", visible=False)
for t in ax.get_xticklabels():
    t.set_color(ps.TEXT)
ps.team_legend(ax, loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
ps.save(fig, M2_IMG / "clu_dendrogram.png")

fig, ax = plt.subplots(figsize=(6.5, 4))
ax.plot(ks, hc_sil, marker="o", color=ps.VIOLET, lw=2, label="hclust (cosine)")
ax.plot(ks, sil, marker="o", color=ps.RED, lw=2, alpha=0.7, label="k-means (euclidean)")
ax.set(title="Silhouette by number of clusters", xlabel="k", ylabel="mean silhouette")
ax.legend()
ps.save(fig, M2_IMG / "clu_hc_vs_km_silhouette.png")


# ---------- compare the two methods ----------

hc_labels = {}
for k in compare:
    hc_labels[k] = order_clusters(fcluster(Z, k, criterion="maxclust") - 1)
    print(f"k={k}  ARI={adjusted_rand_score(km_labels[k], hc_labels[k]):.2f}  hclust sizes={np.bincount(hc_labels[k])}")

fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), gridspec_kw={"width_ratios": [2, 4]})
for ax, k in zip(axes, [2, 4]):
    ct = pd.crosstab(km_labels[k] + 1, hc_labels[k] + 1)
    ax.imshow(ct.values, cmap="Reds", vmin=0)
    for i in range(ct.shape[0]):
        for j in range(ct.shape[1]):
            v = ct.values[i, j]
            ax.text(j, i, v, ha="center", va="center", weight="bold", color="white" if v > ct.values.max() / 2 else "#222")
    ax.set_xticks(range(ct.shape[1]), [f"H{c}" for c in ct.columns])
    ax.set_yticks(range(ct.shape[0]), [f"K{c}" for c in ct.index])
    ari = adjusted_rand_score(km_labels[k], hc_labels[k])
    ax.set(title=f"k = {k}  (ARI {ari:.2f})", xlabel="hclust cluster", ylabel="k-means cluster")
    ax.grid(False)
ps.save(fig, M2_IMG / "clu_crosstab.png")


# ---------- what the k=4 clusters look like ----------

# silhouette likes k=2 best but k=4 is easier to explain in racing terms
for k in compare:
    profiles[f"kmeans_k{k}"] = km_labels[k] + 1
profiles["hclust_k2"] = hc_labels[2] + 1
profiles["hclust_k4"] = hc_labels[4] + 1
cols = ["season", "driver_code", "driver_name", "constructor_name", "label",
        "kmeans_k2", "kmeans_k3", "kmeans_k4", "hclust_k2", "hclust_k4"]
profiles[cols].to_csv(M2_DATA / "clustering_assignments.csv", index=False)

centroids = profiles.groupby("kmeans_k4")[FEATURES].mean()
print(centroids.round(2).T)
z = (centroids - profiles[FEATURES].mean()) / profiles[FEATURES].std()

fig, ax = plt.subplots(figsize=(11, 5.2))
im = ax.imshow(z.values, cmap="RdBu_r", vmin=-2, vmax=2, aspect="auto")
ax.set_xticks(range(len(FEATURES)), [f.replace("_", " ") for f in FEATURES], rotation=30, ha="right")
sizes = profiles["kmeans_k4"].value_counts()
ax.set_yticks(range(4), [f"Cluster {c} (n={sizes[c]})" for c in centroids.index])
for i in range(4):
    for j in range(len(FEATURES)):
        ax.text(j, i, f"{centroids.values[i, j]:.2f}", ha="center", va="center", fontsize=8,
                color="white" if abs(z.values[i, j]) > 1.1 else "black")
ax.set_title("Cluster centroids, k = 4 (colour = z-score, number = raw average)")
ax.grid(False)
fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01)
ps.save(fig, M2_IMG / "clu_centroids.png")

for c in range(1, 5):
    print(c, list(profiles.loc[profiles["kmeans_k4"] == c, "label"]))


# ---------- diagrams for the overview section (made up data) ----------

rng = np.random.default_rng(7)
blobs = np.vstack([rng.normal(c, 0.55, (25, 2)) for c in [(0, 0), (4, 1), (2, 4)]])
toy = KMeans(3, n_init=10, random_state=42).fit(blobs)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
for c in range(3):
    pts = blobs[toy.labels_ == c]
    axes[0].scatter(pts[:, 0], pts[:, 1], s=30, color=ps.PALETTE[c])
axes[0].scatter(toy.cluster_centers_[:, 0], toy.cluster_centers_[:, 1], marker="X", s=200, color="white", edgecolor=ps.BG)
axes[0].set(title="Partitional (k-means)\npick k, assign each point to the nearest centroid", xticks=[], yticks=[])
toy_Z = linkage(blobs[::3], "average")
dendrogram(toy_Z, ax=axes[1], no_labels=True, color_threshold=(toy_Z[-2, 2] + toy_Z[-3, 2]) / 2, above_threshold_color=ps.DIM)
axes[1].set(title="Hierarchical (agglomerative)\nmerge the closest groups into a tree", ylabel="merge distance")
axes[1].grid(axis="x", visible=False)
ps.save(fig, M2_IMG / "clu_concept_partitional_vs_hier.png")

fig, ax = plt.subplots(figsize=(6, 5))
vecs = {"A": (np.array([4.0, 1.0]), ps.RED), "B": (np.array([1.6, 0.5]), ps.ICE), "C": (np.array([1.2, 3.6]), ps.AMBER)}
for name, (v, col) in vecs.items():
    ax.annotate("", v, (0, 0), arrowprops=dict(arrowstyle="-|>", color=col, lw=2.4))
    ax.text(v[0] + 0.12, v[1] + 0.12, name, color=col, weight="bold", fontsize=13)
ax.plot([4.0, 1.6], [1.0, 0.5], ls=":", color=ps.DIM)
ax.text(2.4, 1.15, "euclidean A-B is long", color=ps.DIM, fontsize=9.5)
ax.text(1.9, 0.12, "but the angle A-B is tiny,\nso cosine distance is ~0", color=ps.ICE, fontsize=9.5)
ax.text(1.3, 2.4, "angle A-C is wide:\ncosine distance is large", color=ps.AMBER, fontsize=9.5)
ax.set(xlim=(-0.2, 4.8), ylim=(-0.2, 4.2), title="Euclidean vs cosine distance", xticks=[], yticks=[])
ps.save(fig, M2_IMG / "clu_concept_cosine.png")
