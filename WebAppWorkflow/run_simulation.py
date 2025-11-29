import sys
import time

from sim_config import SIM_TIME, NUM_REPETITIONS, BATCH_K, BATCH_B, PLOT_VISITS
from src.simulator import finite_horizon_simulation, infinite_horizon_simulation, find_batch_b
from src.utils import print_line


def run_finite_horizon():
    print("\n[INFO] Avviata simulazione a orizzonte FINITO...\n")
    sim_time = SIM_TIME
    num_repetitions = NUM_REPETITIONS

    #########################################
    # Per il plot della sequenza delle visite
    if PLOT_VISITS:
        sim_time = 12  # secondi
        num_repetitions = 1
    #########################################

    time.sleep(1)
    print(f"\n\n==== Finite-Horizon Simulation ===="
          f"\n* Simulation time: {sim_time}"
          f"\n* Repetitions:     {num_repetitions}")
    print_line()

    finite_horizon_simulation(sim_time, num_repetitions)
    print()
    print_line()
    time.sleep(1)
    print("[INFO] Simulazione finita.\n")
    print_line()
    print()
    time.sleep(1)

def run_infinite_horizon():
    print("\n[INFO] Avviata simulazione a orizzonte INFINITO...\n")
    time.sleep(1)
    '''
    print(f"\n\n==== Infinite-Horizon Simulation ===="
          f"\n#batch: {BATCH_K}")
    print_line()
    infinite_horizon_simulation(BATCH_K, BATCH_B)
    '''
    find_batch_b(k=BATCH_K)
    print()
    print_line()
    time.sleep(1)
    print("[INFO] Simulazione finita.\n")


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
