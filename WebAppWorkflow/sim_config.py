# ============================================================
#   CONFIGURAZIONE GENERALE DEL MODELLO
# ============================================================

# Seleziona lo scenario:
#   "light_1FA"
#   "light_2FA"
#   "heavy_1FA"
#   "heavy_1FA_newServerB"
SCENARIO = "light_1FA"

# Imposta a 'True' per visualizzare le visite ai server
PLOT_VISITS = False

# Imposta a 'True' per la ricerca del batch size ottimale
SEARCH_BATCH_SIZE = False


# ------------------------------------------------------------
# PARAMETRI BASE
# ------------------------------------------------------------
SEED = 12345
ARRIVAL_STREAM = 0    # stream dedicato agli arrivi

# Stream per ogni server
SERVICE_STREAMS = {
    'A': 1,
    'B': 2,
    'P': 3,
}

# Per la simulazione a orizzonte finito
if PLOT_VISITS:
    SIM_TIME = 12  # secondi
    NUM_REPETITIONS = 1
else:
    SIM_TIME = 3600 * 4
    NUM_REPETITIONS = 128

TS_STEP = 60  # time-slot (in secondi)


# Parametri Batch Means (per la simulazione a orizzonte infinito)
BATCH_K = 128

if SEARCH_BATCH_SIZE:
    B_VALUES = (4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768)
    BATCH_B = None
else:
    B_VALUES = None
    if SCENARIO == "light_1FA":
        BATCH_B = 8192
    elif SCENARIO == "light_2FA":
        BATCH_B = 8192
    elif SCENARIO == "heavy_1FA":
        BATCH_B = 8192
    elif SCENARIO == "heavy_1FA_newServerB":
        BATCH_B = 32768
    else:
        BATCH_B = None



# ============================================================
#   SERVICE DEMANDS BASE (scenario: LIGHT, 1 FACTOR)
# ============================================================

BASE_SERVICE_DEMANDS = {
    'A': {   # 3 visite: Class1, Class2, Class3
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


# ============================================================
#   MODIFICHE PER AUTENTICAZIONE A 2 FATTORI (2FA / SCA)
# ============================================================

SCA_MODIFICATIONS = {
    ('A', 'Class3'): 0.15,   # terza visita server A
    ('P', 'Class2'): 0.7,    # server pagamenti
}


# ============================================================
#   SCALING SERVER B (nuovo server B = 2× più veloce)
# ============================================================
NEW_SERVER_B = {
    ('B', 'Class1'): 0.4
}


# ============================================================
#   ARRIVAL RATES PER GLI SCENARI
# ============================================================

ARRIVAL_RATES = {
    "light": 1.2,    # circa 4300 req/h
    "heavy": 1.4,    # +15% = ~5000 req/h
}


# ============================================================
#   COSTRUZIONE DELLO SCENARIO
# ============================================================

# Copia dei service demands base
import copy
SERVICE_DEMANDS = copy.deepcopy(BASE_SERVICE_DEMANDS)

# ------------------------------------------------------------
# 1) LIGHT WORKLOAD, 1 FACTOR
# ------------------------------------------------------------
if SCENARIO == "light_1FA":
    ARRIVAL_RATE = ARRIVAL_RATES["light"]

# ------------------------------------------------------------
# 2) LIGHT WORKLOAD + AUTENTICAZIONE A 2 FATTORI
# ------------------------------------------------------------
elif SCENARIO == "light_2FA":
    ARRIVAL_RATE = ARRIVAL_RATES["light"]
    for (node, cls), value in SCA_MODIFICATIONS.items():
        SERVICE_DEMANDS[node][cls] = value

# ------------------------------------------------------------
# 3) HEAVY WORKLOAD (stessi tempi di servizio)
# ------------------------------------------------------------
elif SCENARIO == "heavy_1FA":
    ARRIVAL_RATE = ARRIVAL_RATES["heavy"]

# ------------------------------------------------------------
# 4) HEAVY WORKLOAD + NUOVO SERVER B (2× più veloce)
# ------------------------------------------------------------
elif SCENARIO == "heavy_1FA_newServerB":
    ARRIVAL_RATE = ARRIVAL_RATES["heavy"]
    for (node, cls), value in NEW_SERVER_B.items():
        SERVICE_DEMANDS[node][cls] = value

else:
    raise ValueError(f"Scenario sconosciuto: {SCENARIO}")
