
# ============================================================
# NETWORK CONFIGURATION
# ============================================================

# Number of sensor nodes
NUM_SENSORS = 500

# Deployment area (metres)
AREA_WIDTH = 100
AREA_HEIGHT = 100

# Base Station position (metres)
BS_X = 50
BS_Y = 150

# Initial energy range comes from our preprocessed dataset
MIN_INITIAL_ENERGY = 1.90  # Joules
MAX_INITIAL_ENERGY = 2.10  # Joules

# Data transmission
PACKET_SIZE = 4000  # bits per sensor reading packet

# Radio Energy Model
E_ELEC = 50e-9       # Joules per bit
E_AMP = 100e-12      # Joules per bit per metre squared
E_DA = 5e-9          # Joules per bit for data aggregation

# Clustering
MIN_CLUSTERS = 5
MAX_CLUSTERS = 25
DEFAULT_CLUSTERS = 25

# Simulation
NUM_ROUNDS = 15000

# Reproducibility
RANDOM_SEED = 42


