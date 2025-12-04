import os
import matplotlib.pyplot as plt
import numpy as np


SCENARIO = "light_1FA"
STEP = 4  # per i tick

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FOLDER = os.path.join(BASE_DIR, "..", "results", "infinite")

def plot_infinite_rt_with_qos(folder, rt_file):
    path = os.path.join(folder, rt_file)

    with open(path, "r") as f:
        rt_values = [float(line.strip()) for line in f.readlines()]

    x = np.arange(1, len(rt_values) + 1)

    # Calcolo della media del tempo di risposta
    rt_mean = float(np.mean(rt_values))

    plt.figure(figsize=(9, 4.2))
    plt.plot(x, rt_values, linestyle='-', linewidth=2, color='tab:blue', label="RT")

    plt.xlabel("Batch", labelpad=10)
    plt.ylabel("Tempo di risposta RT [s]", labelpad=15)
    plt.title("Tempo di Risposta del Sistema (RT) per batch",
              fontweight='bold', fontsize=14, pad=18)

    # Tick ogni 'step'
    plt.xticks(x[::STEP])

    qos = 30
    plt.axhline(qos, color='red', linestyle='--', linewidth=1.8,
                label="QoS = 30 s")

    # Media del tempo di risposta
    plt.axhline(rt_mean, color='tab:blue', linestyle='--', linewidth=1.8,
                label=f"Media RT = {rt_mean:.2f} s")

    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_infinite_metrics(folder=RESULTS_FOLDER):
    # Prendi tutti i file .dat nella cartella
    files = [f for f in os.listdir(folder) if f.endswith(f"{SCENARIO}.dat")]

    if not files:
        print(f"Nessun file .dat trovato in {folder}")
        return

    # ---------------------------------------------------------
    # Grafico speciale per la RT del sistema nel primo scenario
    # ---------------------------------------------------------
    rt_file = f"RT_{SCENARIO}.dat"
    if rt_file in files:
        # QoS SOLO per lo scenario light_1FA
        if SCENARIO == "light_1FA":
            plot_infinite_rt_with_qos(folder, rt_file)
    else:
        print("\nNessun file RT.dat trovato: impossibile generare il grafico RT.\n")

    # Disegna tutti gli altri grafici
    for file in files:
        path = os.path.join(folder, file)

        # Leggi i valori dal file
        with open(path, "r") as f:
            values = [float(line.strip()) for line in f.readlines()]

        # Asse x: batch indices (1-based)
        x = np.arange(1, len(values) + 1)

        # Calcolo della media
        mean = float(np.mean(values))

        # Titolo ed etichetta della metrica dal nome file
        metric_name = os.path.splitext(file)[0]

        plt.figure(figsize=(8, 4))
        plt.plot(x, values, linestyle='-', color='tab:blue')
        plt.xlabel("Batch", labelpad=10)
        plt.ylabel(metric_name, labelpad=15)
        plt.title(f"{metric_name} per batch", fontweight='bold', fontsize=14, pad=18)

        # Media
        plt.axhline(mean, color='tab:blue', linestyle='--', linewidth=1.8,
                    label=f"Media = {mean:.2f} s")

        # Mostra un tick ogni 'step' batch
        plt.xticks(x[::STEP])
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    plot_infinite_metrics()
