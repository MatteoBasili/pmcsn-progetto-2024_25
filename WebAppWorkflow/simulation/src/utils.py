import os
import time

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from collections import OrderedDict, defaultdict

from lib.DES import rvgs, rngs

RESULTS_FOLDER = "results/"
FINITE_FOLDER = "finite/"
INFINITE_FOLDER = "infinite/"

RESULTS_FINITE_FOLDER = RESULTS_FOLDER + FINITE_FOLDER
RESULTS_INFINITE_FOLDER = RESULTS_FOLDER + INFINITE_FOLDER


# Exponential service-time sampler
def exp_sample(mean, stream):
    rngs.selectStream(stream)
    if mean <= 0:
        raise ValueError(f"exp_sample: mean must be > 0, got {mean}")
    return rvgs.Exponential(mean)


# Exponential interarrival sampler
def interarrival_time(rate, stream):
    rngs.selectStream(stream)
    if rate <= 0:
        raise ValueError(f"interarrival_time: rate must be > 0, got {rate}")
    return rvgs.Exponential(1.0 / rate)


# Routing table
def next_node_after(server_name, job):
    c = job.current_class
    if c == 'Class1':
        if server_name == 'A': return 'B'
        elif server_name == 'B': return 'CS'
    elif c == 'Class2':
        if server_name == 'A': return 'P'
        elif server_name == 'P': return 'CS'
    elif c == 'Class3':
        if server_name == 'A': return 'SINK'

    return 'SINK'


# Update class after CS
def do_class_switch(job):
    if job.current_class == 'Class1':
        job.current_class = 'Class2'
    elif job.current_class == 'Class2':
        job.current_class = 'Class3'

    return job.current_class

# Calcola metriche a orizzonte finito
def compute_metrics_finite(servers, completed_jobs, t, in_flight):
    metrics = {}

    # RT e throughput globali
    n_completed = len(completed_jobs)
    if n_completed > 0 and t > 0:
        metrics['RT'] = sum(j.finish - j.birth for j in completed_jobs) / n_completed
        metrics['Throughput'] = n_completed / t
    else:
        metrics['RT'] = 0.0
        metrics['Throughput'] = 0.0

    # metriche server
    for sname, srv in servers.items():
        metrics[f'N_{sname}'] = len(srv.jobs)
        metrics[f'U_{sname}'] = (srv.cumulative_busy_time / t) if t > 0 else 0.0
        metrics[f'Throughput_{sname}'] = (srv.num_departures / t) if t > 0 else 0.0

        # RT per server
        server_rts = [j.server_times.get(sname, 0.0) for j in completed_jobs]
        metrics[f'RT_{sname}'] = sum(server_rts)/len(server_rts) if server_rts else 0.0

    # numero di richieste in esecuzione nel sistema
    metrics['N_system'] = len(in_flight)

    return metrics

# Calcola metriche a orizzonte infinito
def compute_metrics_infinite(servers, completed_batch, duration):
    metrics = {}

    # --- Global RT & Throughput ---
    n_completed = len(completed_batch)
    if n_completed > 0 and duration > 0:
        metrics['RT'] = sum(j.finish - j.birth for j in completed_batch) / n_completed
        metrics['Throughput'] = n_completed / duration
    else:
        metrics['RT'] = 0.0
        metrics['Throughput'] = 0.0

    # --- Server-level metrics ---
    for sname, srv in servers.items():
        metrics[f'N_{sname}'] = (srv.area_num_in_system / duration) if duration > 0 else 0.0
        metrics[f'U_{sname}'] = (srv.cumulative_busy_time / duration) if duration > 0 else 0.0
        metrics[f'Throughput_{sname}'] = (srv.num_departures / duration) if duration > 0 else 0.0

        # Server response times
        server_rts = [j.server_times.get(sname, 0.0) for j in completed_batch]
        metrics[f'RT_{sname}'] = sum(server_rts) / len(server_rts) if server_rts else 0.0

    # System-wide number of jobs in system
    if duration > 0:
        n_system_avg = sum(srv.area_num_in_system for srv in servers.values()) / duration
    else:
        n_system_avg = 0.0
    metrics['N_system'] = n_system_avg

    # Throughput Bound + Service Demands
    totals = {}  # server -> total service requested on that server across batch

    for job in completed_batch:
        for srv, t in job.requested_service.items():
            totals[srv] = totals.get(srv, 0.0) + t

    if n_completed > 0:
        d_max = 0.0

        for srv in servers:
            d_i = totals.get(srv, 0.0) / n_completed
            metrics[f'D_{srv}'] = d_i

            if d_i > d_max:
                d_max = d_i

        thr_max = 1.0 / d_max if d_max > 0 else float('inf')
    else:
        for srv in servers:
            metrics[f'D_{srv}'] = 0.0
        thr_max = 0.0

    metrics['Throughput_bound'] = thr_max  # req/s

    return metrics

