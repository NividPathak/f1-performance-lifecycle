"""Build a tidy per-driver-per-race dataset from the raw Jolpica-F1 JSON pulls
(results, qualifying, pit stops) and, when available, the FastF1 tyre/weather
summaries. Documents every cleaning decision inline via the `cleaning_log`
list, which is written out alongside the cleaned CSV so the steps are
traceable.
"""
import json
import os
import numpy as np
import pandas as pd

SEASONS = [2021, 2022, 2023]
cleaning_log = []


def log(msg):
    cleaning_log.append(msg)
    print(msg)


def load_results():
    rows = []
    for season in SEASONS:
        with open(f"raw/results_{season}_full.json") as f:
            data = json.load(f)
        for race in data["races"]:
            for res in race.get("Results", []):
                rows.append({
                    "season": int(season),
                    "round": int(race["round"]),
                    "race_name": race["raceName"],
                    "circuit_id": race["Circuit"]["circuitId"],
                    "circuit_name": race["Circuit"]["circuitName"],
                    "date": race["date"],
                    "driver_id": res["Driver"]["driverId"],
                    "driver_code": res["Driver"].get("code", ""),
                    "driver_name": res["Driver"]["givenName"] + " " + res["Driver"]["familyName"],
                    "constructor_id": res["Constructor"]["constructorId"],
                    "constructor_name": res["Constructor"]["name"],
                    "grid": int(res["grid"]),
                    "final_position": res.get("position"),
                    "position_text": res.get("positionText"),
                    "points": float(res["points"]),
                    "status": res["status"],
                    "laps_completed": int(res["laps"]),
                    "fastest_lap_rank": res.get("FastestLap", {}).get("rank"),
                    "fastest_lap_time": res.get("FastestLap", {}).get("Time", {}).get("time"),
                })
    return pd.DataFrame(rows)


def load_qualifying():
    rows = []
    for season in SEASONS:
        with open(f"raw/qualifying_{season}_full.json") as f:
            data = json.load(f)
        for race in data["races"]:
            for res in race.get("QualifyingResults", []):
                rows.append({
                    "season": int(season),
                    "round": int(race["round"]),
                    "driver_id": res["Driver"]["driverId"],
                    "quali_position": int(res["position"]),
                    "q1": res.get("Q1"),
                    "q2": res.get("Q2"),
                    "q3": res.get("Q3"),
                })
    return pd.DataFrame(rows)


def load_pitstops():
    rows = []
    for season in SEASONS:
        with open(f"raw/pitstops_{season}_full.json") as f:
            data = json.load(f)
        for rnd, stops in data.items():
            per_driver = {}
            for s in stops:
                did = s["driverId"]
                per_driver.setdefault(did, []).append(s)
            for did, slist in per_driver.items():
                durations = []
                for s in slist:
                    try:
                        durations.append(float(s["duration"]))
                    except (KeyError, ValueError):
                        pass
                rows.append({
                    "season": int(season),
                    "round": int(rnd),
                    "driver_id": did,
                    "num_pitstops": len(slist),
                    "avg_pitstop_duration_s": float(np.mean(durations)) if durations else np.nan,
                    "first_pitstop_lap": min(int(s["lap"]) for s in slist),
                })
    return pd.DataFrame(rows)


def load_fastf1():
    """Optional: merge tyre-stint and weather summaries if FastF1 fetch has
    produced files by the time this runs. Returns empty frames if not."""
    stint_rows, weather_rows = [], []
    fdir = "raw/fastf1"
    if not os.path.isdir(fdir):
        return pd.DataFrame(), pd.DataFrame()
    for fname in os.listdir(fdir):
        with open(os.path.join(fdir, fname)) as f:
            d = json.load(f)
        season, rnd = d["season"], d["round"]
        weather_rows.append({
            "season": season, "round": rnd,
            "air_temp_mean": d["weather"]["air_temp_mean"],
            "track_temp_mean": d["weather"]["track_temp_mean"],
            "humidity_mean": d["weather"]["humidity_mean"],
            "rainfall": d["weather"]["rainfall"],
        })
        # number of distinct tyre compounds used per driver = strategy proxy
        by_driver = {}
        for s in d["stints"]:
            by_driver.setdefault(s["Driver"], set()).add(s["Compound"])
        for drv, compounds in by_driver.items():
            stint_rows.append({
                "season": season, "round": rnd, "driver_code": drv,
                "num_compounds_used": len(compounds),
                "compounds_used": ",".join(sorted(compounds)),
            })
    return pd.DataFrame(stint_rows), pd.DataFrame(weather_rows)


