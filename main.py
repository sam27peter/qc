
"""Main runner for the Q3 Wireless Sensor Network project."""

from copy import deepcopy

from src.config import NUM_ROUNDS, DEFAULT_CLUSTERS, MIN_CLUSTERS, MAX_CLUSTERS
from src.sensor import create_sensors
from src.simulation import (
    simulate_direct,
    simulate_clustered,
    print_summary,
)
from src.clustering import select_cluster_heads, form_clusters
from src.energy import count_alive_sensors, total_residual_energy
from src.visualization import generate_all_graphs


def find_best_k(sensors):
    """Choose K by measured network lifetime and residual energy.

    Every candidate is evaluated with a complete dynamic-clustering
    simulation, so the selected K is based on FND/LND and consumed energy.
    """
    print("\nSelecting K from full lifetime simulations...")
    alive = count_alive_sensors(sensors)
    candidates = [k for k in range(MIN_CLUSTERS, MAX_CLUSTERS + 1) if k <= alive]
    if DEFAULT_CLUSTERS <= alive and DEFAULT_CLUSTERS not in candidates:
        candidates.append(DEFAULT_CLUSTERS)
    if not candidates:
        candidates = [alive]

    results = []
    for k in sorted(set(candidates)):
        print(f"  Simulating dynamic clustering, K={k}...")
        result = simulate_clustered(
            sensors=deepcopy(sensors), k=k, max_rounds=NUM_ROUNDS,
            mode="dynamic",
        )
        results.append({
            "k": k, "fnd": result["fnd"], "lnd": result["lnd"],
            "rounds": result["round"][-1],
            "residual_energy_j": result["residual_energy_j"][-1],
            "energy_consumed_j": sum(result["energy_consumed_j"]),
            "mean_energy_per_round_j": (
                sum(result["energy_consumed_j"]) / max(1, result["round"][-1])
            ),
        })
        print(f"    FND={result['fnd']}, LND={result['lnd']}, "
              f"mean energy/round={results[-1]['mean_energy_per_round_j']:.4f} J")

    max_fnd = max(row["fnd"] or row["rounds"] for row in results) or 1
    max_lnd = max(row["lnd"] or row["rounds"] for row in results) or 1
    max_mean_energy = max(row["mean_energy_per_round_j"] for row in results) or 1
    for row in results:
        # Reward longer FND/LND and lower per-round energy use.
        row["optimization_score"] = (
            0.35 * (row["fnd"] or row["rounds"]) / max_fnd
            + 0.45 * (row["lnd"] or row["rounds"]) / max_lnd
            + 0.20 * (1 - row["mean_energy_per_round_j"] / max_mean_energy)
        )

    best = max(results, key=lambda row: (
        row["optimization_score"], row["lnd"] or row["rounds"], -row["k"]
    ))
    print(f"\nSelected K from simulated lifetime: {best['k']}")
    return best["k"], results


def run_lifetime_sweep(sensors, k_values, mode):
    """Run full lifetime simulations for each K and clustering mode."""
    rows = []
    for k in k_values:
        print(f"  {mode.capitalize()} clustering, K={k}...")
        result = simulate_clustered(
            sensors=deepcopy(sensors), k=k, max_rounds=NUM_ROUNDS,
            mode=mode,
        )
        rows.append({
            "k": k, "fnd": result["fnd"], "lnd": result["lnd"],
            "rounds": result["round"][-1],
            "residual_energy_j": result["residual_energy_j"][-1],
            "energy_consumed_j": sum(result["energy_consumed_j"]),
            "mean_energy_per_round_j": (
                sum(result["energy_consumed_j"]) / max(1, result["round"][-1])
            ),
        })
    return rows

def main():
    print("=" * 60)
    print("WIRELESS SENSOR NETWORK: Q3 SIMULATION")
    print("=" * 60)

    sensors = create_sensors()
    initial_energy = total_residual_energy(sensors)

    # 1. Select K using estimated communication cost.
    selected_k, k_energy_results = find_best_k(sensors)

    # 2. Compare direct transmission against clustered communication.
    print("\nRunning direct-transmission simulation...")
    direct = simulate_direct(
        sensors=deepcopy(sensors),
        max_rounds=NUM_ROUNDS,
    )

    print("\nRunning clustered-transmission simulation...")
    clustered = simulate_clustered(
        sensors=deepcopy(sensors),
        k=selected_k,
        max_rounds=NUM_ROUNDS,
        mode="dynamic",
    )

    comparison = {
        "direct": direct,
        "clustered": clustered,
    }
    print_summary(comparison)

    # 3. Compare truly fixed CH/cluster assignments with per-round dynamic
    # clustering across the same K values.
    sweep_ks = sorted(set(row["k"] for row in k_energy_results))
    print("\nRunning static/dynamic lifetime comparison...")
    dynamic_results = k_energy_results
    static_results = run_lifetime_sweep(sensors, sweep_ks, "static")
    print("\nStatic vs dynamic lifetime (FND / LND):")
    for static, dynamic in zip(static_results, dynamic_results):
        print(f"  K={static['k']:>2}: static "
              f"{static['fnd']} / {static['lnd']}; dynamic "
              f"{dynamic['fnd']} / {dynamic['lnd']}")

    # 4. K optimisation uses measured dynamic FND/LND and energy per round.
    k_lifetime_results = dynamic_results

    # 5. Generate all figures.
    print("\nGenerating graphs...")
    generate_all_graphs(
        sensors=sensors,
        results=comparison,
        k_results=k_lifetime_results,
        static_results=static_results,
        dynamic_results=dynamic_results,
        selected_k=selected_k,
    )

    print("\n" + "=" * 60)
    print("SIMULATION COMPLETE")
    print(f"Initial network energy: {initial_energy:.3f} J")
    print(f"Selected cluster count: {selected_k}")
    print("Check the results/ folder for the generated graphs.")
    print("=" * 60)


if __name__ == "__main__":
    main()
