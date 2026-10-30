# labeled data + train/test split for naive bayes and decision trees
# label = race result (Podium / Points / No points), train = 2021-2022, test = 2023

import json

import numpy as np
import pandas as pd

import plot_style as ps
from paths import CLEANED_CSV, M3_DATA, M3_IMG
from sample_format import table_rows

plt = ps.plt
M3_DATA.mkdir(parents=True, exist_ok=True)

CLASSES = ["Podium", "Points", "No points"]
CLASS_COLORS = {"Podium": ps.AMBER, "Points": ps.ICE, "No points": "#6b6b75"}
IDS = ["season", "round", "race_name", "driver_code", "constructor_name"]
PRE_RACE = ["grid", "quali_position", "grid_penalty", "team_form", "driver_form"]
STRATEGY = ["num_pitstops", "first_stop_pct", "avg_pit_lane_s"]
FEATURES = PRE_RACE + STRATEGY


if __name__ == "__main__":
    df = pd.read_csv(CLEANED_CSV).sort_values(["season", "round", "final_position_num"]).reset_index(drop=True)

    finished = ~df["did_not_finish"]
    df["result"] = "No points"
    df.loc[finished & (df["final_position_num"] <= 10), "result"] = "Points"
    df.loc[finished & (df["final_position_num"] <= 3), "result"] = "Podium"

    # form = avg points per car over the previous 5 races, shift(1) so the race itself isnt included
    df["race_idx"] = df.groupby(["season", "round"]).ngroup()
    team = df.groupby(["race_idx", "constructor_name"])["points"].mean().rename("team_pts").reset_index()
    team["team_form"] = team.groupby("constructor_name")["team_pts"].transform(
        lambda s: s.shift(1).rolling(5, min_periods=1).mean())
    df = df.merge(team[["race_idx", "constructor_name", "team_form"]], on=["race_idx", "constructor_name"])
    df["driver_form"] = df.groupby("driver_id")["points"].transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())

    # 2021 round 1 has no previous races to look at so it gets dropped
    df = df[df["team_form"].notna()].copy()
    # a driver's first race: use what the car has been scoring
    df["driver_form"] = df["driver_form"].fillna(df["team_form"])

    df["quali_position"] = df["quali_position"].fillna(df["grid"])
    df["grid_penalty"] = df["grid"] - df["quali_position"]
    df["race_laps"] = df.groupby(["season", "round"])["laps_completed"].transform("max")
    # no stop = never stopped before the end, so 1.0, and no pit lane time
    df["first_stop_pct"] = (df["first_pitstop_lap"] / df["race_laps"]).fillna(1.0)
    df["avg_pit_lane_s"] = df["avg_pitstop_duration_s"].fillna(0)

    df = df[IDS + FEATURES + ["result"]].round(3).reset_index(drop=True)
    df.to_csv(M3_DATA / "labeled_data.csv", index=False)

    train = df[df["season"] < 2023]
    test = df[df["season"] == 2023]
    print("labeled rows:", len(df), "train:", len(train), "test:", len(test))
    print(pd.crosstab(df["season"] < 2023, df["result"]))

    shared = set(zip(train["season"], train["round"], train["driver_code"])) & set(zip(test["season"], test["round"], test["driver_code"]))
    print("rows in both sets:", len(shared))

    train.to_csv(M3_DATA / "train.csv", index=False)
    test.to_csv(M3_DATA / "test.csv", index=False)


    fig, axes = plt.subplots(1, 2, figsize=(13, 3.6), gridspec_kw={"width_ratios": [2.2, 1]})
    ax = axes[0]
    races = df.groupby(["season", "round"]).size().reset_index()
    for i, r in races.iterrows():
        col = ps.ICE if r["season"] < 2023 else ps.AMBER
        ax.add_patch(plt.Rectangle((i, 0), 0.7, 1, facecolor=col, edgecolor="none"))
    for s, x in [(2021, 0), (2022, 21), (2023, 43)]:
        ax.text(x, 1.15, str(s), color=ps.TEXT, fontsize=10, fontweight="bold")
    ax.text(len(races) * 0.33, -0.45, f"TRAINING SET  {len(train)} driver-races (43 races)", ha="center", color=ps.ICE, fontsize=10.5)
    ax.text(len(races) * 0.83, -0.45, f"TEST SET  {len(test)} (22 races)", ha="center", color=ps.AMBER, fontsize=10.5)
    ax.set_xlim(-0.5, len(races))
    ax.set_ylim(-0.8, 1.5)
    ax.axis("off")
    ax.set_title("Split by season: learn from 2021-22, predict 2023", loc="left")

    ax = axes[1]
    shares = pd.DataFrame({"train": train["result"].value_counts(normalize=True),
                           "test": test["result"].value_counts(normalize=True)}).loc[CLASSES]
    left = np.zeros(2)
    for c in CLASSES:
        ax.barh(["test", "train"], shares.loc[c, ["test", "train"]], left=left, color=CLASS_COLORS[c], label=c)
        for y, v, l in zip([0, 1], shares.loc[c, ["test", "train"]], left):
            ax.text(l + v / 2, y, f"{v:.0%}", ha="center", va="center", color="black", fontsize=9)
        left += shares.loc[c, ["test", "train"]].values
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.grid(False)
    ax.legend(ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.25), frameon=False, fontsize=9)
    ax.set_title("Class mix in each set", loc="left")
    ps.save(fig, M3_IMG / "split_overview.png")


    tables_file = M3_DATA / "sample_tables.json"
    tables = json.loads(tables_file.read_text()) if tables_file.exists() else {}
    show = ["season", "round", "driver_code", "constructor_name"] + FEATURES + ["result"]
    sample = df[(df["season"] == 2022) & (df["round"] == 1)].head(8)
    tables["nb_labeled"] = table_rows(sample[show])
    tables["dt_labeled"] = table_rows(sample[show])
    tables["dt_train"] = table_rows(train[FEATURES + ["result"]].sample(6, random_state=3))
    tables["dt_test"] = table_rows(test[FEATURES + ["result"]].sample(6, random_state=3))
    tables_file.write_text(json.dumps(tables, indent=1))
