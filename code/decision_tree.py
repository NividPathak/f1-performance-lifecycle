# decision trees - 3 trees on the same train/test split as naive bayes
# run prep_supervised.py first

import json

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier, plot_tree

import plot_style as ps
from paths import M3_DATA, M3_IMG
from prep_supervised import CLASS_COLORS, CLASSES, FEATURES, PRE_RACE

plt = ps.plt

train = pd.read_csv(M3_DATA / "train.csv")
test = pd.read_csv(M3_DATA / "test.csv")
y_train = train["result"]
y_test = test["result"]
races = train["season"].astype(str) + "-" + train["round"].astype(str)
cv = GroupKFold(n_splits=5)


def entropy(counts):
    p = np.array(counts) / sum(counts)
    p = p[p > 0]
    return -(p * np.log2(p)).sum()


def gini(counts):
    p = np.array(counts) / sum(counts)
    return 1 - (p ** 2).sum()


# worked example: 2022 bahrain, split on grid <= 10
ex = train[(train["season"] == 2022) & (train["round"] == 1)]
parent = [int((ex["result"] == c).sum()) for c in CLASSES]
left = [int(((ex["grid"] <= 10) & (ex["result"] == c)).sum()) for c in CLASSES]
right = [p - l for p, l in zip(parent, left)]
example = {"parent": parent, "left": left, "right": right}
for name, f in [("entropy", entropy), ("gini", gini)]:
    w = (sum(left) * f(left) + sum(right) * f(right)) / sum(parent)
    example[name] = {"parent": round(f(parent), 4), "left": round(f(left), 4), "right": round(f(right), 4),
                     "weighted": round(w, 4), "gain": round(f(parent) - w, 4)}
alt = [int(((ex["grid"] <= 3) & (ex["result"] == c)).sum()) for c in CLASSES]
alt_r = [p - a for p, a in zip(parent, alt)]
example["alt_grid3"] = {"left": alt, "right": alt_r,
                        "gain": round(entropy(parent) - (sum(alt) * entropy(alt) + sum(alt_r) * entropy(alt_r)) / 20, 4)}
print(json.dumps(example, indent=1))


trees = {
    "A": dict(cols=PRE_RACE, model=DecisionTreeClassifier(criterion="gini", max_depth=3, random_state=0)),
    "B": dict(cols=FEATURES, model=DecisionTreeClassifier(criterion="entropy", max_depth=3, random_state=0)),
}

# tree C: let cross validation pick the pruning strength (folds split by race)
path = DecisionTreeClassifier(random_state=0).cost_complexity_pruning_path(train[FEATURES], y_train)
best = (0, None, None)
for crit in ["gini", "entropy"]:
    for a in np.unique(path.ccp_alphas.round(5)):
        m = DecisionTreeClassifier(criterion=crit, ccp_alpha=a, random_state=0)
        s = cross_val_score(m, train[FEATURES], y_train, groups=races, cv=cv).mean()
        if s > best[0]:
            best = (s, crit, a)
print("best cv:", best)
trees["C"] = dict(cols=FEATURES, model=DecisionTreeClassifier(criterion=best[1], ccp_alpha=best[2], random_state=0))

results = {"example": example, "trees": {}}
for name, t in trees.items():
    m = t["model"].fit(train[t["cols"]], y_train)
    pred = m.predict(test[t["cols"]])
    t["pred"] = pred
    results["trees"][name] = {
        "criterion": m.criterion, "depth": int(m.get_depth()), "leaves": int(m.get_n_leaves()),
        "ccp_alpha": float(m.ccp_alpha), "features": t["cols"],
        "train_acc": round(m.score(train[t["cols"]], y_train), 4),
        "test_acc": round(accuracy_score(y_test, pred), 4),
        "cm": confusion_matrix(y_test, pred, labels=CLASSES).tolist(),
        "importance": dict(zip(t["cols"], m.feature_importances_.round(4))),
    }
    print(name, {k: v for k, v in results["trees"][name].items() if k not in ("cm", "features")})
results["cv_best"] = {"score": round(best[0], 4), "criterion": best[1], "alpha": float(best[2])}

full = DecisionTreeClassifier(random_state=0).fit(train[FEATURES], y_train)
results["full_tree"] = {"leaves": int(full.get_n_leaves()), "depth": int(full.get_depth()),
                        "train_acc": round(full.score(train[FEATURES], y_train), 4),
                        "test_acc": round(full.score(test[FEATURES], y_test), 4)}
print("full tree:", results["full_tree"])
(M3_DATA / "dt_results.json").write_text(json.dumps(results, indent=1, default=float))


NICE = {"grid": "grid", "quali_position": "quali", "grid_penalty": "grid penalty", "team_form": "team form",
        "driver_form": "driver form", "num_pitstops": "pit stops", "first_stop_pct": "first stop %",
        "avg_pit_lane_s": "pit lane s"}