# Salva le statistiche a orizzonte finito in file .dat (un valore per riga)
def save_finite_metrics(all_replicas_metrics, num_repetitions, scenario):
    os.makedirs(RESULTS_FINITE_FOLDER, exist_ok=True)

    num_samples = len(all_replicas_metrics[0])
    metric_keys = all_replicas_metrics[0][0].keys()

    # Calcola la media tra le repliche per ogni tempo di campionamento
    for key in metric_keys:
        avg_values = []
        for i in range(num_samples):
            mean_at_i = sum(all_replicas_metrics[r][i][key]
                            for r in range(num_repetitions)) / num_repetitions
            avg_values.append(mean_at_i)

        # Salva .dat
        filename = f"{key}_{scenario}.dat"
        path = os.path.join(RESULTS_FINITE_FOLDER, filename)
        with open(path, "w") as f:
            for val in avg_values:
                f.write(f"{val}\n")

    print(f"\n✔ Finite-horizon metrics saved in {RESULTS_FINITE_FOLDER}")

# Salva il numero di arrivi totali al sistema in un file .dat (un valore per riga)
def save_finite_total_arrivals(arrivals_per_run, scenario):
    os.makedirs(RESULTS_FINITE_FOLDER, exist_ok=True)

    filename = f"total_arrivals_{scenario}.dat"
    path = os.path.join(RESULTS_FINITE_FOLDER, filename)

    with open(path, "w") as f:
        for val in arrivals_per_run:
            f.write(f"{val}\n")

    print(f"\n✔ Total arrivals per run saved in {path}")

# Salva le statistiche a orizzonte infinito in file .dat (un valore per riga)
def save_infinite_metrics(batch_stats, scenario):
    os.makedirs(RESULTS_INFINITE_FOLDER, exist_ok=True)

    # Ottieni la lista delle metriche (chiavi del primo batch)
    metric_keys = list(batch_stats[0].keys())

    for key in metric_keys:
        filename = f"{key}_{scenario}.dat"
        path = os.path.join(RESULTS_INFINITE_FOLDER, filename)

        with open(path, "w") as f:
            for bs in batch_stats:
                f.write(f"{bs[key]}\n")

    print(f"\n✔ Infinite-horizon metrics saved in {RESULTS_INFINITE_FOLDER}")

# Salva i tempi di risposta del batch in un file .dat (un valore per riga)
def save_batch_rts(batch_rts, b, scenario):
    os.makedirs(RESULTS_INFINITE_FOLDER, exist_ok=True)
    filename = f"rt_batch_inf_{b}_{scenario}.dat"
    path = os.path.join(RESULTS_INFINITE_FOLDER, filename)

    with open(path, "w") as f:
        for rt in batch_rts:
            f.write(f"{rt}\n")

    return path

