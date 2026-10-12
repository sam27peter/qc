
"""Round-by-round WSN simulation: direct vs clustered communication."""

from copy import deepcopy

from src.config import NUM_ROUNDS, DEFAULT_CLUSTERS
from src.sensor import create_sensors
from src.energy import (
    transmission_energy,
    reception_energy,
    aggregation_energy,
    consume_energy,
    total_residual_energy,
    count_alive_sensors,
)
from src.clustering import (
    select_cluster_heads,
    form_clusters,
    distance,
    distance_to_bs,
)


def _initial_history(sensors):
    """Create a round-zero snapshot and metric history."""
    return {
        "round": [0],
        "alive_nodes": [count_alive_sensors(sensors)],
        "residual_energy_j": [total_residual_energy(sensors)],
        "energy_consumed_j": [0.0],
        "fnd": None,
        "lnd": None,
    }


def _record_round(history, sensors, round_number, energy_used):
    """Record network statistics after a round."""
    alive = count_alive_sensors(sensors)

    history["round"].append(round_number)
    history["alive_nodes"].append(alive)
    history["residual_energy_j"].append(
        total_residual_energy(sensors)
    )
    history["energy_consumed_j"].append(energy_used)

    if history["fnd"] is None and alive < len(sensors):
        history["fnd"] = round_number

    if history["lnd"] is None and alive == 0:
        history["lnd"] = round_number


def simulate_direct(sensors=None, max_rounds=NUM_ROUNDS):
    """Every alive sensor sends one packet directly to the BS."""
    if sensors is None:
        sensors = create_sensors()

    nodes = deepcopy(sensors)
    history = _initial_history(nodes)

    for round_number in range(1, max_rounds + 1):
        if count_alive_sensors(nodes) == 0:
            break

        round_energy = 0.0

        for sensor in nodes:
            if not sensor.alive:
                continue

            cost = transmission_energy(distance_to_bs(sensor))
            consume_energy(sensor, cost)
            round_energy += cost

        _record_round(history, nodes, round_number, round_energy)

    history["method"] = "direct"
    history["final_sensors"] = nodes
    return history


def simulate_clustered(
    sensors=None,
    k=DEFAULT_CLUSTERS,
    max_rounds=NUM_ROUNDS,
    mode="dynamic",
):
    """Simulate clustered communication with dynamic or fixed CHs.

    Deployment membership is formed once. Dynamic mode re-elects an alive
    CH in every cluster each round; static mode keeps the original CHs. If a
    fixed CH dies, its surviving members transmit directly to the BS.
    """
    if sensors is None:
        sensors = create_sensors()
    if int(k) < 1:
        raise ValueError("k must be at least 1.")
    if mode not in {"dynamic", "static"}:
        raise ValueError("mode must be 'dynamic' or 'static'.")

    nodes = deepcopy(sensors)
    history = _initial_history(nodes)
    previous_head_ids = set()
    # Deployment clusters are formed once. Dynamic mode reselects the CH
    # within each surviving cluster every round; static mode fixes the initial
    # CH identities. This captures CH rotation without refitting K-means for
    # every round.
    initial_heads = select_cluster_heads(
        nodes, k=min(int(k), count_alive_sensors(nodes))
    )
    deployment_clusters = form_clusters(nodes, initial_heads)
    static_heads = list(initial_heads)

    for round_number in range(1, max_rounds + 1):
        if count_alive_sensors(nodes) == 0:
            break
        clusters = deployment_clusters
        if mode == "dynamic":
            heads = []
            for members in clusters.values():
                alive_members = [m for m in members if m.alive and m.energy > 0]
                if alive_members:
                    # Rotate the role by choosing the least-used living
                    # candidate first. Among equally used candidates, prefer
                    # distance-efficient positions, then higher residual
                    # energy. The distance score balances cluster-centre
                    # proximity with the candidate's link to the BS.
                    cx = sum(m.x for m in alive_members) / len(alive_members)
                    cy = sum(m.y for m in alive_members) / len(alive_members)
                    selected = min(alive_members, key=lambda candidate: (
                        candidate.ch_count,
                        candidate.id in previous_head_ids,
                        (candidate.x - cx) ** 2 + (candidate.y - cy) ** 2
                        + 0.05 * distance_to_bs(candidate) ** 2,
                        -candidate.energy,
                        candidate.id,
                    ))
                    heads.append(selected)
        else:
            heads = [h for h in static_heads if h.alive and h.energy > 0]

        round_energy = 0.0
        head_by_id = {h.id: h for h in heads}
        for deployment_head_id, members in clusters.items():
            # Dynamic heads are selected from the original spatial cluster;
            # associate the selected head with that cluster by membership.
            if mode == "dynamic":
                alive_members = [m for m in members if m.alive and m.energy > 0]
                head = next((candidate for candidate in heads
                             if candidate in alive_members), None)
            else:
                head = head_by_id.get(deployment_head_id)
            active_members = [m for m in members if m.alive and m.energy > 0]
            if not active_members:
                continue
            if head is None or not head.alive:
                # A fixed static CH has failed: its cluster falls back to
                # direct-to-BS communication. Dynamic mode always chooses an
                # alive member as its CH.
                for member in active_members:
                    cost = transmission_energy(distance_to_bs(member))
                    consume_energy(member, cost)
                    round_energy += cost
                continue

            delivered = []
            for member in active_members:
                if member.id == head.id:
                    continue
                tx_cost = transmission_energy(distance(member, head))
                consume_energy(member, tx_cost)
                round_energy += tx_cost
                if member.alive:
                    rx_cost = reception_energy()
                    consume_energy(head, rx_cost)
                    round_energy += rx_cost
                    if head.alive:
                        delivered.append(member)

            if head.alive:
                aggregate_cost = (len(delivered) + 1) * aggregation_energy()
                consume_energy(head, aggregate_cost)
                round_energy += aggregate_cost
            if head.alive:
                bs_cost = transmission_energy(distance_to_bs(head))
                consume_energy(head, bs_cost)
                round_energy += bs_cost
                head.ch_count += 1
                head.last_ch_round = round_number

        previous_head_ids = {h.id for h in heads}
        _record_round(history, nodes, round_number, round_energy)

    history["method"] = "clustered_" + mode
    history["mode"] = mode
    history["k"] = int(k)
    history["final_sensors"] = nodes
    return history

def compare_methods(sensors=None, k=DEFAULT_CLUSTERS,
                    max_rounds=NUM_ROUNDS):
    """Compare both methods from identical initial sensor states."""
    if sensors is None:
        sensors = create_sensors()

    return {
        "direct": simulate_direct(sensors, max_rounds=max_rounds),
        "clustered": simulate_clustered(
            sensors, k=k, max_rounds=max_rounds
        ),
    }


def print_summary(results):
    """Print the final statistics for both methods."""
    print("\n========== WSN SIMULATION RESULTS ==========")

    for name in ("direct", "clustered"):
        result = results[name]

        print(f"\nMethod: {name}")
        if name == "clustered":
            print(f"Cluster heads (K): {result['k']}")

        print(f"Rounds simulated: {result['round'][-1]}")
        print(f"Alive nodes: {result['alive_nodes'][-1]}")
        print(
            "Residual energy: "
            f"{result['residual_energy_j'][-1]:.6f} J"
        )
        print(f"First-node death (FND): {result['fnd']}")
        print(f"Last-node death (LND): {result['lnd']}")
