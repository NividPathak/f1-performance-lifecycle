# naive bayes - multinomial + bernoulli on binned pre-race features
# run prep_supervised.py first

import json

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.naive_bayes import BernoulliNB, GaussianNB, MultinomialNB

import plot_style as ps
from paths import CLEANED_CSV, M3_DATA, M3_IMG
from prep_supervised import CLASS_COLORS, CLASSES, PRE_RACE
from sample_format import table_rows

plt = ps.plt

GRID_BINS = [0, 1, 3, 6, 10, 15, 30]
GRID_NAMES = ["P1", "P2-3", "P4-6", "P7-10", "P11-15", "P16+"]
FORM_BINS = [-1, 1, 4, 8, 12, 30]
FORM_NAMES = ["0-1", "1-4", "4-8", "8-12", "12+"]


def to_counts(df):
    parts = {
        "grid": pd.cut(df["grid"], GRID_BINS, labels=GRID_NAMES),
        "team_form": pd.cut(df["team_form"], FORM_BINS, labels=FORM_NAMES),
        "driver_form": pd.cut(df["driver_form"], FORM_BINS, labels=FORM_NAMES),
        "penalty": np.sign(df["grid_penalty"]).map({1: "dropped", 0: "none", -1: "gained"}),
    }
    cols = []
    for name, s in parts.items():
        cats = s.cat.categories if hasattr(s, "cat") else ["dropped", "none", "gained"]
        for c in cats:
            cols.append(pd.Series((s == c).astype(int).values, name=f"{name}_{c}"))
    return pd.concat(cols, axis=1)


def grid_rule(df):
    return np.where(df["grid"] <= 3, "Podium", np.where(df["grid"] <= 10, "Points", "No points"))


train = pd.read_csv(M3_DATA / "train.csv")
test = pd.read_csv(M3_DATA / "test.csv")
X_train = to_counts(train)
X_test = to_counts(test)
y_train = train["result"]
y_test = test["result"]

pd.concat([X_train, y_train], axis=1).to_csv(M3_DATA / "nb_train.csv", index=False)
pd.concat([X_test, y_test], axis=1).to_csv(M3_DATA / "nb_test.csv", index=False)

mnb = MultinomialNB(alpha=1.0).fit(X_train, y_train)
bnb = BernoulliNB(alpha=1.0).fit(X_train, y_train)
gnb = GaussianNB().fit(train[PRE_RACE], y_train)

preds = {
    "Always 'No points'": np.full(len(test), "No points"),
    "Grid-only rule": grid_rule(test),
    "Gaussian NB (raw numbers)": gnb.predict(test[PRE_RACE]),
    "Bernoulli NB": bnb.predict(X_test),
    "Multinomial NB": mnb.predict(X_test),
}
acc = {k: accuracy_score(y_test, p) for k, p in preds.items()}
for k, v in acc.items():
    print(f"{k}: {v:.3f}")
print(classification_report(y_test, preds["Multinomial NB"], labels=CLASSES, digits=3))
print("train acc mnb:", round(mnb.score(X_train, y_train), 3))

results = {"accuracy": {k: round(v, 4) for k, v in acc.items()},
           "mnb_cm": confusion_matrix(y_test, preds["Multinomial NB"], labels=CLASSES).tolist(),
           "bnb_cm": confusion_matrix(y_test, preds["Bernoulli NB"], labels=CLASSES).tolist(),
           "mnb_report": classification_report(y_test, preds["Multinomial NB"], labels=CLASSES, output_dict=True)}
(M3_DATA / "nb_results.json").write_text(json.dumps(results, indent=1))

tables_file = M3_DATA / "sample_tables.json"
tables = json.loads(tables_file.read_text())
tables["nb_train"] = table_rows(pd.concat([X_train, y_train], axis=1).sample(6, random_state=3))
tables["nb_test"] = table_rows(pd.concat([X_test, y_test], axis=1).sample(6, random_state=3))
tables_file.write_text(json.dumps(tables, indent=1))