# Visualizza la sequenza delle visite ai tre server
def plot_job_visit_sequence(completed_jobs, scenario):
    row_order = OrderedDict()
    row_intervals = defaultdict(list)
    max_time = 0.0

    # Costruisci le righe in ordine di prima apparizione
    for job in completed_jobs:
        for entry in job.history:
            sname, job_class, visit_number, t_start, t_end = entry
            if t_end is None:
                t_end = t_start
            key = (sname, job_class, visit_number)
            if key not in row_order:
                row_order[key] = None
            row_intervals[key].append((t_start, t_end))
            if t_end > max_time:
                max_time = t_end

    sorted_keys = list(row_order.keys())[::-1]  # ordine invertito

    fig, ax = plt.subplots(figsize=(6, 0.5 * len(sorted_keys) + 2))

    # Titolo
    ax.set_title(
        f"Sequenza temporale delle Visite ai tre Server durante l'esecuzione di una Richiesta (Job)\n\nScenario: {scenario}",
        fontweight='bold',
        fontsize=14,
        pad=15
    )

    server_colors = {'A': 'skyblue', 'B': 'salmon', 'P': 'lightgreen'}

    # Disegna le barre dei job
    for i, key in enumerate(sorted_keys):
        sname, job_class, visit_number = key
        color = server_colors.get(sname, 'gray')
        for t_start, t_end in row_intervals[key]:
            ax.barh(i, t_end - t_start, left=t_start, height=0.6, color=color, edgecolor='black')

    # Etichette delle righe
    yticks = np.arange(len(sorted_keys))
    ytick_labels = [f"Server {sname} — {job_class}\n(Visit {visit_number})" for (sname, job_class, visit_number) in sorted_keys]
    ax.set_yticks(yticks)
    ax.set_yticklabels(ytick_labels, ha='center', va='center', linespacing=1.5)
    ax.tick_params(axis='y', pad=60)
    ax.set_xlabel("Time [s]")

    # Linee orizzontali per separare le righe
    for y in np.arange(-0.5, len(sorted_keys), 1):
        ax.axhline(y=float(y), color='gray', linestyle='-', linewidth=0.5, alpha=0.5)

    # Linee verticali tratteggiate ogni secondo
    step = 1
    for x in np.arange(0, np.ceil(max_time)+step, step):
        ax.axvline(x=float(x), color='gray', linestyle='--', linewidth=0.5, alpha=0.5)

    # Tick principali a ogni secondo
    ax.set_xticks(np.arange(0, 13, 1))
    ax.set_xlim(0, 12)
    ax.set_ylim(-0.5, len(sorted_keys)-0.5)

    for job in completed_jobs:
        t = job.birth
        # linea verticale rossa
        ax.axvline(x=t, color='red', linestyle='-', linewidth=0.8, alpha=0.6)
        ax.text(
            t,  # posizione x
            -1.25,
            f"Job {job.id}   ⟶",  # testo
            rotation=90,
            verticalalignment='top',
            horizontalalignment='center',
            color='red',
            fontsize=11
        )

    # Aggiungi legenda
    arrival_line = Line2D([0], [0], color='red', lw=1, alpha=0.6, label='Arrivo richiesta al sistema')
    ax.legend(
        handles=[arrival_line],
        loc='upper left',
        bbox_to_anchor=(0.003, 0.992),
        fontsize=9
    )

    plt.tight_layout()
    plt.show()

def plot_throughput_vs_lambda(lambda_values, throughput_values, scenario):
    thr_max = 1.250741

    plt.figure(figsize=(9, 5))

    # Curva throughput simulato
    plt.plot(lambda_values, throughput_values, marker='o', label="Throughput simulato")

    # Linea del throughput bound analitico
    plt.axhline(y=thr_max, color='r', linestyle='--', linewidth=2,
                label=f"Throughput bound = {thr_max:.2f}")

    plt.xlabel("λ (arrival rate)")
    plt.ylabel("Throughput medio")
    plt.title(f"Throughput simulato al variare di λ\n\nScenario {scenario}")
    plt.grid(True)

    plt.legend()
    plt.tight_layout()
    plt.show()

# Stampa a schermo arrivi, completamenti e job ancora in coda
def print_arrivals_and_completions(total_system_arrivals, completed_jobs, jobs_in_flight, servers):
    print("\n============================================================\n")

    print(f"ARRIVI TOTALI AL SISTEMA: {total_system_arrivals}")
    print(f"COMPLETAMENTI TOTALI:    {len(completed_jobs)}")
    print(f"JOB ANCORA NEL SISTEMA:  {len(jobs_in_flight)}")

    print("\n--- Servers ---")
    for name, srv in servers.items():
        print(f"\nServer {name}:")
        print(f"  Arrivi:        {srv.num_arrivals}")
        print(f"  Completamenti: {srv.num_departures}")
        print(f"  Job residui:   {len(srv.jobs)}")

    print("\n============================================================\n")

# Stampa a schermo una linea di separazione
def print_line():
    print("————————————————————————————————————————————————————————————————————————————————————————")

# Stampa a schermo che è finita la simulazione
def close_simulation():
    print()
    print_line()
    time.sleep(1)
    print("[INFO] Simulazione finita.\n")
    print_line()
    print()
    time.sleep(1)