def main():
    os.makedirs("cleaned", exist_ok=True)

    results = load_results()
    log(f"Loaded {len(results)} driver-race result rows from Jolpica-F1 (results endpoint), "
        f"seasons {SEASONS}.")

    qualifying = load_qualifying()
    log(f"Loaded {len(qualifying)} driver-race qualifying rows from Jolpica-F1 (qualifying endpoint).")

    pitstops = load_pitstops()
    log(f"Loaded pit stop summaries for {len(pitstops)} driver-race combinations "
        f"(count, avg duration, first-stop lap) from Jolpica-F1 (pitstops endpoint, per race).")

    df = results.merge(qualifying, on=["season", "round", "driver_id"], how="left")
    log("Merged results with qualifying on (season, round, driver_id).")
    df = df.merge(pitstops, on=["season", "round", "driver_id"], how="left")
    log("Merged in pit stop summaries on (season, round, driver_id).")

    stints, weather = load_fastf1()
    if not stints.empty:
        df = df.merge(stints, on=["season", "round", "driver_code"], how="left")
        log(f"Merged in FastF1 tyre-compound strategy summaries for {len(stints)} driver-race rows "
            f"(number of distinct compounds used).")
    else:
        log("FastF1 tyre-compound data not yet available at merge time; num_compounds_used/"
            "compounds_used left absent for this run.")
    if not weather.empty:
        df = df.merge(weather, on=["season", "round"], how="left")
        log(f"Merged in FastF1 weather summaries for {len(weather)} races "
            f"(mean air/track temp, humidity, rainfall flag).")
    else:
        log("FastF1 weather data not yet available at merge time; weather columns left absent.")

    raw_snapshot = df.copy()
    raw_snapshot.to_csv("raw/combined_raw_snapshot.csv", index=False)
    log(f"Saved combined-but-uncleaned snapshot ({raw_snapshot.shape[0]} rows x "
        f"{raw_snapshot.shape[1]} cols) to raw/combined_raw_snapshot.csv before any cleaning, "
        f"for before/after comparison.")

    # ---------------- CLEANING STEPS ----------------

    # 1. DNF/DNS/DSQ handling: the raw `position` field from Jolpica-F1 is
    #    actually always populated with a classified running order, even for
    #    drivers who retired but completed enough of the race distance to be
    #    scored (their status just says why, e.g. "Retired", "Accident",
    #    "+1 Lap" for being lapped but still classified as a finisher). So a
    #    numeric position alone cannot distinguish a true non-finish from a
    #    normal finish. did_not_finish is instead derived from the `status`
    #    text: "Finished" and the "+N Lap(s)" lapped-but-classified statuses
    #    count as finishes; anything else (mechanical failure, accident,
    #    disqualification, did-not-start, withdrew) counts as a genuine DNF.
    finished_pattern = r"^(Finished|\+\d+ Laps?)$"
    df["did_not_finish"] = ~df["status"].str.match(finished_pattern)
    n_dnf = df["did_not_finish"].sum()
    log(f"Derived did_not_finish from the status text (Finished / +N Lap(s) = finished; anything "
        f"else, e.g. Retired, Accident, Disqualified, Did not start = True): {n_dnf} of {len(df)} "
        f"rows flagged as genuine non-finishes. Jolpica-F1 always reports a classified numeric "
        f"position even for most non-finishers, so position alone could not be used for this.")
    df["final_position_num"] = pd.to_numeric(df["final_position"], errors="coerce")

    # 2. Duplicate rows
    before = len(df)
    df = df.drop_duplicates(subset=["season", "round", "driver_id"])
    log(f"Dropped {before - len(df)} exact duplicate (season, round, driver_id) rows.")

    # 3. Grid position of 0 in Ergast/Jolpica means the driver started from
    #    the pit lane (no formal grid slot). Recode to 21 (one worse than the
    #    typical 20-car grid's last real slot) so it stays numerically
    #    meaningful for grid-vs-outcome analysis instead of implying P0.
    n_pitlane_start = (df["grid"] == 0).sum()
    df.loc[df["grid"] == 0, "grid"] = 21
    log(f"Recoded {n_pitlane_start} grid=0 values (pit-lane starts, no official grid slot) to 21 "
        f"so they sort as worse than every real grid position instead of implying pole position.")

    # 4. Pit stop fields: a true NaN here means the driver made zero pit
    #    stops in that race (rare, e.g. red-flagged/shortened races), which
    #    is a real and valid value of zero, not a missing measurement.
    n_no_stops = df["num_pitstops"].isna().sum()
    df["num_pitstops"] = df["num_pitstops"].fillna(0).astype(int)
    log(f"Filled {n_no_stops} missing num_pitstops values with 0 (no pit-stop record for that "
        f"driver-race means zero stops were made, most often in races ended early by a red flag).")

    # 5. avg_pitstop_duration_s: leave NaN when num_pitstops == 0 (duration is
    #    undefined, not zero) but flag clearly.
    df["avg_pitstop_duration_s"] = np.where(
        df["num_pitstops"] == 0, np.nan, df["avg_pitstop_duration_s"]
    )
    log("Left avg_pitstop_duration_s as NaN specifically where num_pitstops==0, since an average "
        "duration is undefined (not zero) when no stop occurred; this keeps the column honest for "
        "downstream numeric summaries.")

    # 6. Outlier check on pit stop durations: extreme values (>100s) are
    #    almost always drive-through/stop-go penalties or long unscheduled
    #    repairs recorded oddly by the timing system, not representative of
    #    a normal tyre-change strategy call. Cap rather than drop so the row
    #    (and its grid/finish data) is retained, flagging the capped rows.
    dur_col = "avg_pitstop_duration_s"
    outlier_mask = df[dur_col] > 100
    n_outliers = outlier_mask.sum()
    df["pitstop_duration_outlier_capped"] = outlier_mask
    df.loc[outlier_mask, dur_col] = 100.0
    log(f"Capped {n_outliers} avg_pitstop_duration_s values above 100 seconds at 100s and flagged "
        f"them in pitstop_duration_outlier_capped; such long stops are typically penalties or "
        f"unscheduled repairs, not representative tyre-change times, and dropping the whole row "
        f"would have discarded otherwise-valid grid/finish/constructor data.")

    # 7. quali_position missing (driver did not set a qualifying time, e.g.
    #    withdrew before qualifying, or a sprint-weekend edge case). Left as
    #    NaN with an explicit flag rather than imputed, since there is no
    #    defensible fill value for "did not qualify."
    n_no_quali = df["quali_position"].isna().sum()
    df["no_qualifying_time"] = df["quali_position"].isna()
    log(f"Flagged {n_no_quali} rows with missing quali_position as no_qualifying_time=True rather "
        f"than imputing a value; there is no valid stand-in for a qualifying position that was "
        f"never set.")

    # 8. points / laps_completed / final_position_num sanity bounds.
    bad_points = df[(df["points"] < 0) | (df["points"] > 26)]
    log(f"Sanity check: {len(bad_points)} rows outside the plausible F1 points range [0, 26] "
        f"(found: none)." if bad_points.empty else
        f"Sanity check found {len(bad_points)} rows with implausible points values; removed.")
    df = df[(df["points"] >= 0) & (df["points"] <= 26)]

    # 9. Discretize grid position into starting-zone buckets for the EDA
    #    tab (front row / top 5 / midfield / back), useful for grouped plots.
    bins = [0, 1, 3, 5, 10, 21]
    labels = ["Pole (P1)", "Front row (P2-P3)", "Top 5 (P4-P5)", "Midfield (P6-P10)", "Back (P11+)"]
    df["grid_zone"] = pd.cut(df["grid"], bins=bins, labels=labels, include_lowest=True)
    log("Added a discretized grid_zone column (Pole / Front row / Top 5 / Midfield / Back) "
        "from the numeric grid column, for grouped visualizations.")

    # 10. Standardize dtypes and column order for the final cleaned file.
    df["did_finish_points"] = df["points"] > 0
    final_cols = [
        "season", "round", "race_name", "circuit_id", "circuit_name", "date",
        "driver_id", "driver_code", "driver_name", "constructor_id", "constructor_name",
        "grid", "grid_zone", "quali_position", "no_qualifying_time",
        "final_position_num", "did_not_finish", "status",
        "points", "did_finish_points", "laps_completed",
        "num_pitstops", "first_pitstop_lap", "avg_pitstop_duration_s",
        "pitstop_duration_outlier_capped",
    ]
    optional_cols = ["num_compounds_used", "compounds_used", "air_temp_mean",
                      "track_temp_mean", "humidity_mean", "rainfall"]
    for c in optional_cols:
        if c in df.columns:
            final_cols.append(c)
    df = df[final_cols]

    df.to_csv("cleaned/f1_driver_race_cleaned.csv", index=False)
    log(f"Wrote final cleaned dataset: {df.shape[0]} rows x {df.shape[1]} columns to "
        f"cleaned/f1_driver_race_cleaned.csv.")

    with open("cleaned/cleaning_log.txt", "w") as f:
        f.write("\n".join(f"{i+1}. {m}" for i, m in enumerate(cleaning_log)))
    log("Cleaning log written to cleaned/cleaning_log.txt")

    print("\n--- Final null counts (should be zero except intentionally-preserved fields) ---")
    print(df.isna().sum())


if __name__ == "__main__":
    main()
