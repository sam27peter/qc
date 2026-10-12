
"""Generate Q3 WSN simulation graphs."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from src.config import BS_X, BS_Y, AREA_WIDTH, AREA_HEIGHT
from src.clustering import (
    select_cluster_heads,
    form_clusters,
    distance_to_bs,
)
from src.energy import transmission_energy


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def _save(fig, filename):
    """Save a graph and close its figure."""
    path = RESULTS_DIR / filename
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {path}")


def plot_cluster_layout(sensors, k):
    """Plot the first-round cluster layout and Base Station."""
    alive = [s for s in sensors if s.alive and s.energy > 0]
    heads = select_cluster_heads(alive, k=k)
    clusters = form_clusters(alive, heads)

    fig, ax = plt.subplots(figsize=(9, 7))

    for head_id, members in clusters.items():
        ax.scatter(
            [s.x for s in members],
            [s.y for s in members],
            s=18,
            alpha=0.75,
        )

    ax.scatter(
        [h.x for h in heads],
        [h.y for h in heads],
        marker="*",
        s=180,
        edgecolors="black",
        label="Cluster Heads",
        zorder=5,
    )
    ax.scatter(
        [BS_X],
        [BS_Y],
        marker="s",
        s=120,
        color="red",
        label="Base Station",
        zorder=6,
    )

    ax.set_title(f"WSN Cluster Layout (K={len(heads)})")
    ax.set_xlabel("X position (m)")
    ax.set_ylabel("Y position (m)")
    ax.set_xlim(0, AREA_WIDTH)
    ax.set_ylim(0, max(AREA_HEIGHT, BS_Y + 10))
    ax.grid(True, alpha=0.25)
    ax.legend()

    _save(fig, "q3_cluster_layout.png")


def plot_network_lifetime(results):
    """Compare alive sensor counts over time."""
    fig, ax = plt.subplots(figsize=(9, 6))

    for name, label in (
        ("direct", "Direct transmission"),
        ("clustered", "Clustered transmission"),
    ):
        result = results[name]
        ax.plot(
            result["round"],
            result["alive_nodes"],
            label=label,
            linewidth=2,
        )

    ax.set_title("Network Lifetime Comparison")
    ax.set_xlabel("Simulation round")
    ax.set_ylabel("Alive sensors")
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.3)
    ax.legend()

    _save(fig, "q3_network_lifetime.png")


def plot_energy_dissipation(results):
    """Compare total residual battery energy over time."""
    fig, ax = plt.subplots(figsize=(9, 6))

    for name, label in (
        ("direct", "Direct transmission"),
        ("clustered", "Clustered transmission"),
    ):
        result = results[name]
        ax.plot(
            result["round"],
            result["residual_energy_j"],
            label=label,
            linewidth=2,
        )

    ax.set_title("Network Energy Dissipation")
    ax.set_xlabel("Simulation round")
    ax.set_ylabel("Total residual energy (J)")
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.3)
    ax.legend()

    _save(fig, "q3_energy_dissipation.png")


def plot_k_optimisation(k_results):
    """Plot first-node death and last-node death against K."""
    if not k_results:
        raise ValueError("No K optimisation results supplied.")

    ks = [row["k"] for row in k_results]
    fnd = [row["fnd"] or np.nan for row in k_results]
    lnd = [row["lnd"] or np.nan for row in k_results]

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(ks, fnd, marker="o", label="First-node death (FND)")
    ax.plot(ks, lnd, marker="s", label="Last-node death (LND)")

    ax.set_title("Cluster Count Optimisation")
    ax.set_xlabel("Number of Cluster Heads (K)")
    ax.set_ylabel("Lifetime (rounds)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left")

    energy = [row.get("mean_energy_per_round_j", np.nan) for row in k_results]
    if any(np.isfinite(value) for value in energy):
        energy_ax = ax.twinx()
        energy_ax.plot(
            ks, energy, color="tab:green", marker="^", linestyle="--",
            label="Mean energy per round",
        )
        energy_ax.set_ylabel("Mean energy consumed per round (J)")
        energy_ax.legend(loc="upper right")

    _save(fig, "q3_k_optimisation.png")


def plot_static_dynamic_comparison(static_results, dynamic_results):
    """Compare static and dynamic clustering lifetime across K."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    for results, label, marker in (
        (static_results, "Static clustering", "o"),
        (dynamic_results, "Dynamic clustering", "s"),
    ):
        ks = [row["k"] for row in results]
        fnd = [row["fnd"] or np.nan for row in results]
        lnd = [row["lnd"] or np.nan for row in results]

        axes[0].plot(ks, fnd, marker=marker, label=label)
        axes[1].plot(ks, lnd, marker=marker, label=label)

    axes[0].set_title("First-Node Death")
    axes[1].set_title("Last-Node Death")

    for ax in axes:
        ax.set_xlabel("Number of Cluster Heads (K)")
        ax.set_ylabel("Rounds")
        ax.grid(True, alpha=0.3)
        ax.legend()

    fig.suptitle("Static vs Dynamic Clustering")
    _save(fig, "q3_static_dynamic_comparison.png")


def generate_all_graphs(
    sensors,
    results,
    k_results,
    static_results,
    dynamic_results,
    selected_k,
):
    """Generate and save all Q3 graph groups."""
    plot_cluster_layout(sensors, selected_k)
    plot_network_lifetime(results)
    plot_energy_dissipation(results)
    plot_k_optimisation(k_results)
    plot_static_dynamic_comparison(static_results, dynamic_results)

    print(f"\nAll Q3 graphs saved in: {RESULTS_DIR}")
