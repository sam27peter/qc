
import json
from pathlib import Path

from src.config import NUM_SENSORS


# ============================================================
# FILE PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "output"
    / "sensor_dataset_preprocessed.json"
)


# ============================================================
# LOAD SENSOR DATA
# ============================================================

def load_sensor_data():
    """Load and validate the preprocessed sensor dataset."""

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}\n"
            "Run python src/preprocessing.py first."
        )

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Expected a JSON list of sensor records.")

    if len(data) != NUM_SENSORS:
        raise ValueError(
            f"Expected {NUM_SENSORS} sensors, "
            f"but found {len(data)}."
        )

    required_columns = {
        "x_position_m",
        "y_position_m",
        "temperature_c",
        "energy_stored_j",
    }

    for index, record in enumerate(data):
        missing = required_columns - record.keys()

        if missing:
            raise ValueError(
                f"Sensor record {index + 1} is missing: "
                f"{sorted(missing)}"
            )

        for column in required_columns:
            if record[column] is None:
                raise ValueError(
                    f"Missing value in record {index + 1}: {column}"
                )

        energy = float(record["energy_stored_j"])

        if not 1.90 <= energy <= 2.10:
            raise ValueError(
                f"Invalid energy for record {index + 1}: {energy} J"
            )

    print("Dataset loaded successfully.")
    print(f"Sensor records: {len(data)}")
    print(f"Data source: {DATA_FILE}")

    return data
