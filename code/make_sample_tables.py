# Raw vs cleaned sample rows for the Data Prep tab, rendered as real tables on the page.
import json

import pandas as pd

from paths import CLEANED_CSV, COMBINED_RAW_CSV, DATA

RAW_COLS = ["season", "round", "driver_code", "constructor_name", "grid",
            "final_position", "status", "points", "num_pitstops", "avg_pitstop_duration_s"]
CLEAN_COLS = ["season", "round", "driver_code", "constructor_name", "grid", "grid_zone",
              "final_position_num", "did_not_finish", "points", "num_pitstops",
              "avg_pitstop_duration_s"]
ROWS = 8


def sample(path, cols):
    df = pd.read_csv(path)[cols].head(ROWS)
    rows = []
    for row in df.itertuples(index=False):
        out = []
        for v in row:
            if pd.isna(v):
                out.append("NaN")
            elif isinstance(v, float):
                out.append(f"{v:.2f}".rstrip("0").rstrip("."))
            else:
                out.append(str(v))
        rows.append(out)
    return {"columns": cols, "rows": rows}


out = {"raw": sample(COMBINED_RAW_CSV, RAW_COLS), "cleaned": sample(CLEANED_CSV, CLEAN_COLS)}
with open(DATA / "sample_tables.json", "w") as f:
    json.dump(out, f, indent=1)
print("wrote data/sample_tables.json")
