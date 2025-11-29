import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from collections import OrderedDict, defaultdict

from lib.DES import rvgs, rngs


RESULTS_FOLDER = "results/"
RESULTS_FINITE_FOLDER = RESULTS_FOLDER + "finite/"
RESULTS_INFINITE_FOLDER = RESULTS_FOLDER + "infinite/"


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

# Stampa a schermo una linea di separazione
def print_line():
    print("————————————————————————————————————————————————————————————————————————————————————————")

# Salva le statistiche ad orizzonte finito in file .dat
def save_finite_metrics(all_replicas_metrics, num_repetitions):
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
        path = os.path.join(RESULTS_FINITE_FOLDER, f"{key}.dat")
        with open(path, "w") as f:
            for val in avg_values:
                f.write(f"{val}\n")

    print(f"\n✔ Average metrics saved in {RESULTS_FINITE_FOLDER}")

# Visualizza la sequenza delle visite ai tre server
def plot_job_visit_sequence(completed_jobs):
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
    ax.set_title(
        "Sequenza temporale delle Visite ai tre Server durante l'esecuzione di una Richiesta (Job)",
        fontweight='bold',
        fontsize=14,
        pad=15
    )

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
            -1,
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
