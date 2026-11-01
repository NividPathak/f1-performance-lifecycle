# does adding more pre-race features help? (short answer: no)
# run prep_supervised.py first

import json

import pandas as pd
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier

from paths import CLEANED_CSV, M3_DATA
from prep_supervised import PRE_RACE


def past_mean(s, n):
    return s.shift(1).rolling(n, min_periods=1).mean()


c = pd.read_csv(CLEANED_CSV).sort_values(["season", "round", "final_position_num"])
c["race_idx"] = c.groupby(["season", "round"]).ngroup()
c["pos"] = c["final_position_num"].where(~c["did_not_finish"], 20)
c["gain"] = (c["grid"] - c["final_position_num"]).where(~c["did_not_finish"])

team = c.groupby(["race_idx", "constructor_name"]).agg(tpos=("pos", "mean"), tdnf=("did_not_finish", "mean")).reset_index()
team["team_pos_form"] = team.groupby("constructor_name")["tpos"].transform(lambda s: past_mean(s, 5))
team["team_dnf_rate"] = team.groupby("constructor_name")["tdnf"].transform(lambda s: past_mean(s, 10))
c = c.merge(team[["race_idx", "constructor_name", "team_pos_form", "team_dnf_rate"]], on=["race_idx", "constructor_name"])

c["driver_pos_form"] = c.groupby("driver_id")["pos"].transform(lambda s: past_mean(s, 5))
c["driver_gain_form"] = c.groupby("driver_id")["gain"].transform(lambda s: s.shift(1).rolling(10, min_periods=1).mean())
q = c["quali_position"].fillna(c["grid"])
c["teammate_gap"] = q - (q.groupby([c["race_idx"], c["constructor_name"]]).transform("sum") - q)

# how much the order shuffles at a circuit, only using earlier seasons
c["abs_change"] = (c["grid"] - c["final_position_num"]).abs().where(~c["did_not_finish"])
circ = c.groupby(["circuit_id", "season"])["abs_change"].mean().rename("m").reset_index().sort_values("season")
circ["circuit_shuffle"] = circ.groupby("circuit_id")["m"].transform(lambda s: s.shift(1).expanding().mean())
c = c.merge(circ[["circuit_id", "season", "circuit_shuffle"]], on=["circuit_id", "season"])
c["circuit_shuffle"] = c["circuit_shuffle"].fillna(c.loc[c["season"] == 2021, "abs_change"].mean())

NEW = ["team_pos_form", "team_dnf_rate", "driver_pos_form", "driver_gain_form", "teammate_gap", "circuit_shuffle"]
d = pd.read_csv(M3_DATA / "labeled_data.csv").merge(c[["season", "round", "driver_code"] + NEW],
                                                    on=["season", "round", "driver_code"])
d["driver_pos_form"] = d["driver_pos_form"].fillna(d["team_pos_form"])
d["driver_gain_form"] = d["driver_gain_form"].fillna(0)

train = d[d["season"] < 2023]
test = d[d["season"] == 2023]
races = train["season"].astype(str) + "-" + train["round"].astype(str)

out = {}
models = {"tree depth 3": lambda: DecisionTreeClassifier(max_depth=3, min_samples_leaf=20, random_state=0),
          "tree depth 5": lambda: DecisionTreeClassifier(max_depth=5, min_samples_leaf=20, random_state=0),
          "gaussian NB": lambda: GaussianNB()}
for name, make in models.items():
    for label, cols in [("original 5", PRE_RACE), ("original + 6 new", PRE_RACE + NEW)]:
        m = make()
        cv = cross_val_score(m, train[cols], train["result"], groups=races, cv=GroupKFold(5)).mean()
        acc = m.fit(train[cols], train["result"]).score(test[cols], test["result"])
        out[f"{name}, {label}"] = {"cv": round(cv, 4), "test": round(acc, 4)}
        print(f"{name}, {label}: cv {cv:.3f}  test {acc:.3f}")
(M3_DATA / "extra_features_results.json").write_text(json.dumps(out, indent=1))
