# Formula 1 Race Performance & Strategy — Data Science Lifecycle Project

A static, tab-based website built for an individual Data Science Lifecycle course project at CU Boulder. This is **Module 1, Part 1**: only the *Introduction* and *DataPrep_EDA* tabs have content; the rest are placeholders for later modules.

**Topic:** what factors — grid position, tyre strategy, pit stop timing, constructor, and weather — predict race outcomes and driver performance in Formula 1.

## Data sources (real data only)

- [Jolpica-F1 API](https://api.jolpi.ca/ergast/f1) — official historical race results, qualifying, and pit stop records, 2021–2023 seasons (66 races).
- [FastF1](https://docs.fastf1.dev/) Python library — official F1 timing data for tyre-compound strategy and race weather, for 38 of the 66 races (the rest were not pulled due to the public timing API's hourly rate limit).

No simulated or synthetic data was used anywhere in this project.

## Repository layout

```
index.html              the site (tab navigation, all content)
assets/style.css         styling
assets/script.js         tab-switching logic
assets/img/               all 15 figures (data previews + EDA visualizations)
data/f1_driver_race_cleaned.csv   final cleaned dataset (1,320 rows x 31 cols)
data/combined_raw_snapshot.csv    merged data before cleaning
data/cleaning_log.txt             step-by-step cleaning log
data/raw_pulls/                    every raw API response, uncleaned
code/                              every script used to fetch, clean, and visualize the data
```

## Publishing this to GitHub Pages

1. Create a new **public** GitHub repository (e.g. `f1-data-science-lifecycle`) — do this on github.com, no need to add a README/gitignore there since this folder already has one.
2. From inside this folder, point it at your new repo and push:

   ```bash
   git remote add origin https://github.com/<your-username>/<your-repo>.git
   git branch -M main
   git push -u origin main
   ```

3. On GitHub, open the repo's **Settings → Pages**.
4. Under "Build and deployment", set **Source** to "Deploy from a branch", branch **main**, folder **/ (root)**, then click **Save**.
5. GitHub will publish the site at `https://<your-username>.github.io/<your-repo>/` within a minute or two (refresh the Pages settings page to get the link).

Every later module can be added by editing the relevant empty `<section>` in `index.html` and running `git add . && git commit -m "..." && git push` — Pages redeploys automatically on every push to `main`.
