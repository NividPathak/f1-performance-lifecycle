# Pit stops from Jolpica, one request per race.
import json
import time
import urllib.request

from paths import RAW

BASE = "https://api.jolpi.ca/ergast/f1"
SEASONS = [2021, 2022, 2023]


def fetch_race_pitstops(season, rnd):
    offset = 0
    limit = 100
    stops = []
    total = None
    while total is None or offset < total:
        url = f"{BASE}/{season}/{rnd}/pitstops.json?limit={limit}&offset={offset}"
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read())
        m = data["MRData"]
        total = int(m["total"])
        races = m["RaceTable"]["Races"]
        if races:
            stops.extend(races[0].get("PitStops", []))
        offset += limit
        time.sleep(0.2)
    return stops


def main():
    for season in SEASONS:
        with open(RAW / f"schedule_{season}.json") as f:
            sched = json.load(f)
        rounds = [r["round"] for r in sched["MRData"]["RaceTable"]["Races"]]
        season_out = {}
        for rnd in rounds:
            stops = fetch_race_pitstops(season, rnd)
            season_out[rnd] = stops
            print(f"{season} round {rnd}: {len(stops)} pit stops")
        with open(RAW / f"pitstops_{season}_full.json", "w") as f:
            json.dump(season_out, f)


if __name__ == "__main__":
    main()
