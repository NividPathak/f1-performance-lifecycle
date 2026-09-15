"""Precompute all aggregates needed for the 12 interactive Chart.js
visualizations, split by season where useful so the site's season filter can
re-render client-side without recomputing from the full row-level CSV.
"""
import json
import numpy as np
import pandas as pd

df = pd.read_csv("cleaned/f1_driver_race_cleaned.csv")

GRID_ZONES = ["Pole (P1)", "Front row (P2-P3)", "Top 5 (P4-P5)", "Midfield (P6-P10)", "Back (P11+)"]

out = {"seasons": [2021, 2022, 2023]}


def by_season(frame, builder):
    """Return {'all': builder(frame), '2021': builder(...), ...}"""
    result = {"all": builder(frame)}
    for s in [2021, 2022, 2023]:
        result[str(s)] = builder(frame[frame["season"] == s])
    return result


# 1. grid vs final position scatter (finishers only), sampled points
def scatter_grid_final(frame):
    f = frame[~frame["did_not_finish"]]
    pts = f[["grid", "final_position_num"]].dropna()
    return [{"x": int(r.grid), "y": int(r.final_position_num)} for r in pts.itertuples()]


out["grid_vs_final"] = by_season(df, scatter_grid_final)

# 2. avg final position by grid zone
def avg_by_grid_zone(frame):
    f = frame[~frame["did_not_finish"]]
    g = f.groupby("grid_zone", observed=True)["final_position_num"].mean()
    return {"labels": GRID_ZONES, "values": [round(float(g.get(z, np.nan)), 2) for z in GRID_ZONES]}


out["avg_position_by_grid_zone"] = by_season(df, avg_by_grid_zone)

# 3. avg points by constructor
def avg_points_by_constructor(frame):
    g = frame.groupby("constructor_name")["points"].mean().sort_values(ascending=False)
    return {"labels": list(g.index), "values": [round(float(v), 2) for v in g.values]}


out["avg_points_by_constructor"] = by_season(df, avg_points_by_constructor)

# 4. avg final position by number of pitstops (cap at 4)
def avg_position_by_pitstops(frame):
    f = frame[(~frame["did_not_finish"]) & (frame["num_pitstops"] <= 4)]
    g = f.groupby("num_pitstops")["final_position_num"].mean().sort_index()
    return {"labels": [str(i) for i in g.index], "values": [round(float(v), 2) for v in g.values]}


out["avg_position_by_pitstops"] = by_season(df, avg_position_by_pitstops)

# 5. pitstop count distribution
def pitstop_count_dist(frame):
    g = frame["num_pitstops"].value_counts().sort_index()
    g = g[g.index <= 6]
    return {"labels": [str(i) for i in g.index], "values": [int(v) for v in g.values]}


out["pitstop_count_distribution"] = by_season(df, pitstop_count_dist)

# 6. avg pit stop duration histogram (bins)
def duration_histogram(frame):
    vals = frame["avg_pitstop_duration_s"].dropna()
    counts, edges = np.histogram(vals, bins=16, range=(18, 60))
    labels = [f"{edges[i]:.0f}-{edges[i+1]:.0f}" for i in range(len(edges) - 1)]
    return {"labels": labels, "values": [int(c) for c in counts]}


out["pitstop_duration_histogram"] = by_season(df, duration_histogram)

# 7. first pit lap vs final position, split by scored points or not
def first_pit_scatter(frame):
    f = frame[(~frame["did_not_finish"])].dropna(subset=["first_pitstop_lap"])
    scored = f[f["did_finish_points"]]
    not_scored = f[~f["did_finish_points"]]
    return {
        "scored": [{"x": int(r.first_pitstop_lap), "y": int(r.final_position_num)} for r in scored.itertuples()],
        "not_scored": [{"x": int(r.first_pitstop_lap), "y": int(r.final_position_num)} for r in not_scored.itertuples()],
    }


out["first_pitstop_vs_position"] = by_season(df, first_pit_scatter)

# 8. season points by top 6 constructors, line chart (fixed across all seasons, not filterable)
top6 = df.groupby("constructor_name")["points"].sum().sort_values(ascending=False).head(6).index.tolist()
season_points = (
    df[df["constructor_name"].isin(top6)]
    .groupby(["season", "constructor_name"])["points"]
    .sum()
    .reset_index()
)
datasets = []
for c in top6:
    sub = season_points[season_points["constructor_name"] == c].sort_values("season")
    datasets.append({"label": c, "data": [round(float(v), 1) for v in sub["points"]]})
out["season_points_top_constructors"] = {"labels": ["2021", "2022", "2023"], "datasets": datasets}

# 9. DNF rate by constructor
def dnf_rate_by_constructor(frame):
    g = (frame.groupby("constructor_name")["did_not_finish"].mean() * 100).sort_values(ascending=False)
    return {"labels": list(g.index), "values": [round(float(v), 1) for v in g.values]}


out["dnf_rate_by_constructor"] = by_season(df, dnf_rate_by_constructor)

# 10. quali vs grid scatter
def quali_vs_grid_scatter(frame):
    f = frame.dropna(subset=["quali_position"])
    pts = f[["quali_position", "grid"]]
    return [{"x": int(r.quali_position), "y": int(r.grid)} for r in pts.itertuples()]


out["quali_vs_grid"] = by_season(df, quali_vs_grid_scatter)

# 11. DNF rate by air temperature bucket (only rows with weather data, not season-filterable
#     in a meaningful way given the small weather subset, so computed once on all rows)
weather_df = df.dropna(subset=["air_temp_mean"]).copy()
if len(weather_df) > 0:
    bins = pd.cut(weather_df["air_temp_mean"], bins=5)
    weather_df["temp_bucket"] = bins.astype(str)
    order = sorted(weather_df["temp_bucket"].unique(), key=lambda s: float(s.split(",")[0].strip("(")))
    g = (weather_df.groupby("temp_bucket", observed=True)["did_not_finish"].mean() * 100)
    out["dnf_rate_by_temperature"] = {
        "labels": [b.replace("(", "").replace("]", "").replace(",", " to") + " C" for b in order],
        "values": [round(float(g[b]), 1) for b in order],
        "n": int(len(weather_df)),
    }
else:
    out["dnf_rate_by_temperature"] = {"labels": [], "values": [], "n": 0}

# 12. avg final position by number of distinct tyre compounds used
tyre_df = df.dropna(subset=["num_compounds_used"])
if len(tyre_df) > 0:
    f = tyre_df[~tyre_df["did_not_finish"]]
    g = f.groupby("num_compounds_used")["final_position_num"].mean().sort_index()
    out["position_by_tyre_compounds"] = {
        "labels": [str(int(i)) for i in g.index],
        "values": [round(float(v), 2) for v in g.values],
        "n": int(len(tyre_df)),
    }
else:
    out["position_by_tyre_compounds"] = {"labels": [], "values": [], "n": 0}

with open("site/data/chart_data.json", "w") as f:
    json.dump(out, f)

print("wrote site/data/chart_data.json")
print("size:", len(json.dumps(out)), "bytes")
