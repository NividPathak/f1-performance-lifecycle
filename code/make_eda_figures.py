"""Generate 12 labeled EDA visualizations exploring grid position, tyre
strategy, pit stop timing, constructor, and weather vs race outcomes, from
the cleaned Formula 1 dataset. All figures saved to figures/ as PNGs.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns

sns.set_theme(style="whitegrid")
PALETTE = "crest"

df = pd.read_csv("cleaned/f1_driver_race_cleaned.csv")
finished = df[~df["did_not_finish"]].copy()

def save(fig, name):
    fig.tight_layout()
    fig.savefig(f"figures/{name}", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


# 1. Grid position vs final finishing position (scatter + trend)
fig, ax = plt.subplots(figsize=(7, 6))
sns.regplot(data=finished, x="grid", y="final_position_num", scatter_kws={"alpha": 0.15, "s": 20},
            line_kws={"color": "crimson"}, ax=ax)
ax.set_title("Grid Position vs Final Race Position\n(2021-2023 seasons, finishers only)")
ax.set_xlabel("Starting Grid Position")
ax.set_ylabel("Final Race Position")
ax.invert_yaxis()
save(fig, "01_grid_vs_final_position.png")

# 2. Distribution of final position by grid zone
fig, ax = plt.subplots(figsize=(8, 6))
order = ["Pole (P1)", "Front row (P2-P3)", "Top 5 (P4-P5)", "Midfield (P6-P10)", "Back (P11+)"]
sns.boxplot(data=finished, x="grid_zone", y="final_position_num", order=order, palette=PALETTE, ax=ax)
ax.set_title("Final Race Position by Starting Grid Zone")
ax.set_xlabel("Starting Grid Zone")
ax.set_ylabel("Final Race Position")
ax.invert_yaxis()
plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
save(fig, "02_final_position_by_grid_zone.png")

# 3. Average points by constructor
fig, ax = plt.subplots(figsize=(9, 6))
avg_pts = df.groupby("constructor_name")["points"].mean().sort_values(ascending=False)
sns.barplot(x=avg_pts.values, y=avg_pts.index, palette=PALETTE, ax=ax)
ax.set_title("Average Points per Race by Constructor (2021-2023)")
ax.set_xlabel("Average Points per Race")
ax.set_ylabel("Constructor")
save(fig, "03_avg_points_by_constructor.png")

# 4. Number of pit stops vs final position
fig, ax = plt.subplots(figsize=(8, 6))
sns.boxplot(data=finished[finished["num_pitstops"] <= 4], x="num_pitstops", y="final_position_num",
            palette=PALETTE, ax=ax)
ax.set_title("Final Race Position by Number of Pit Stops")
ax.set_xlabel("Number of Pit Stops")
ax.set_ylabel("Final Race Position")
ax.invert_yaxis()
save(fig, "04_final_position_by_num_pitstops.png")

# 5. Distribution of pit stop counts
fig, ax = plt.subplots(figsize=(7, 5))
sns.countplot(data=df, x="num_pitstops", palette=PALETTE, ax=ax,
              order=sorted(df["num_pitstops"].unique())[:7])
ax.set_title("Distribution of Pit Stop Counts per Driver per Race")
ax.set_xlabel("Number of Pit Stops")
ax.set_ylabel("Count of Driver-Races")
save(fig, "05_pitstop_count_distribution.png")

# 6. Average pit stop duration distribution
fig, ax = plt.subplots(figsize=(7, 5))
sns.histplot(df["avg_pitstop_duration_s"].dropna(), bins=30, kde=True, color="#3b82f6", ax=ax)
ax.set_title("Distribution of Average Pit Stop Duration")
ax.set_xlabel("Average Pit Stop Duration (seconds)")
ax.set_ylabel("Count of Driver-Races")
save(fig, "06_pitstop_duration_distribution.png")

# 7. First pit stop lap vs final position
fig, ax = plt.subplots(figsize=(7, 6))
sub = finished.dropna(subset=["first_pitstop_lap"])
sns.scatterplot(data=sub, x="first_pitstop_lap", y="final_position_num", alpha=0.25,
                 hue="did_finish_points", palette={True: "#16a34a", False: "#94a3b8"}, ax=ax)
ax.set_title("First Pit Stop Lap vs Final Race Position")
ax.set_xlabel("Lap of First Pit Stop")
ax.set_ylabel("Final Race Position")
ax.invert_yaxis()
ax.legend(title="Scored Points")
save(fig, "07_first_pitstop_lap_vs_position.png")

# 8. Points by season (trend across seasons, constructor stability)
fig, ax = plt.subplots(figsize=(8, 6))
top_constructors = df.groupby("constructor_name")["points"].sum().sort_values(ascending=False).head(6).index
sub = df[df["constructor_name"].isin(top_constructors)]
season_pts = sub.groupby(["season", "constructor_name"])["points"].sum().reset_index()
sns.lineplot(data=season_pts, x="season", y="points", hue="constructor_name", marker="o", ax=ax)
ax.set_title("Total Season Points, Top 6 Constructors (2021-2023)")
ax.set_xlabel("Season")
ax.set_ylabel("Total Points")
ax.set_xticks([2021, 2022, 2023])
ax.legend(title="Constructor", bbox_to_anchor=(1.02, 1), loc="upper left")
save(fig, "08_season_points_top_constructors.png")

# 9. DNF rate by constructor
fig, ax = plt.subplots(figsize=(9, 6))
dnf_rate = df.groupby("constructor_name")["did_not_finish"].mean().sort_values(ascending=False) * 100
sns.barplot(x=dnf_rate.values, y=dnf_rate.index, palette="flare", ax=ax)
ax.set_title("Did-Not-Finish Rate by Constructor (2021-2023)")
ax.set_xlabel("DNF Rate (%)")
ax.set_ylabel("Constructor")
save(fig, "09_dnf_rate_by_constructor.png")

# 10. Qualifying position vs grid position (checking penalties/discrepancies)
fig, ax = plt.subplots(figsize=(7, 6))
sub = df.dropna(subset=["quali_position"])
sns.scatterplot(data=sub, x="quali_position", y="grid", alpha=0.2, ax=ax, color="#7c3aed")
ax.plot([0, 20], [0, 20], "--", color="gray", label="No change (grid = quali)")
ax.set_title("Qualifying Position vs Actual Starting Grid Position\n(gap = grid penalties)")
ax.set_xlabel("Qualifying Position")
ax.set_ylabel("Actual Starting Grid Position")
ax.legend()
save(fig, "10_quali_vs_grid_position.png")

# 11. Weather (air temp) vs DNF rate, where FastF1 weather data is available
weather_df = df.dropna(subset=["air_temp_mean"]).copy()
if len(weather_df) > 0:
    weather_df["temp_bucket"] = pd.cut(weather_df["air_temp_mean"], bins=5)
    fig, ax = plt.subplots(figsize=(8, 6))
    dnf_by_temp = weather_df.groupby("temp_bucket")["did_not_finish"].mean() * 100
    dnf_by_temp.plot(kind="bar", color="#f97316", ax=ax)
    ax.set_title(f"DNF Rate by Average Air Temperature Bucket\n(n={len(weather_df)} driver-races with FastF1 weather data)")
    ax.set_xlabel("Average Air Temperature Bucket (°C)")
    ax.set_ylabel("DNF Rate (%)")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    save(fig, "11_dnf_rate_by_temperature.png")

# 12. Tyre compounds used vs final position, where FastF1 stint data is available
tyre_df = df.dropna(subset=["num_compounds_used"])
if len(tyre_df) > 0:
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.boxplot(data=tyre_df[~tyre_df["did_not_finish"]], x="num_compounds_used", y="final_position_num",
                palette=PALETTE, ax=ax)
    ax.set_title(f"Final Position by Number of Distinct Tyre Compounds Used\n(n={len(tyre_df)} driver-races with FastF1 tyre data)")
    ax.set_xlabel("Number of Distinct Tyre Compounds Used")
    ax.set_ylabel("Final Race Position")
    ax.invert_yaxis()
    save(fig, "12_tyre_compounds_vs_position.png")

print("Done.")
