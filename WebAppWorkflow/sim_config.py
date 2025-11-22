# ----------------- Configuration File -----------------
SIM_TIME = 3600.0 * 20   # total simulation time (seconds)
ARRIVAL_RATE = 1.2      # requests per second
SEED = 12345
ARRIVAL_STREAM = 0    # stream dedicated to arrivals

# Stream assignment for each service center
SERVICE_STREAMS = {
    'A': 1,
    'B': 2,
    'P': 3,
}

# Numero di ripetizioni
NUM_REPETITIONS = 16 #128

# Time-slot (for finite-horizon simulation)
TS_STEP = 300   # 5 minutes


# Mean service times for each node/class
service_demands = {
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
    service_demands['A']['Class3'] = 0.15
    service_demands['P']['Class2'] = 0.7

if USE_POW_B:
    service_demands['B']['Class1'] = 0.4
