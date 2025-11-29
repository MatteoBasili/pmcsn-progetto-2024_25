import os
import matplotlib.pyplot as plt
import numpy as np

from sim_config import TS_STEP
from src.utils import RESULTS_FINITE_FOLDER


def plot_finite_metrics(folder=RESULTS_FINITE_FOLDER):
    # Prendi tutti i file .dat nella cartella
    files = [f for f in os.listdir(folder) if f.endswith(".dat")]

    if not files:
        print(f"Nessun file .dat trovato in {folder}")
        return

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