def draw_tree(model, cols, path, title, size):
    fig, ax = plt.subplots(figsize=size)
    arts = plot_tree(model, feature_names=[NICE[c] for c in cols], class_names=list(model.classes_),
                     impurity=True, rounded=True, fontsize=9, ax=ax, precision=2)
    for a in arts:
        txt = a.get_text()
        cls = txt.split("class = ")[-1].strip()
        if a.get_bbox_patch() is not None:
            a.get_bbox_patch().set_facecolor(CLASS_COLORS.get(cls, ps.PANEL))
            a.get_bbox_patch().set_edgecolor(ps.BG)
            a.set_color("black")
        if a.arrow_patch is not None:
            a.arrow_patch.set_color(ps.DIM)
    ax.set_title(title, loc="left")
    handles = [plt.Rectangle((0, 0), 1, 1, color=CLASS_COLORS[c]) for c in CLASSES]
    ax.legend(handles, CLASSES, loc="upper right", frameon=False, title="majority class")
    ps.save(fig, path)


labels = {
    "A": "Tree A: Gini, max depth 3, pre-race features only",
    "B": "Tree B: Entropy, max depth 3, pre-race + strategy features",
    "C": f"Tree C: {best[1].capitalize()}, pruned with ccp_alpha = {best[2]:.4f} (picked by 5-fold CV)",
}
draw_tree(trees["A"]["model"], trees["A"]["cols"], M3_IMG / "dt_tree_a.png", labels["A"], (17, 7))
draw_tree(trees["B"]["model"], trees["B"]["cols"], M3_IMG / "dt_tree_b.png", labels["B"], (17, 7))
draw_tree(trees["C"]["model"], trees["C"]["cols"], M3_IMG / "dt_tree_c.png", labels["C"], (13, 6))

fig, ax = plt.subplots(figsize=(18, 6))
arts = plot_tree(full, ax=ax, fontsize=1, impurity=False, label="none")
for a in arts:
    if a.get_bbox_patch() is not None:
        a.get_bbox_patch().set_facecolor(ps.RED)
        a.get_bbox_patch().set_edgecolor("none")
        a.set_color(ps.RED)
    if a.arrow_patch is not None:
        a.arrow_patch.set_color(ps.DIM)
        a.arrow_patch.set_linewidth(0.4)
ax.set_title(f"No limits: {full.get_n_leaves()} leaves, depth {full.get_depth()}, 100% on training data, "
             f"{results['full_tree']['test_acc']:.1%} on 2023", loc="left")
ps.save(fig, M3_IMG / "dt_tree_full.png")


fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
for ax, name in zip(axes, "ABC"):
    cm = np.array(results["trees"][name]["cm"])
    rec = cm / cm.sum(axis=1, keepdims=True)
    ax.imshow(rec, cmap="magma", vmin=0, vmax=1)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{cm[i, j]}\n{rec[i, j]:.0%}", ha="center", va="center", fontsize=10,
                    color="black" if rec[i, j] > 0.55 else "white")
    ax.set_xticks(range(3), CLASSES)
    ax.set_yticks(range(3), CLASSES)
    ax.set_xlabel("predicted")
    ax.set_ylabel("actual" if name == "A" else "")
    ax.set_title(f"Tree {name}  ({results['trees'][name]['test_acc']:.1%})", loc="left", fontsize=12)
    ax.grid(False)
fig.tight_layout()
ps.save(fig, M3_IMG / "dt_confusion.png")


# depth vs accuracy, to show overfitting
depths = list(range(1, 16))
rows = []
for d in depths:
    m = DecisionTreeClassifier(max_depth=d, random_state=0)
    cvs = cross_val_score(m, train[FEATURES], y_train, groups=races, cv=cv).mean()
    m.fit(train[FEATURES], y_train)
    rows.append((d, m.score(train[FEATURES], y_train), cvs, m.score(test[FEATURES], y_test)))
curve = pd.DataFrame(rows, columns=["depth", "train", "cv", "test"])
print(curve.round(3).to_string(index=False))
fig, ax = plt.subplots(figsize=(10, 4.2))
ax.plot(curve["depth"], curve["train"], marker="o", color=ps.DIM, label="training accuracy")
ax.plot(curve["depth"], curve["cv"], marker="o", color=ps.ICE, label="5-fold CV accuracy (on 2021-22)")
ax.plot(curve["depth"], curve["test"], marker="o", color=ps.RED, label="test accuracy (2023)")
ax.set_xlabel("max depth")
ax.set_ylabel("accuracy")
ax.set_xticks(depths)
ax.legend(frameon=False)
ax.set_title("Deeper trees memorise 2021-22 and get worse at 2023", loc="left")
ps.save(fig, M3_IMG / "dt_depth_curve.png")


