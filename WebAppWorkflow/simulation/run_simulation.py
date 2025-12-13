import sys
import time

from sim_config import SCENARIO, SIM_TIME, NUM_REPETITIONS, BATCH_K, SEARCH_BATCH_SIZE, BATCH_B, B_VALUES, ARRIVAL_RATE, \
    SEARCH_THR_BOUND
from src.simulator import finite_horizon_simulation, infinite_horizon_simulation, find_batch_b, \
    compute_throughput_vs_lambda
from src.utils import print_line, close_simulation


def run_finite_horizon():
    print("\n[INFO] Avviata simulazione a orizzonte FINITO...\n")
    scenario = SCENARIO
    sim_time = SIM_TIME
    num_repetitions = NUM_REPETITIONS

    time.sleep(1)
    print(f"\n\n==== Finite-Horizon Simulation ===="
          f"\n*  Scenario:        {scenario}"
          f"\n*  Simulation time: {sim_time}"
          f"\n*  Repetitions:     {num_repetitions}")
    print_line()

    finite_horizon_simulation(sim_time, num_repetitions)

    close_simulation()

def run_infinite_horizon():
    print("\n[INFO] Avviata simulazione a orizzonte INFINITO...\n")
    time.sleep(1)

    if SEARCH_BATCH_SIZE:
        print("\n==== Ricerca Batch Size Ottimale ====")
        print(f"*  Scenario: {SCENARIO}")
        print(f"*  # Batch: {BATCH_K}")
        print("*  Valori testati di b:", B_VALUES)
        print_line()

        find_batch_b(BATCH_K, B_VALUES)
    elif SEARCH_THR_BOUND:
        if SCENARIO == "light_1FA" or SCENARIO == "heavy_1FA":
            scenario = "1FA"
        elif SCENARIO == "light_2FA":
            scenario = "2FA"
        else:
            scenario = "1FA New B"
        print(f"\n\n==== Ricerca del Throughput Bound ===="
              f"\n*  Scenario: {scenario}")
        print_line()

        compute_throughput_vs_lambda(scenario)
    else:
        print(f"\n\n==== Infinite-Horizon Simulation ===="
              f"\n*  Scenario: {SCENARIO}"
              f"\n*  # Batch: {BATCH_K}"
              f"\n*  Batch size: {BATCH_B}")
        print_line()

        infinite_horizon_simulation(BATCH_K, BATCH_B, ARRIVAL_RATE)

    close_simulation()

def main_menu():
    while True:
        print("\n===== MENU SIMULAZIONE E-COMMERCE =====")
        print("1. Simulazione a orizzonte finito")
        print("2. Simulazione a orizzonte infinito")
        print("3. Esci")

        choice = input("Seleziona un'opzione (1-3): ").strip()

        if choice == "1":
            run_finite_horizon()
        elif choice == "2":
            run_infinite_horizon()
        elif choice == "3":
            print("Uscita dal programma. Arrivederci!")
            sys.exit(0)
        else:
            print("[ERRORE] Opzione non valida. Inserisci 1, 2 o 3.")


if __name__ == "__main__":
    main_menu()
