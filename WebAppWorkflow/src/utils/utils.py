import csv

from lib.DES import rvgs, rngs
from sim_config import ARRIVAL_STREAM


# Exponential service-time sampler
def exp_sample(mean, stream):
    rngs.selectStream(stream)
    if mean <= 0:
        raise ValueError(f"exp_sample: mean must be > 0, got {mean}")
    return rvgs.Exponential(mean)


# Exponential interarrival sampler
def interarrival_time(rate):
    rngs.selectStream(ARRIVAL_STREAM)
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

def save_response_times_matrix_csv(response_times_ts, ts_step):
    filename = f"response_times_matrix_{ts_step}s.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([f"t={i*ts_step}" for i in range(len(response_times_ts[0]))])
        writer.writerows(response_times_ts)
    print(f"[OK] Saved CSV: {filename}")

def save_mean_curve_csv(mean_curve, ts_step):
    filename = f"mean_response_time_{ts_step}s.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "mean_response_time"])
        for i, v in enumerate(mean_curve):
            writer.writerow([i * ts_step, v])
    print(f"[OK] Saved CSV: {filename}")

# Stampa a schermo una linea di separazione
def print_line():
    print("————————————————————————————————————————————————————————————————————————————————————————")
