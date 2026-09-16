"""Fetch per-race tyre-compound (stint) and weather summaries from FastF1's
official timing data feed. Writes one JSON file per race under data/raw_pulls/fastf1/.
Only lap and weather data are loaded (no telemetry) to keep this reasonably
fast across many races. Designed to be resumable: already-fetched races are
skipped on re-run.
"""
import json
import os
import time
import fastf1
import pandas as pd

from paths import FASTF1_CACHE, FASTF1_RAW, RAW

FASTF1_CACHE.mkdir(exist_ok=True)
fastf1.Cache.enable_cache(str(FASTF1_CACHE))
FASTF1_RAW.mkdir(parents=True, exist_ok=True)

SEASONS = [2021, 2022, 2023]


def summarize_race(season, rnd):
    session = fastf1.get_session(season, rnd, "R")
    session.load(telemetry=False, weather=True, laps=True, messages=False)
    laps = session.laps

    # tyre stints: driver -> list of {compound, stint, lap_count}
    stints = (
        laps.groupby(["Driver", "Stint", "Compound"])
        .agg(lap_count=("LapNumber", "count"))
        .reset_index()
    )
    stint_records = stints.to_dict(orient="records")

    # pit-in laps per driver (from lap data, cross-checked against Jolpica pitstops)
    pit_laps = (
        laps[laps["PitInTime"].notna()][["Driver", "LapNumber"]]
        .rename(columns={"LapNumber": "pit_in_lap"})
        .to_dict(orient="records")
    )

    weather = session.weather_data
    weather_summary = {
        "air_temp_mean": float(weather["AirTemp"].mean()),
        "track_temp_mean": float(weather["TrackTemp"].mean()),
        "humidity_mean": float(weather["Humidity"].mean()),
        "wind_speed_mean": float(weather["WindSpeed"].mean()),
        "rainfall": bool(weather["Rainfall"].any()),
    }

    return {
        "season": season,
        "round": rnd,
        "event_name": session.event["EventName"],
        "stints": stint_records,
        "pit_laps": pit_laps,
        "weather": weather_summary,
    }


def main():
    for season in SEASONS:
        with open(RAW / f"schedule_{season}.json") as f:
            sched = json.load(f)
        rounds = [int(r["round"]) for r in sched["MRData"]["RaceTable"]["Races"]]
        for rnd in rounds:
            out_path = FASTF1_RAW / f"{season}_{rnd}.json"
            if os.path.exists(out_path):
                print(f"skip {season} round {rnd} (cached)")
                continue
            try:
                data = summarize_race(season, rnd)
                with open(out_path, "w") as f:
                    json.dump(data, f)
                print(f"OK {season} round {rnd}: {data['event_name']}")
            except Exception as e:
                print(f"FAIL {season} round {rnd}: {e}")
            time.sleep(0.5)


if __name__ == "__main__":
    main()
