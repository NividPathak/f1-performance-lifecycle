# F1 Race Performance & Strategy

Course project for Data Science Lifecycle at CU Boulder. The question: how much do grid position, pit strategy, tyres, team, and weather each matter to where an F1 driver finishes?

Live site: https://nividpathak.github.io/f1-performance-lifecycle/

Right now the Introduction and Data Prep & EDA tabs are done. The other tabs get filled in as the course goes on.

## Data

- [Jolpica-F1 API](https://github.com/jolpica/jolpica-f1): results, qualifying, and pit stops for every race from 2021 to 2023 (66 races).
- [FastF1](https://docs.fastf1.dev/): tyre compounds and weather for 38 of those races (the public timing feed rate-limited me before I got the rest), plus the Bahrain track outline used on the Introduction tab.

## Layout

```
index.html                  the site
assets/style.css            styles
assets/script.js            tab switching, cleaning log loader
assets/motion.js            background speed lines + hero car (anime.js)
assets/track.js             animated Bahrain track map (anime.js + SVG)
assets/charts.js            the 12 EDA charts (Chart.js)
assets/calendar.js          2026 calendar table
assets/vendor_*.min.js      anime.js 3.2.2 and Chart.js, vendored
assets/samples.js           raw / cleaned sample tables
assets/img/                 photo
data/raw_pulls/             raw API responses
data/combined_raw_snapshot.csv
data/f1_driver_race_cleaned.csv
data/cleaning_log.txt
data/chart_data.json        aggregates behind the charts
data/track_bahrain.json     track outline + corner numbers
data/sample_tables.json     rows shown in the before/after tables
code/                       fetch, clean, and chart-prep scripts
```

## Rebuilding the data

Scripts find their files through `code/paths.py`, so run them from anywhere. You need Python 3 with `pandas`, `numpy`, and `matplotlib`, plus `fastf1` for the FastF1 scripts.

```bash
python code/fetch_jolpica.py            # results + qualifying -> data/raw_pulls/
python code/fetch_pitstops.py           # pit stops -> data/raw_pulls/ (needs schedule_*.json)
python code/fetch_fastf1.py             # tyres + weather -> data/raw_pulls/fastf1/ (resumable)
python code/build_dataset.py            # merge + clean -> data/*.csv, data/cleaning_log.txt
python code/make_chart_data.py          # data/chart_data.json
python code/make_sample_tables.py       # data/sample_tables.json
python code/make_track_data.py          # data/track_bahrain.json
```

The raw pulls are already committed, so you only need the last four to regenerate what the site uses.

## Hosting

GitHub Pages serves the root of `master`. Pushing to `master` redeploys the site within a minute or two.

## Credits

Font: Titillium Web (Google Fonts). Animation: [anime.js](https://animejs.com/) (MIT). Charts: [Chart.js](https://www.chartjs.org/) (MIT).