# accuracy comparison
fig, ax = plt.subplots(figsize=(9, 3.8))
names = list(acc)
cols = ["#4a4a55", "#6b6b75", ps.VIOLET, ps.ICE, ps.RED]
ax.barh(names, [acc[n] for n in names], color=cols)
for i, n in enumerate(names):
    ax.text(acc[n] + 0.008, i, f"{acc[n]:.1%}", va="center", fontsize=10)
ax.set_xlim(0, 0.85)
ax.set_xlabel("accuracy on the 2023 test set")
ax.set_title("Naive Bayes vs two simple baselines", loc="left")
ax.grid(axis="y", visible=False)
ps.save(fig, M3_IMG / "nb_accuracy.png")


def draw_cm(ax, cm, title):
    rec = cm / cm.sum(axis=1, keepdims=True)
    ax.imshow(rec, cmap="magma", vmin=0, vmax=1)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{cm[i, j]}\n{rec[i, j]:.0%}", ha="center", va="center", fontsize=10,
                    color="black" if rec[i, j] > 0.55 else "white")
    ax.set_xticks(range(3), CLASSES)
    ax.set_yticks(range(3), CLASSES)
    ax.set_xlabel("predicted")
    ax.set_ylabel("actual")
    ax.set_title(title, loc="left", fontsize=12)
    ax.grid(False)


fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
draw_cm(axes[0], np.array(results["mnb_cm"]), f"Multinomial NB  ({acc['Multinomial NB']:.1%})")
draw_cm(axes[1], np.array(results["bnb_cm"]), f"Bernoulli NB  ({acc['Bernoulli NB']:.1%})")
fig.tight_layout()
ps.save(fig, M3_IMG / "nb_confusion.png")


# P(bin | class) for each feature group
probs = pd.DataFrame(np.exp(mnb.feature_log_prob_), index=mnb.classes_, columns=X_train.columns).loc[CLASSES]
groups = ["grid", "team_form", "driver_form", "penalty"]
fig, axes = plt.subplots(1, 4, figsize=(14, 3.4), gridspec_kw={"width_ratios": [6, 5, 5, 3]})
for ax, g in zip(axes, groups):
    sub = probs[[c for c in probs.columns if c.startswith(g + "_")]]
    sub = sub.div(sub.sum(axis=1), axis=0)
    ax.imshow(sub.values, cmap="magma", vmin=0, vmax=0.8, aspect="auto")
    for i in range(sub.shape[0]):
        for j in range(sub.shape[1]):
            v = sub.values[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=9, color="black" if v > 0.45 else "white")
    ax.set_xticks(range(sub.shape[1]), [c.split("_")[-1] for c in sub.columns], fontsize=9)
    ax.set_yticks(range(3), CLASSES if g == "grid" else [""] * 3)
    ax.set_title(g.replace("_", " "), loc="left", fontsize=11)
    ax.grid(False)
fig.suptitle("What the model learned: P(bin | class) from the 2021-22 training data", x=0.01, ha="left",
             fontsize=13, fontweight="bold")
fig.tight_layout()
ps.save(fig, M3_IMG / "nb_likelihoods.png")


# race preview: singapore 2023, the one race red bull didnt win that year
race = test[(test["round"] == 15)].copy()
race_X = X_test.loc[race.index]
p = pd.DataFrame(mnb.predict_proba(race_X), columns=mnb.classes_, index=race.index)
race["p_podium"] = p["Podium"]
race["p_points"] = p["Points"]
race = race.sort_values("grid")
print(race[["driver_code", "constructor_name", "grid", "result", "p_podium", "p_points"]].round(2).to_string())

fig, ax = plt.subplots(figsize=(12, 4.6))
x = np.arange(len(race))
team_cols = [ps.TEAM_COLORS[t] for t in race["constructor_name"]]
ax.bar(x, race["p_podium"] + race["p_points"], color=team_cols, alpha=0.35, label="P(points or podium)")
ax.bar(x, race["p_podium"], color=team_cols, label="P(podium)")
for i, r in enumerate(race.itertuples()):
    mark = {"Podium": "P", "Points": "pts", "No points": ""}[r.result]
    if mark:
        ax.text(i, r.p_podium + r.p_points + 0.03, mark, ha="center", color=CLASS_COLORS[r.result], fontsize=10,
                fontweight="bold")
