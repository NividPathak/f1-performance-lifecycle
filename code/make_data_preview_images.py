"""Render small labeled table images of a RAW data sample and a CLEANED data
sample (not screenshots — rendered directly from the dataframes with
matplotlib's table feature) for the DataPrep_EDA tab.
"""
import pandas as pd
import matplotlib.pyplot as plt

from paths import CLEANED_CSV, COMBINED_RAW_CSV, IMG

plt.rcParams["font.size"] = 8


def render_table(df, title, out_path, col_widths=None):
    df = df.copy()
    for c in df.columns:
        if df[c].dtype == float:
            df[c] = df[c].round(2)
    fig, ax = plt.subplots(figsize=(13, 3.2))
    ax.axis("off")
    fig.suptitle(title, fontsize=11, fontweight="bold", y=0.98, color="#15151e")
    tbl = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        cellLoc="center",
        loc="upper center",
        bbox=[0, 0, 1, 0.85],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(7.5)
    for (row, col), cell in tbl.get_celld().items():
        cell.set_edgecolor("#e2e2e6")
        if row == 0:
            cell.set_facecolor("#15151e")
            cell.set_text_props(color="white", fontweight="bold")
        else:
            cell.set_facecolor("#fafafb" if row % 2 == 0 else "white")
    fig.savefig(out_path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    print("saved", out_path)


raw = pd.read_csv(COMBINED_RAW_CSV)
raw_cols = ["season", "round", "driver_code", "constructor_name", "grid",
            "final_position", "status", "points", "num_pitstops", "avg_pitstop_duration_s"]
raw_sample = raw[raw_cols].head(8).fillna("NaN")
render_table(raw_sample, "RAW data sample, pre-cleaning: Jolpica-F1 results, qualifying, and pit stops, merged but unprocessed",
             IMG / "00_raw_data_sample.png")

clean = pd.read_csv(CLEANED_CSV)
clean_cols = ["season", "round", "driver_code", "constructor_name", "grid", "grid_zone",
              "final_position_num", "did_not_finish", "points", "num_pitstops", "avg_pitstop_duration_s"]
clean_sample = clean[clean_cols].head(8)
render_table(clean_sample, "CLEANED data sample: DNF flag derived, grid=0 recoded, missing pit-stop values resolved, grid_zone added",
             IMG / "00_cleaned_data_sample.png")
