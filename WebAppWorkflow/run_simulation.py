import sys
import time

from sim_config import SIM_TIME, NUM_REPETITIONS, BATCH_K, BATCH_B
from src.simulator import finite_horizon_simulation, infinite_horizon_simulation
from src.sim_utils import print_line


def run_finite_horizon():
    print("\n[INFO] Avviata simulazione a orizzonte FINITO...\n")
    time.sleep(1)
    print(f"\n\n==== Finite-Horizon Simulation ===="
          f"\n* Simulation time: {SIM_TIME}"
          f"\n* Repetitions:     {NUM_REPETITIONS}")
    print_line()
    finite_horizon_simulation(SIM_TIME)
    print()
    print_line()
    time.sleep(1)
    print("[INFO] Simulazione finita.\n")

def run_infinite_horizon():
    print("\n[INFO] Avviata simulazione a orizzonte INFINITO...\n")
    time.sleep(1)
    print(f"\n\n==== Infinite-Horizon Simulation ===="
          f"\n#batch: {BATCH_K}")
    print_line()
    infinite_horizon_simulation(BATCH_K, BATCH_B)
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