ax.set_xticks(x, [f"{d}\nP{g}" for d, g in zip(race["driver_code"], race["grid"])], fontsize=8.5)
ax.set_ylim(0, 1.12)
ax.set_ylabel("predicted probability")
ax.set_title("2023 Singapore GP, predicted before lights out (drivers in grid order)", loc="left")
ax.grid(axis="x", visible=False)
ps.team_legend(ax, loc="upper left", bbox_to_anchor=(1.01, 1), frameon=False)
ps.save(fig, M3_IMG / "nb_race_preview.png")


# overview figures
grid_bin = pd.cut(train["grid"], GRID_BINS, labels=GRID_NAMES)
prior = y_train.value_counts(normalize=True).loc[CLASSES]
like = pd.Series({c: (grid_bin[y_train == c] == "P2-3").mean() for c in CLASSES})
post = prior * like / (prior * like).sum()
print("prior", prior.round(3).to_dict(), "likelihood", like.round(3).to_dict(), "posterior", post.round(3).to_dict())

fig, axes = plt.subplots(1, 3, figsize=(12, 3.6), sharey=True)
for ax, vals, title in zip(axes, [prior, like, post],
                           ["Prior  P(class)", "Likelihood  P(start P2-3 | class)", "Posterior  P(class | start P2-3)"]):
    ax.bar(CLASSES, vals, color=[CLASS_COLORS[c] for c in CLASSES])
    for i, v in enumerate(vals):
        ax.text(i, v + 0.02, f"{v:.2f}", ha="center", fontsize=10)
    ax.set_title(title, loc="left", fontsize=11.5)
    ax.set_ylim(0, 1)
    ax.grid(axis="x", visible=False)
axes[0].text(2.75, 0.5, "×", fontsize=26, ha="center", color=ps.DIM, clip_on=False)
axes[1].text(2.75, 0.5, "∝", fontsize=26, ha="center", color=ps.DIM, clip_on=False)
fig.tight_layout(w_pad=3)
ps.save(fig, M3_IMG / "nb_concept_bayes.png")

words = ["box", "tyres", "gone", "lap", "rain", "push"]
counts = [3, 1, 1, 1, 0, 0]
fig, axes = plt.subplots(1, 2, figsize=(11, 3.4), sharey=True)
for ax, vals, title, col in zip(axes, [counts, [min(c, 1) for c in counts]],
                                ["Multinomial: how many times", "Bernoulli: there or not"], [ps.RED, ps.ICE]):
    ax.barh(words[::-1], vals[::-1], color=col)
    for i, v in enumerate(vals[::-1]):
        ax.text(v + 0.05, i, str(v), va="center", fontsize=10)
    ax.set_xlim(0, 3.6)
    ax.set_xticks([0, 1, 2, 3])
    ax.set_title(title, loc="left", fontsize=12)
    ax.grid(axis="y", visible=False)
fig.suptitle('Team radio: "Box box, box this lap, tyres are gone"', x=0.01, ha="left", fontsize=13, fontweight="bold")
fig.tight_layout()
ps.save(fig, M3_IMG / "nb_concept_mn_vs_bern.png")


# how far off are the misses
order = {c: i for i, c in enumerate(CLASSES)}
gap = np.abs(y_test.map(order).values - pd.Series(preds["Multinomial NB"]).map(order).values)
results["within_one"] = {"Multinomial NB": round((gap <= 1).mean(), 4),
                         "Bernoulli NB": round((np.abs(y_test.map(order).values - pd.Series(preds["Bernoulli NB"]).map(order).values) <= 1).mean(), 4)}
print("within one class:", results["within_one"])

