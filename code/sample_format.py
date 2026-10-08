"""One formatter for every sample table on the site, so the same data always looks the same."""

import pandas as pd


def table_rows(df):
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
    return {"columns": list(df.columns), "rows": rows}
