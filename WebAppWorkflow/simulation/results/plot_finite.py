import os
import numpy as np
import matplotlib.pyplot as plt

SCENARIO_BASE = "light_1FA"
SCENARIO_SCA = "light_2FA"
SCENARIO_HEAVY = "heavy_1FA"
SCENARIO_HEAVY_NEW_B = "heavy_1FA_newServerB"

TS_STEP = 300

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FOLDER = os.path.join(BASE_DIR, "..", "results", "finite")

def load_metric(metric_name, scenario):
    filename = f"{metric_name}_{scenario}.dat"
    path = os.path.join(RESULTS_FOLDER, filename)

    if not os.path.exists(path):
        raise FileNotFoundError(f"File non trovato: {path}")

    with open(path, "r") as f:
        values = [float(line.strip()) for line in f.readlines()]

    return np.array(values)

def plot_system_response_time(scenario):
    # --- Carica RT globale ---
    rt_system = load_metric("RT", scenario)

    # Asse tempo
    x = np.arange(len(rt_system)) * TS_STEP

    # --- Plot ---
    plt.figure(figsize=(9, 5))
    plt.plot(x, rt_system, linestyle='-', color='tab:blue', linewidth=2)
    plt.xlabel("Tempo [s]", labelpad=10)
    plt.ylabel("Tempo di Risposta [s]", labelpad=10)
    plt.title(
        f"Tempo di Risposta del Sistema nel Tempo\n\nScenario {scenario}",
        fontweight="bold",
        fontsize=14,
        pad=15
    )
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

def plot_system_number(scenario):
    n_system = load_metric("N_system", scenario)
    x = np.arange(len(n_system)) * TS_STEP

    plt.figure(figsize=(9, 5))
    plt.plot(x, n_system, linestyle='-', color='tab:blue', linewidth=2)
    plt.xlabel("Tempo [s]", labelpad=10)
    plt.ylabel("Numero Medio di Richieste", labelpad=10)
    plt.title(f"Numero Medio di Richieste nel Sistema nel Tempo\n\nScenario {scenario}",
              fontweight="bold", fontsize=14, pad=15)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

def plot_utilizations_together(scenario):
    # --- Carica le tre utilizzazioni ---
    u_a = load_metric("U_A", scenario)
    u_b = load_metric("U_B", scenario)
    u_p = load_metric("U_P", scenario)

    # Asse tempo
    x = np.arange(len(u_a)) * TS_STEP

    # --- Plot ---
    plt.figure(figsize=(9, 5))

    plt.plot(x, u_a, label="Server A", linewidth=2)
    plt.plot(x, u_b, label="Server B", linewidth=2)
    plt.plot(x, u_p, label="Server P", linewidth=2)

    plt.xlabel("Tempo [s]", labelpad=10)
    plt.ylabel("Utilizzazione", labelpad=10)

    plt.title(
        f"Utilizzazione dei Server nel Tempo\n\nScenario {scenario}",
        fontweight="bold",
        fontsize=14,
        pad=15
    )

    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_rt_comparison_between_base_and_sca():
    rt_1 = load_metric("RT", SCENARIO_BASE)
    rt_2 = load_metric("RT", SCENARIO_SCA)

    n = min(len(rt_1), len(rt_2))
    rt_1 = rt_1[:n]
    rt_2 = rt_2[:n]

    x = np.arange(n) * TS_STEP

    plt.figure(figsize=(9, 5))
    plt.plot(x, rt_1, label=f"RT {SCENARIO_BASE}", linewidth=2)
    plt.plot(x, rt_2, label=f"RT {SCENARIO_SCA}", linewidth=2)

    plt.xlabel("Tempo [s]", labelpad=10)
    plt.ylabel("Tempo di Risposta [s]", labelpad=10)
    plt.title(
        "Confronto tra Scenari: Tempo di Risposta\n\nAutenticazione a un Fattore VS Autenticazione a Due Fattori",
        fontweight="bold",
        fontsize=14,
        pad=15
    )

    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_n_system_comparison_between_base_and_sca():
    n_1 = load_metric("N_system", SCENARIO_BASE)
    n_2 = load_metric("N_system", SCENARIO_SCA)

    n = min(len(n_1), len(n_2))
    n_1 = n_1[:n]
    n_2 = n_2[:n]

    x = np.arange(n) * TS_STEP

    plt.figure(figsize=(9, 5))
    plt.plot(x, n_1, label=f"N_system {SCENARIO_BASE}", linewidth=2)
    plt.plot(x, n_2, label=f"N_system {SCENARIO_SCA}", linewidth=2)

    plt.xlabel("Tempo [s]", labelpad=10)
    plt.ylabel("Numero Medio di Richieste", labelpad=10)
    plt.title(
        "Confronto tra Scenari: Numero Medio di Richieste nel Sistema\n\nAutenticazione a un Fattore VS Autenticazione a Due Fattori",
        fontweight="bold",
        fontsize=14,
        pad=15
    )

    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

def plot_jobs_in_servers_together(scenario):
    # --- Carica N_A, N_B, N_P ---
    n_a = load_metric("N_A", scenario)
    n_b = load_metric("N_B", scenario)
    n_p = load_metric("N_P", scenario)

    # Asse tempo
    x = np.arange(len(n_a)) * TS_STEP

    # --- Plot ---
    plt.figure(figsize=(9, 5))

    plt.plot(x, n_a, label="Server A", linewidth=2)
    plt.plot(x, n_b, label="Server B", linewidth=2)
    plt.plot(x, n_p, label="Server P", linewidth=2)

    plt.xlabel("Tempo [s]", labelpad=10)
    plt.ylabel("Numero Medio di Richieste", labelpad=10)

    plt.title(
        f"Andamento delle Richieste in Esecuzione nei Server\n\nScenario {scenario}",
        fontweight="bold",
        fontsize=14,
        pad=15
    )

    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Grafico Tempo di risposta del sistema
    plot_system_response_time(SCENARIO_BASE)

    # Grafico Numero medio di richieste nel sistema
    plot_system_number(SCENARIO_BASE)

    # Grafico Andamento richieste nei Server A–B–P
    plot_jobs_in_servers_together(SCENARIO_BASE)

    # Grafico Utilizzazioni dei server
    plot_utilizations_together(SCENARIO_BASE)

    # Grafico Confronto RT tra light_1FA e light_2FA
    plot_rt_comparison_between_base_and_sca()

    # Grafico Confronto N_system tra light_1FA e light_2FA
    plot_n_system_comparison_between_base_and_sca()
