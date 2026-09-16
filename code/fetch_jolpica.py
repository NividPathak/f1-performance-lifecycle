# Full-season results and qualifying from Jolpica (paged, 100 per request).
import json
import time
import urllib.request

from paths import RAW

BASE = "https://api.jolpi.ca/ergast/f1"
SEASONS = [2021, 2022, 2023]


def fetch_paginated(url_template, season):
    offset = 0
    limit = 100
    all_races = {}
    total = None
    while total is None or offset < total:
        url = url_template.format(season=season, limit=limit, offset=offset)
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read())
        m = data["MRData"]
        total = int(m["total"])
        for race in m["RaceTable"]["Races"]:
            key = race["round"]
            if key not in all_races:
                all_races[key] = race
            else:
                # merge Results / QualifyingResults lists
                for field in ("Results", "QualifyingResults"):
                    if field in race:
                        all_races.setdefault(key, race).setdefault(field, [])
                        all_races[key][field].extend(race[field])
        offset += limit
        time.sleep(0.25)
    return list(all_races.values()), total


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for season in SEASONS:
        for name, path in [
            ("results", "/{season}/results.json?limit={limit}&offset={offset}"),
            ("qualifying", "/{season}/qualifying.json?limit={limit}&offset={offset}"),
        ]:
            url_template = BASE + path
            races, total = fetch_paginated(url_template, season)
            out = {"season": season, "endpoint": name, "total_records": total, "races": races}
            with open(RAW / f"{name}_{season}_full.json", "w") as f:
                json.dump(out, f)
            print(f"{name} {season}: {len(races)} races, {total} total records")


if __name__ == "__main__":
    main()
