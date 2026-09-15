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
```

## Publishing this to GitHub Pages

1. Create a new public GitHub repository (for example `f1-data-science-lifecycle`) on github.com. No need to add a README or gitignore there, since this folder already has one.
2. From inside this folder, point it at your new repo and push.

   ```bash
   git remote add origin https://github.com/<your-username>/<your-repo>.git
   git branch -M main
   git push -u origin main
   ```

3. On GitHub, open the repo's Settings, then Pages.
4. Under "Build and deployment", set Source to "Deploy from a branch", branch main, folder / (root), then click Save.
5. GitHub will publish the site at `https://<your-username>.github.io/<your-repo>/` within a minute or two. Refresh the Pages settings page to get the link.

Every later module can be added by editing the relevant empty `<section>` in `index.html` and running `git add . && git commit -m "..." && git push`. Pages redeploys automatically on every push to `main`.
