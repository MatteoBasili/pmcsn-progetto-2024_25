import os

import matplotlib.pyplot as plt
import numpy as np


SCENARIO = "heavy_1FA_newServerB"
TS_STEP = 60

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FOLDER = os.path.join(BASE_DIR, "..", "results", "finite")

def plot_finite_rt_with_qos(folder, rt_file):
    path = os.path.join(folder, rt_file)
    with open(path, "r") as f:
        rt_values = [float(line.strip()) for line in f.readlines()]

    x = np.arange(len(rt_values)) * TS_STEP

    plt.figure(figsize=(9, 4.2))
    plt.plot(x, rt_values, linestyle='-', linewidth=2, color='tab:blue', label="RT")

    plt.xlabel("Tempo [s]", labelpad=10)
    plt.ylabel("Tempo di risposta RT [s]", labelpad=15)
    plt.title("Tempo di Risposta del Sistema (RT) nel tempo",
              fontweight='bold', fontsize=14, pad=18)

    qos = 30
    plt.axhline(qos, color='red', linestyle='--', linewidth=1.8,
                label="QoS = 30 s")

    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_finite_metrics(folder=RESULTS_FOLDER):
    # Prendi tutti i file .dat nella cartella
    files = [f for f in os.listdir(folder) if f.endswith(f"{SCENARIO}.dat")]

    if not files:
        print(f"Nessun file .dat trovato in {folder}")
        return

    # -----------------------------------------------------
    # Grafico speciale per RT con QoS per il primo scenario
    # -----------------------------------------------------
    rt_file = f"RT_{SCENARIO}.dat"
    if rt_file in files:
        # QoS SOLO per light_1FA
        if SCENARIO == "light_1FA":
            plot_finite_rt_with_qos(folder, rt_file)
    else:
        print("\nNessun file RT.dat trovato: impossibile generare il grafico RT.\n")

    # Disegna tutti gli altri grafici
    for file in files:
        path = os.path.join(folder, file)

        # Leggi i valori dal file
        with open(path, "r") as f:
            values = [float(line.strip()) for line in f.readlines()]

        # Creiamo un array per l'asse x (tempo)
        x = np.arange(len(values)) * TS_STEP

        # Titolo ed etichetta della metrica dal nome file
        metric_name = os.path.splitext(file)[0]

        plt.figure(figsize=(8, 4))
        plt.plot(x, values, linestyle='-', color='tab:blue')
        plt.xlabel(
            "Tempo [s]",
            labelpad=10
        )
        plt.ylabel(
            metric_name,
            labelpad=15
        )
        plt.title(
            f"{metric_name} nel tempo",
            fontweight='bold',
            fontsize=14,
            pad=18
        )
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    plot_finite_metrics()
