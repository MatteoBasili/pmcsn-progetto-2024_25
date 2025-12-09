import os
import numpy as np
import matplotlib.pyplot as plt

SCENARIO_BASE = "light_1FA"
SCENARIO_SCA = "light_2FA"
SCENARIO_HEAVY_NEW_B = "heavy_1FA_newServerB"

BATCH_STEP = 4      # tick asse x
QOS = 30            # soglia QoS per RT

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FOLDER = os.path.join(BASE_DIR, "..", "results", "infinite")

def load_metric(metric_name, scenario):
    filename = f"{metric_name}_{scenario}.dat"
    path = os.path.join(RESULTS_FOLDER, filename)

    if not os.path.exists(path):
        raise FileNotFoundError(f"File non trovato: {path}")

    with open(path, "r") as f:
        values = [float(line.strip()) for line in f.readlines()]

    return np.array(values)

def plot_system_response_time(scenario, ci_minus=None, ci_plus=None):
    rt_system = load_metric("RT", scenario)

    x = np.arange(1, len(rt_system) + 1)
    rt_mean = float(np.mean(rt_system))

    plt.figure(figsize=(9, 5))
    plt.plot(x, rt_system, linestyle='-', linewidth=2, label="RT")

    # Media
    plt.axhline(rt_mean, linestyle='--', linewidth=2,
                label=f"Media RT = {rt_mean:.2f} s")

    # Intervallo di Confidenza 95%
    if ci_minus is not None and ci_plus is not None:
        ci_lower = rt_mean - ci_minus
        ci_upper = rt_mean + ci_plus

        plt.axhline(ci_lower, linestyle=':', linewidth=2,
                    label=f"CI 95% inferiore = {ci_lower:.2f} s")

        plt.axhline(ci_upper, linestyle=':', linewidth=2,
                    label=f"CI 95% superiore = {ci_upper:.2f} s")

        plt.fill_between(x, ci_lower, ci_upper, alpha=0.15)

    # QoS SOLO per BASE
    if scenario == SCENARIO_BASE:
        plt.axhline(QOS, color='red', linestyle='--', linewidth=2,
                    label=f"QoS = {QOS} s")

    plt.xlabel("Batch", labelpad=10)
    plt.ylabel("Tempo di Risposta [s]", labelpad=10)
    plt.title(
        f"Tempo di Risposta (RT) del Sistema per Batch\n\nScenario {scenario}",
        fontweight="bold",
        fontsize=14,
        pad=15
    )

    plt.xticks(x[::BATCH_STEP])
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Grafico Tempo di risposta del sistema
    plot_system_response_time(
        SCENARIO_BASE
    )
