
"""Efficient, energy-aware clustering and Cluster Head selection."""

import math
import numpy as np
from sklearn.cluster import KMeans

from src.config import BS_X, BS_Y, DEFAULT_CLUSTERS
from src.energy import (
    transmission_energy,
    reception_energy,
    aggregation_energy,
)


def distance(a, b):
    """Euclidean distance between two sensors."""
    return math.hypot(a.x - b.x, a.y - b.y)


def distance_to_bs(sensor):
    """Distance from a sensor to the Base Station."""
    return math.hypot(sensor.x - BS_X, sensor.y - BS_Y)


def _alive_sensors(sensors):
    """Return alive sensors with positive residual energy."""
    return [s for s in sensors if s.alive and s.energy > 0]


def form_clusters(sensors, cluster_heads):
    """Assign each alive sensor to its nearest CH."""
    alive = _alive_sensors(sensors)
    heads = _alive_sensors(cluster_heads)

    if not alive or not heads:
        return {}

    clusters = {head.id: [] for head in heads}
    head_ids = {head.id for head in heads}

    for sensor in alive:
        if sensor.id in head_ids:
            clusters[sensor.id].append(sensor)
            continue

        nearest = min(
            heads,
            key=lambda head: (distance(sensor, head), head.id),
        )
        clusters[nearest.id].append(sensor)

    return clusters


def estimate_cluster_energy(cluster_head, members):
    """Estimate one-round cluster communication energy in joules."""
    member_tx = 0.0
    ch_rx = 0.0

    for member in members:
        if member.id == cluster_head.id:
            continue

        member_tx += transmission_energy(distance(member, cluster_head))
        ch_rx += reception_energy()

    # One aggregation operation per reading, including the CH's reading.
    aggregation = len(members) * aggregation_energy()
    ch_to_bs = transmission_energy(distance_to_bs(cluster_head))

    return {
        "member_tx": member_tx,
        "ch_rx": ch_rx,
        "aggregation": aggregation,
        "ch_to_bs": ch_to_bs,
        "total": member_tx + ch_rx + aggregation + ch_to_bs,
        "ch_burden": ch_rx + aggregation + ch_to_bs,
    }


def _choose_head(members, previous_head_ids):
    """
    Choose the CH that minimises estimated cluster communication energy.
    Use battery burden and rotation history to break ties.
    """
    best_head = None
    best_objective = None

    for candidate in members:
        costs = estimate_cluster_energy(candidate, members)
        battery_fraction = (
            costs["ch_burden"] / candidate.energy
            if candidate.energy > 0
            else float("inf")
        )

        # Energy first; battery burden and rotation resolve near-ties.
        objective = (
            round(costs["total"], 12),
            round(battery_fraction, 12),
            candidate.id in previous_head_ids,
            candidate.id,
        )

        if best_objective is None or objective < best_objective:
            best_objective = objective
            best_head = candidate

    return best_head


def select_cluster_heads(
    sensors,
    k=DEFAULT_CLUSTERS,
    previous_head_ids=None,
):
    """
    Form spatial clusters with K-means and select one energy-aware CH
    from each cluster.

    This is a heuristic, not a guarantee of global optimality.
    It does not consume battery energy.
    """
    alive = _alive_sensors(sensors)

    if not alive:
        return []

    k = int(k)
    if not 1 <= k <= len(alive):
        raise ValueError(
            f"k must be between 1 and {len(alive)}; received {k}."
        )

    previous_head_ids = set(previous_head_ids or [])

    positions = np.array([[s.x, s.y] for s in alive], dtype=float)

    # Deterministic spatial grouping for reproducible comparisons.
    model = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10,
        algorithm="lloyd",
    )
    labels = model.fit_predict(positions)

    selected = []

    for cluster_label in range(k):
        members = [
            sensor
            for sensor, label in zip(alive, labels)
            if label == cluster_label
        ]

        if not members:
            continue

        head = _choose_head(members, previous_head_ids)
        selected.append(head)

    return selected


def estimate_network_energy(sensors, cluster_heads):
    """Estimate total clustered communication energy for one round."""
    clusters = form_clusters(sensors, cluster_heads)
    heads_by_id = {head.id: head for head in cluster_heads}

    return sum(
        estimate_cluster_energy(heads_by_id[head_id], members)["total"]
        for head_id, members in clusters.items()
    )


def evaluate_cluster_counts(sensors, k_values=None):
    """
    Estimate first-round energy for candidate K values.

    Full multi-round simulation is required to choose K using FND, LND,
    and energy consumption.
    """
    if k_values is None:
        # Include every feasible K from 1 to the number of alive sensors.
        k_values = range(1, len(_alive_sensors(sensors)) + 1)

    results = []

    for k in k_values:
        heads = select_cluster_heads(sensors, k=k)
        clusters = form_clusters(sensors, heads)

        results.append({
            "k": len(heads),
            "estimated_energy_j": estimate_network_energy(sensors, heads),
            "cluster_sizes": {
                head_id: len(members)
                for head_id, members in clusters.items()
            },
        })

    return results
