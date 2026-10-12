# Wireless Sensor Network Clustering

A Python simulation of clustered data transmission for 500 battery-powered temperature sensors. It compares direct transmission with clustered transmission, evaluates static and dynamic cluster-head (CH) behavior, searches for a suitable cluster count, and saves plots under `results/`.

## Dataset

The sensor records used in this project are based on a dataset available on the internet. The project includes the raw and preprocessed files under `data/` so the simulation can be run locally.

## Features

- Direct-to-base-station transmission baseline.
- K-means spatial grouping and energy-aware cluster-head selection.
- Static CH runs with fixed CH assignments; a cluster falls back to direct transmission if its fixed CH dies.
- Dynamic CH rotation within deployment clusters, favoring the least-used living sensor, then distance and residual energy.
- Full lifetime simulations for every K from 5 through 25. K is selected using a weighted score of FND (35%), LND (45%), and lower mean energy consumption per round (20%).
- Plots for cluster layout, alive-node lifetime, energy dissipation, K optimization, and static-versus-dynamic lifetime.

## Simulation configuration

The defaults are defined in `src/config.py`:

- 500 sensors in a 100 m x 100 m deployment area.
- Base Station at (50 m, 150 m).
- Initial sensor energy from 1.90 J to 2.10 J.
- 4,000-bit packet size.
- Radio model: `E_tx = L(E_elec + E_amp d^2)`, `E_rx = L E_elec`, and aggregation cost `E_DA = L E_DA`.

The lifetime is measured in simulation rounds. FND is the first round in which a sensor dies; LND is the round in which all sensors have died.

## Setup

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
```

Activate the environment, then install dependencies:

```bash
pip install -r requirements.txt
```

## Run

From the project root:

```bash
python main.py
```

The workflow runs the K sweep, direct and clustered comparisons, static-versus-dynamic comparisons, and saves figures in `results/`.

To rebuild the preprocessed dataset from the included raw CSV:

```bash
python src/preprocessing.py
```

## Project structure

```text
qc/
|-- data/
|   |-- Raw_file/
|   `-- output/
|-- results/
|-- src/
|   |-- clustering.py
|   |-- config.py
|   |-- data_loader.py
|   |-- energy.py
|   |-- preprocessing.py
|   |-- sensor.py
|   |-- simulation.py
|   `-- visualization.py
|-- main.py
|-- requirements.txt
`-- README.md
```
