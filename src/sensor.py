
from src.config import MIN_INITIAL_ENERGY, MAX_INITIAL_ENERGY
from src.data_loader import load_sensor_data


class Sensor:
    """Represent one sensor node in the WSN."""

    def __init__(self, sensor_id, x, y, temperature, energy):
        self.id = sensor_id
        self.x = float(x)
        self.y = float(y)
        self.temperature = float(temperature)

        self.energy = float(energy)
        self.initial_energy = float(energy)

        self.alive = True

        # Number of rounds in which this sensor was a CH
        self.ch_count = 0
        self.last_ch_round = 0

    def position(self):
        """Return the sensor's coordinates."""
        return self.x, self.y


def create_sensors():
    """Create sensor objects from the preprocessed dataset."""

    records = load_sensor_data()
    sensors = []

    for sensor_id, record in enumerate(records, start=1):
        energy = float(record["energy_stored_j"])

        if not MIN_INITIAL_ENERGY <= energy <= MAX_INITIAL_ENERGY:
            raise ValueError(
                f"Sensor {sensor_id} has invalid energy: {energy} J"
            )

        sensor = Sensor(
            sensor_id=sensor_id,
            x=record["x_position_m"],
            y=record["y_position_m"],
            temperature=record["temperature_c"],
            energy=energy,
        )

        sensors.append(sensor)

    print(f"\nCreated {len(sensors)} sensor objects.")
    print(
        f"Initial network energy: "
        f"{sum(s.energy for s in sensors):.2f} J"
    )

    return sensors
