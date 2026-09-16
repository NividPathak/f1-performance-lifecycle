# Formula 1 Race Performance and Strategy: Data Science Lifecycle Project

A tab-based website built for an individual Data Science Lifecycle course project at CU Boulder. This is Module 1, Part 1. Only the Introduction and DataPrep_EDA tabs have content. The rest are placeholders for later modules.

Topic: what factors, grid position, tyre strategy, pit stop timing, constructor, and weather, predict race outcomes and driver performance in Formula 1.

## Data sources (real data only)

- [Jolpica-F1 API](https://api.jolpi.ca/ergast/f1): official historical race results, qualifying, and pit stop records, 2021 to 2023 seasons (66 races).
- [FastF1](https://docs.fastf1.dev/) Python library: official F1 timing data for tyre compound strategy and race weather, for 38 of the 66 races. The rest were not pulled due to the public timing API's hourly rate limit.

No simulated or synthetic data was used anywhere in this project. The 2026 season calendar shown on the Introduction tab is real, sourced from formula1.com and the FIA's 2026 calendar confirmation, and is included for context only. It is not part of the analyzed dataset.

## Design notes

The site uses a flat color theme (F1 red, black, white, silver) with no gradients, and all 12 EDA charts are rendered live in the browser with Chart.js from precomputed data, so they are interactive (hover for exact values) instead of static images. The header emblem is an original checkered-flag badge, not the official F1 logo, since that mark is trademarked.

## Repository layout

```
index.html                         the site (tab navigation, all content)
assets/style.css                   styling
assets/script.js                   tab-switching logic
assets/charts.js                   renders the 12 interactive charts with Chart.js
assets/calendar.js                 renders the 2026 season calendar table
assets/img/                        raw and cleaned data preview images, intro illustration
data/f1_driver_race_cleaned.csv    final cleaned dataset (1,320 rows, 31 columns)
data/combined_raw_snapshot.csv     merged data before cleaning
data/cleaning_log.txt              step-by-step cleaning log
data/chart_data.json               precomputed aggregates that feed the charts
data/raw_pulls/                    every raw API response, uncleaned
code/                              every script used to fetch, clean, and prepare the data
code/paths.py                      shared file locations used by all scripts
```

## Rebuilding the data

The scripts in `code/` resolve every file location through `code/paths.py`, so they can be run from anywhere. They need Python 3 with `pandas`, `numpy`, and `matplotlib` (plus `fastf1` for the FastF1 pull).

```bash
python code/fetch_jolpica.py            # results + qualifying -> data/raw_pulls/
python code/fetch_pitstops.py           # pit stops -> data/raw_pulls/ (needs schedule_*.json)
python code/fetch_fastf1.py             # tyre + weather -> data/raw_pulls/fastf1/ (rate limited, resumable)
python code/build_dataset.py            # merge + clean -> data/*.csv, data/cleaning_log.txt
python code/make_chart_data.py          # aggregates -> data/chart_data.json
python code/make_data_preview_images.py # raw/cleaned sample tables -> assets/img/
python code/make_intro_image.py         # intro illustration -> assets/img/
```

The raw API pulls are already committed, so only the last four steps are needed to regenerate the site's data.

## Hosting

The site is live on GitHub Pages at https://nividpathak.github.io/f1-performance-lifecycle/, served from the root of the `master` branch. Every push to `master` redeploys it automatically, usually within a minute or two.

Later modules are added by filling in the matching empty `<section>` in `index.html`, then committing and pushing.