clean = pd.read_csv(CLEANED_CSV)[["season", "round", "driver_code", "did_not_finish", "final_position_num"]]
info = test.merge(clean, on=["season", "round", "driver_code"], how="left")
wrong = preds["Multinomial NB"] != y_test.values
dnf = wrong & info["did_not_finish"].values
edge = wrong & ~info["did_not_finish"].values & info["final_position_num"].isin([3, 4, 10, 11]).values
other = wrong & ~dnf & ~edge
results["errors"] = {"total": int(wrong.sum()), "dnf": int(dnf.sum()), "boundary": int(edge.sum()), "other": int(other.sum())}
print("errors:", results["errors"])

fig, ax = plt.subplots(figsize=(10, 2.6))
parts = [("Retired (can't be seen pre-race)", dnf.sum(), "#6b6b75"),
         ("Finished P3/P4 or P10/P11 (one place off)", edge.sum(), ps.AMBER),
         ("Everything else", other.sum(), ps.RED)]
left = 0
for label, n, col in parts:
    ax.barh([0], [n], left=left, color=col)
    ax.text(left + n / 2, 0, str(n), ha="center", va="center", color="black", fontsize=11, fontweight="bold")
    left += n
handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in parts]
ax.legend(handles, [p[0] for p in parts], ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.15), frameon=False, fontsize=9)
ax.set_xlim(0, left)
ax.set_yticks([])
ax.set_xticks([])
ax.grid(False)
ax.set_title(f"The {wrong.sum()} wrong calls by multinomial NB, broken down", loc="left")
ps.save(fig, M3_IMG / "nb_error_breakdown.png")


# two class version: top 10 or not
two = lambda y: np.where(y == "No points", "No points", "Points")
y2_train = two(y_train)
y2_test = two(y_test)
mnb2 = MultinomialNB(alpha=1.0).fit(X_train, y2_train)
bnb2 = BernoulliNB(alpha=1.0).fit(X_train, y2_train)
grid2 = np.where(test["grid"] <= 10, "Points", "No points")
results["two_class"] = {"Multinomial NB": round(mnb2.score(X_test, y2_test), 4),
                        "Bernoulli NB": round(bnb2.score(X_test, y2_test), 4),
                        "Grid-only rule": round((grid2 == y2_test).mean(), 4),
                        "Always 'No points'": round((y2_test == "No points").mean(), 4),
                        "mnb_cm": confusion_matrix(y2_test, mnb2.predict(X_test), labels=["Points", "No points"]).tolist()}
print("two class:", results["two_class"])
(M3_DATA / "nb_results.json").write_text(json.dumps(results, indent=1))

fig, axes = plt.subplots(1, 2, figsize=(12, 4), gridspec_kw={"width_ratios": [1.3, 1]})
ax = axes[0]
names = ["Always 'No points'", "Grid-only rule", "Bernoulli NB", "Multinomial NB"]
vals = [results["two_class"][n] for n in names]
ax.barh(names, vals, color=["#4a4a55", "#6b6b75", ps.ICE, ps.RED])
for i, v in enumerate(vals):
    ax.text(v + 0.01, i, f"{v:.1%}", va="center", fontsize=10)
ax.set_xlim(0, 1)
ax.set_xlabel("accuracy on 2023")
ax.grid(axis="y", visible=False)
ax.set_title("Two classes: will they score points?", loc="left", fontsize=12)
ax = axes[1]
cm = np.array(results["two_class"]["mnb_cm"])
rec = cm / cm.sum(axis=1, keepdims=True)
ax.imshow(rec, cmap="magma", vmin=0, vmax=1)
for i in range(2):
    for j in range(2):
        ax.text(j, i, f"{cm[i, j]}\n{rec[i, j]:.0%}", ha="center", va="center", fontsize=11,
                color="black" if rec[i, j] > 0.55 else "white")
ax.set_xticks([0, 1], ["Points", "No points"])
ax.set_yticks([0, 1], ["Points", "No points"])
ax.set_xlabel("predicted")
ax.set_ylabel("actual")
ax.set_title("Multinomial NB, 2 classes", loc="left", fontsize=12)
ax.grid(False)
fig.tight_layout()
ps.save(fig, M3_IMG / "nb_two_class.png")
