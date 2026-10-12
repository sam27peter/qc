
import math

from src.config import PACKET_SIZE, E_ELEC, E_AMP, E_DA


def distance_between(sensor_a, sensor_b):
    """Calculate the Euclidean distance between two sensors."""
    return math.hypot(
        sensor_a.x - sensor_b.x,
        sensor_a.y - sensor_b.y,
    )


def distance_to_base_station(sensor):
    """Calculate the distance from a sensor to the Base Station."""
    from src.config import BS_X, BS_Y

    return math.hypot(
        sensor.x - BS_X,
        sensor.y - BS_Y,
    )


def transmission_energy(distance, packet_size=PACKET_SIZE):
    """
    Energy needed to transmit a packet.

    E_TX = L * (E_ELEC + E_AMP * distance^2)
    """
    if distance < 0:
        raise ValueError("Distance cannot be negative.")

    if packet_size < 0:
        raise ValueError("Packet size cannot be negative.")

    return packet_size * (
        E_ELEC + E_AMP * distance**2
    )


def reception_energy(packet_size=PACKET_SIZE):
    """Energy needed to receive a packet."""
    if packet_size < 0:
        raise ValueError("Packet size cannot be negative.")

    return packet_size * E_ELEC


def aggregation_energy(packet_size=PACKET_SIZE):
    """Energy needed to aggregate a packet's worth of data."""
    if packet_size < 0:
        raise ValueError("Packet size cannot be negative.")

    return packet_size * E_DA


def consume_energy(sensor, energy_used):
    """
    Deduct energy from a sensor.

    A sensor cannot have negative remaining energy. Once its energy
    reaches zero, it is marked dead.
    """
    if energy_used < 0:
        raise ValueError("Energy usage cannot be negative.")

    if not sensor.alive:
        return sensor.energy

    sensor.energy = max(0.0, sensor.energy - energy_used)

    if sensor.energy <= 0:
        sensor.alive = False

    return sensor.energy


def total_residual_energy(sensors):
    """Return the total remaining battery energy of all sensors."""
    return sum(sensor.energy for sensor in sensors)


def count_alive_sensors(sensors):
    """Return the number of sensors that are still alive."""
    return sum(sensor.alive for sensor in sensors)