fig, ax = plt.subplots(figsize=(10, 4.4))
w = 0.27
for i, (name, col) in enumerate(zip("ABC", [ps.ICE, ps.VIOLET, ps.RED])):
    imp = [results["trees"][name]["importance"].get(f, 0) for f in FEATURES]
    ax.barh(np.arange(len(FEATURES)) + (i - 1) * w, imp, height=w, color=col, label=f"Tree {name}")
ax.set_yticks(range(len(FEATURES)), [NICE[f] for f in FEATURES])
ax.invert_yaxis()
ax.set_xlabel("feature importance (share of total impurity decrease)")
ax.legend(frameon=False)
ax.grid(axis="y", visible=False)
ax.set_title("What each tree actually splits on", loc="left")
ps.save(fig, M3_IMG / "dt_importance.png")


nb = json.loads((M3_DATA / "nb_results.json").read_text())["accuracy"]
board = {"Always 'No points'": nb["Always 'No points'"], "Grid-only rule": nb["Grid-only rule"],
         "Multinomial NB": nb["Multinomial NB"], "Bernoulli NB": nb["Bernoulli NB"],
         "Fully grown tree": results["full_tree"]["test_acc"]}
for n in "ABC":
    board[f"Tree {n}"] = results["trees"][n]["test_acc"]
board = dict(sorted(board.items(), key=lambda kv: kv[1]))
fig, ax = plt.subplots(figsize=(9, 4.4))
cols = [ps.RED if k.startswith("Tree") else ps.ICE if "NB" in k else "#5a5a64" for k in board]
ax.barh(list(board), list(board.values()), color=cols)
for i, v in enumerate(board.values()):
    ax.text(v + 0.006, i, f"{v:.1%}", va="center", fontsize=10)
ax.set_xlim(0, 0.85)
ax.set_xlabel("accuracy on the 2023 test set")
ax.grid(axis="y", visible=False)
ax.set_title("Every model so far, same test set", loc="left")
ps.save(fig, M3_IMG / "dt_scoreboard.png")


# overview figures
p = np.linspace(0.001, 0.999, 200)
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(p, -(p * np.log2(p) + (1 - p) * np.log2(1 - p)), color=ps.RED, lw=2.4, label="entropy")
ax.plot(p, 1 - p ** 2 - (1 - p) ** 2, color=ps.ICE, lw=2.4, label="Gini")
ax.plot(p, 1 - np.maximum(p, 1 - p), color=ps.DIM, lw=1.6, ls="--", label="misclassification")
ax.set_xlabel("share of the node that is class 1")
ax.set_ylabel("impurity")
ax.legend(frameon=False)
ax.set_title("Impurity peaks when a node is a 50/50 mix", loc="left")
ps.save(fig, M3_IMG / "dt_concept_impurity.png")

small = DecisionTreeClassifier(max_depth=2, random_state=0).fit(train[["grid", "team_form"]], y_train)
fig, axes = plt.subplots(1, 2, figsize=(16, 5.2), gridspec_kw={"width_ratios": [1, 1.15]})
ax = axes[0]
gx, gy = np.meshgrid(np.linspace(0, 21.5, 300), np.linspace(-0.5, 22, 300))
zz = small.predict(pd.DataFrame({"grid": gx.ravel(), "team_form": gy.ravel()})).reshape(gx.shape)
num = np.vectorize({c: i for i, c in enumerate(CLASSES)}.get)(zz)
from matplotlib.colors import ListedColormap
ax.contourf(gx, gy, num, levels=[-0.5, 0.5, 1.5, 2.5], cmap=ListedColormap([CLASS_COLORS[c] for c in CLASSES]), alpha=0.22)
rng = np.random.default_rng(0)
for c in CLASSES:
    s = train[y_train == c]
    ax.scatter(s["grid"] + rng.uniform(-0.3, 0.3, len(s)), s["team_form"], s=12, color=CLASS_COLORS[c], label=c,
               edgecolor="none", alpha=0.85)
ax.set_xlabel("grid position")
ax.set_ylabel("team form (points per car, last 5 races)")
ax.legend(frameon=False, loc="upper right")
ax.set_title("Each split is a straight cut, so the regions are boxes", loc="left", fontsize=12)
ax.grid(False)
draw_ax = axes[1]
arts = plot_tree(small, feature_names=["grid", "team form"], class_names=list(small.classes_), impurity=False,
                 rounded=True, fontsize=9, ax=draw_ax)
for a in arts:
    cls = a.get_text().split("class = ")[-1].strip()
    if a.get_bbox_patch() is not None:
        a.get_bbox_patch().set_facecolor(CLASS_COLORS.get(cls, ps.PANEL))
        a.set_color("black")
    if a.arrow_patch is not None:
        a.arrow_patch.set_color(ps.DIM)
draw_ax.set_title("The same depth-2 tree", loc="left", fontsize=12)
fig.tight_layout()
ps.save(fig, M3_IMG / "dt_concept_partition.png")
