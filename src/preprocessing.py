import pandas as pd
from pathlib import Path

# ============================================================
# PROJECT PATHS
# ============================================================

# Project root = one level above src/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

RAW_DIR = DATA_DIR / "Raw_file"
OUTPUT_DIR = DATA_DIR / "output"

# Create output folder if it doesn't exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# FILE PATHS
# ============================================================

INPUT_FILE = RAW_DIR / "sensor_dataset_500.csv"

OUTPUT_CSV = OUTPUT_DIR / "sensor_dataset_preprocessed.csv"

OUTPUT_JSON = OUTPUT_DIR / "sensor_dataset_preprocessed.json"

# ============================================================
# LOAD DATA
# ============================================================

print("Loading dataset...")
print(f"Input file: {INPUT_FILE}")

df = pd.read_csv(INPUT_FILE)

print("\nOriginal dataset:")
print(df.head())

print("\nOriginal columns:")
print(df.columns.tolist())

# ============================================================
# REMOVE UNWANTED COLUMNS
# ============================================================

df = df.drop(
    columns=["sensor_id", "serial_number"]
)

# ============================================================
# PREPROCESS ENERGY
# ============================================================

df["energy_stored_j"] = pd.to_numeric(
    df["energy_stored_j"],
    errors="coerce"
)

# Remove rows where energy is missing
df = df.dropna(
    subset=["energy_stored_j"]
)

# Restrict energy to 1.90 - 2.10 J
df["energy_stored_j"] = df["energy_stored_j"].clip(
    lower=1.90,
    upper=2.10
)

# Round to 2 decimal places
df["energy_stored_j"] = df["energy_stored_j"].round(2)

# ============================================================
# SAVE PREPROCESSED CSV
# ============================================================

df.to_csv(
    OUTPUT_CSV,
    index=False
)

# ============================================================
# CONVERT TO JSON
# ============================================================

df.to_json(
    OUTPUT_JSON,
    orient="records",
    indent=4
)

# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n========================================")
print("PREPROCESSING COMPLETED")
print("========================================")

print("\nFinal columns:")
print(df.columns.tolist())

print("\nNumber of records:")
print(len(df))

print("\nEnergy range:")
print(
    f"{df['energy_stored_j'].min():.2f} J "
    f"to "
    f"{df['energy_stored_j'].max():.2f} J"
)

print("\nFinal dataset:")
print(df.head())

print("\nSaved files:")
print(f"CSV  : {OUTPUT_CSV}")
print(f"JSON : {OUTPUT_JSON}")