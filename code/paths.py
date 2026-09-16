from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw_pulls"
FASTF1_RAW = RAW / "fastf1"
IMG = ROOT / "assets" / "img"

COMBINED_RAW_CSV = DATA / "combined_raw_snapshot.csv"
CLEANED_CSV = DATA / "f1_driver_race_cleaned.csv"
CLEANING_LOG = DATA / "cleaning_log.txt"
CHART_DATA = DATA / "chart_data.json"
FASTF1_CACHE = ROOT / "fastf1_cache"
