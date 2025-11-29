# ----------------- Configuration File -----------------
SIM_TIME = 3600 * 4  # total simulation time (seconds)
ARRIVAL_RATE = 1.2      # requests per second
SEED = 12345
ARRIVAL_STREAM = 0    # stream dedicated to arrivals

# Stream assignment for each service center
SERVICE_STREAMS = {
    'A': 1,
    'B': 2,
    'P': 3,
}


# For finite-horizon simulation
NUM_REPETITIONS = 128  # number of repetitions
TS_STEP = 60  # time-slot (in seconds)


# Batch parameters (for infinite-horizon simulation)
BATCH_K = 128
BATCH_B = 8192


# Mean service times for each node/class
SERVICE_DEMANDS = {
    'A': {
        'Class1': 0.2,
        'Class2': 0.4,
        'Class3': 0.1,
    },
    'B': {
        'Class1': 0.8,
    },
    'P': {
        'Class2': 0.4,
    }
}


# Optional switches
USE_2FA = False
USE_POW_B = False

# Apply modifications
if USE_2FA:
    SERVICE_DEMANDS['A']['Class3'] = 0.15
    SERVICE_DEMANDS['P']['Class2'] = 0.7

if USE_POW_B:
    SERVICE_DEMANDS['B']['Class1'] = 0.4


# For visits plot
PLOT_VISITS = False
