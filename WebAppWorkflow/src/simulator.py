import csv
import heapq
import time

from tqdm import tqdm

from sim_config import *
from src.entities import *
from src.utils import *


def schedule_departure(sname, now, servers, evq):
    srv = servers[sname]
    srv.version += 1
    td = srv.next_departure_time(now)
    if td is not None:
        heapq.heappush(evq, Event(td, 'departure', (sname, srv.version)))

def handle_arrival(t, evq, servers, service_demands, arrival_stream, service_streams,
                   arrival_rate, in_flight):

    job = Job(t)
    in_flight[job.id] = job
    mean = service_demands['A'][job.current_class]
    st = exp_sample(mean, service_streams['A'])

    #########################################
    # Per il plot della sequenza delle visite
    if PLOT_VISITS:
        st = mean
    #########################################

    servers['A'].process_arrival(job, st)

    # aggiorna visita e history
    job.visit_count['A'] = job.visit_count.get('A', 0) + 1
    visit_number = job.visit_count['A']
    job.history.append(('A', job.current_class, visit_number, t, None))

    schedule_departure('A', t, servers, evq)

    # Schedule next arrival
    t_next_arr = t + interarrival_time(arrival_rate, arrival_stream)

    #########################################
    # Per il plot della sequenza delle visite
    if PLOT_VISITS:
        t_next_arr = t + 3  # un arrivo ogni tre secondi
    #########################################

    heapq.heappush(evq, Event(t_next_arr, 'arrival', None))

def handle_departure(ev, t, evq, servers, service_demands,
                     service_streams, in_flight, completed_jobs):
    sname, ev_version = ev.payload
    srv = servers[sname]

    job = srv.process_completion(ev_version)
    if job is None:
        # stale event
        return

    # Aggiorna la history del job
    for i in range(len(job.history) - 1, -1, -1):
        if job.history[i][0] == sname and job.history[i][4] is None:
            job.history[i] = (
                job.history[i][0],
                job.history[i][1],
                job.history[i][2],
                job.history[i][3],
                t
            )
            job.server_times[sname] = job.server_times.get(sname, 0.0) + (t - job.history[i][3])
            break

    schedule_departure(sname, t, servers, evq)

    # Routing
    nextn = next_node_after(sname, job)
    if nextn == 'CS':
        new_class = do_class_switch(job)
        mean = service_demands['A'][new_class]
        st = exp_sample(mean, service_streams['A'])

        #########################################
        # Per il plot della sequenza delle visite
        if PLOT_VISITS:
            st = mean
        #########################################

        servers['A'].process_arrival(job, st)

        # aggiorna visita e history
        job.visit_count['A'] = job.visit_count.get('A', 0) + 1
        visit_number = job.visit_count['A']
        job.history.append(('A', job.current_class, visit_number, t, None))

        schedule_departure('A', t, servers, evq)

    elif nextn in ['B', 'P']:
        mean = service_demands[nextn][job.current_class]
        st = exp_sample(mean, service_streams[nextn])

        #########################################
        # Per il plot della sequenza delle visite
        if PLOT_VISITS:
            st = mean
        #########################################

        servers[nextn].process_arrival(job, st)

        job.visit_count[nextn] = job.visit_count.get(nextn, 0) + 1
        visit_number = job.visit_count[nextn]
        job.history.append((nextn, job.current_class, visit_number, t, None))

        schedule_departure(nextn, t, servers, evq)

    elif nextn == 'SINK':
        job.finish = t
        completed_jobs.append(job)
        in_flight.pop(job.id, None)

def process_event(ev, t, evq, servers, service_demands, arrival_stream, service_streams,
                  arrival_rate, in_flight, completed_jobs):

    # Process event
    if ev.etype == 'arrival':
        handle_arrival(t, evq, servers, service_demands, arrival_stream, service_streams,
                       arrival_rate, in_flight)

    elif ev.etype == 'departure':
        handle_departure(ev, t, evq, servers, service_demands,
                         service_streams, in_flight, completed_jobs)

def simulate_batch(max_completed_jobs, arrival_rate, service_demands, arrival_stream, service_streams,
                   initial_servers=None, initial_evq=None,
                   initial_t=0.0, initial_in_flight=None):
    t = float(initial_t)

    # Initialize servers
    if initial_servers is None:
        servers = {name: PSServer(name) for name in ['A', 'B', 'P']}
    else:
        servers = initial_servers

    # Event queues
    evq = [] if initial_evq is None else initial_evq  # heapq for departures
    in_flight = {} if initial_in_flight is None else initial_in_flight

    completed_jobs = []

    # Ensure at least one arrival is scheduled
    if not evq:
        t_next_arr = t + interarrival_time(arrival_rate, arrival_stream)
        heapq.heappush(evq, Event(t_next_arr, 'arrival', None))

    # Main loop
    while evq and len(completed_jobs) < max_completed_jobs:
        ev = heapq.heappop(evq)
        t = ev.time

        # Update server stats
        for srv in servers.values():
            srv.update_progress(t)

        process_event(
            ev, t, evq, servers, service_demands, arrival_stream, service_streams,
            arrival_rate, in_flight, completed_jobs
        )

    return completed_jobs, servers, in_flight, evq, t

def find_batch_b(b_values=(64,128,256,512,1024,2048, 4096, 8192),
                 k=128,
                 output_folder="results/infinite/"):
    print("\n=== Ricerca batch size b ottimale ===")
    print(f"Batch k = {k}")
    print("Valori testati di b:", b_values)

    rngs.plantSeeds(SEED)

    for b in b_values:
        print(f"\n>>> Test batch size b = {b}")

        servers = {name: PSServer(name) for name in ['A', 'B', 'P']}
        evq = []
        in_flight = {}
        t = 0.0

        batch_rts = []

        for _ in tqdm(range(k), desc=f"b={b}", ascii="░▒▓█", ncols=90):
            completed_batch, servers, in_flight, evq, t = simulate_batch(
                max_completed_jobs=b,
                arrival_rate=ARRIVAL_RATE,
                service_demands=SERVICE_DEMANDS,
                arrival_stream=ARRIVAL_STREAM,
                service_streams=SERVICE_STREAMS,
                initial_servers=servers,
                initial_evq=evq,
                initial_t=t,
                initial_in_flight=in_flight
            )

            # calcolo mean response time del batch
            if completed_batch:
                mean_rt = sum(job.finish - job.birth for job in completed_batch) / len(completed_batch)
            else:
                mean_rt = 0.0

            batch_rts.append(mean_rt)

            # resetta solo le statistiche dei server
            for srv in servers.values():
                srv.reset_statistics()

        os.makedirs(output_folder, exist_ok=True)
        csv_path = f"{output_folder}rt_batch_inf_{b}.csv"
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            for rt in batch_rts:
                w.writerow([rt])

        print(f"✔ Salvato CSV: {csv_path}")

    print("\n=== Completato. Ora puoi lanciare acs.c sui CSV generati. ===\n")

def infinite_horizon_simulation(k, b):
    rngs.plantSeeds(SEED)

    # inizializzo sistema
    servers = {name: PSServer(name) for name in ['A', 'B', 'P']}
    evq = []
    in_flight = {}
    t = 0.0
    last_completion_time = 0.0

    batch_stats = []

    for bi in tqdm(range(k), desc="Simulation in progress...", ascii="░▒▓█", ncols=100):
        completed_batch, servers, in_flight, evq, t = simulate_batch(
            max_completed_jobs=b,
            arrival_rate=ARRIVAL_RATE,
            service_demands=SERVICE_DEMANDS,
            arrival_stream=ARRIVAL_STREAM,
            service_streams=SERVICE_STREAMS,
            initial_servers=servers,
            initial_evq=evq,
            initial_t=t,
            initial_in_flight=in_flight
        )

        # calcolo durata batch
        if completed_batch:
            batch_start = last_completion_time
            batch_end = completed_batch[-1].finish
            duration = max(batch_end - batch_start, 1e-9)
            last_completion_time = batch_end
        else:
            duration = 1.0  # fallback

        # statistiche batch
        bs = {
            'batch_index': bi,
            'n_completed': len(completed_batch),
            'mean_rt': sum(job.finish - job.birth for job in completed_batch)/len(completed_batch) if completed_batch else 0.0,
            'throughput_rps': len(completed_batch)/duration
        }

        # utilizzo e avg_n server
        for sname, srv in servers.items():
            bs[f'{sname}_util'] = srv.cumulative_busy_time / duration
            bs[f'{sname}_avg_n'] = srv.area_num_in_system / duration
            bs[f'{sname}_arrivals'] = srv.num_arrivals
            bs[f'{sname}_departures'] = srv.num_departures

            # resetto statistiche batch mantenendo job in sistema e code
            srv.reset_statistics()

        batch_stats.append(bs)
        time.sleep(0.05)

    # --- Generazione file .dat per ogni statistica ---
    stats_to_save = list(batch_stats[0].keys())
    for stat in stats_to_save:
        path = os.path.join("results/infinite/", f"{stat}.dat")
        with open(path, "w") as f:
            for b in batch_stats:
                f.write(f"{b[stat]}\n")
        print(f"✔ Salvato {path}")

    '''
    # statistiche aggregate su tutti i batch
    aggregated = {}
    aggregated['mean_rt'] = sum(b['mean_rt'] for b in batch_stats) / k
    aggregated['throughput_rps'] = sum(b['throughput_rps'] for b in batch_stats) / k
    for sname in ['A', 'B', 'P']:
        aggregated[f'{sname}_util'] = sum(b[f'{sname}_util'] for b in batch_stats) / k
        aggregated[f'{sname}_avg_n'] = sum(b[f'{sname}_avg_n'] for b in batch_stats) / k
        aggregated[f'{sname}_arrivals'] = sum(b[f'{sname}_arrivals'] for b in batch_stats) / k
        aggregated[f'{sname}_departures'] = sum(b[f'{sname}_departures'] for b in batch_stats) / k

    final_state = (servers, evq, in_flight, t)

    # Stampo i risultati aggregati
    print("\n=== Aggregated Statistics Over All Batches ===")
    for key, value in aggregated.items():
        print(f"{key}: {value}")

    return batch_stats, aggregated, final_state
    '''

# Funzione helper per calcolare metriche
def compute_metrics_finite(servers, completed_jobs, t, in_flight):
    metrics = {}
    # RT e throughput globali
    if completed_jobs:
        metrics['RT'] = sum(j.finish - j.birth for j in completed_jobs) / len(completed_jobs)
        metrics['Throughput'] = len(completed_jobs) / t
    else:
        metrics['RT'] = 0.0
        metrics['Throughput'] = 0.0

    # metriche server
    for sname, srv in servers.items():
        metrics[f'N_{sname}'] = len(srv.jobs)
        metrics[f'U_{sname}'] = srv.cumulative_busy_time / t
        metrics[f'Throughput_{sname}'] = srv.num_departures / t

        # RT per server
        server_rts = [j.server_times.get(sname, 0.0) for j in completed_jobs]
        metrics[f'RT_{sname}'] = sum(server_rts)/len(server_rts) if server_rts else 0.0

    # numero di richieste in esecuzione nel sistema
    metrics['N_system'] = len(in_flight)

    return metrics

# -------------------------------------------------------
#                     Simulation Engine
# -------------------------------------------------------
def simulate_finite(stop_time, arrival_rate, service_demands, arrival_stream, service_streams, ts_step):
    Job._id = 0
    t = 0.0
    next_sample_time = 0.0

    servers = {name: PSServer(name) for name in ['A','B','P']}
    evq = []
    completed_jobs = []
    in_flight = {}

    # Lista finale di campioni: ogni elemento è un dict con tutte le metriche
    sampled_metrics = []

    # first arrival
    t_next_arr = t + interarrival_time(arrival_rate, arrival_stream)

    #########################################
    # Per il plot della sequenza delle visite
    if PLOT_VISITS:
        t_next_arr = t + 3   # un arrivo ogni tre secondi
    #########################################

    heapq.heappush(evq, Event(t_next_arr, 'arrival', None))

    while evq:
        ev = heapq.heappop(evq)
        t = ev.time

        if t > stop_time:
            for srv in servers.values():
                srv.update_progress(stop_time)

            while next_sample_time <= stop_time:
                metrics = compute_metrics_finite(servers, completed_jobs, stop_time, in_flight)
                sampled_metrics.append(metrics)
                next_sample_time += ts_step
            break

        for srv in servers.values():
            srv.update_progress(t)

        # --- SAMPLING ---
        while next_sample_time <= t:
            metrics = compute_metrics_finite(servers, completed_jobs, t, in_flight)
            sampled_metrics.append(metrics)
            next_sample_time += ts_step

        process_event(
            ev, t, evq, servers, service_demands, arrival_stream, service_streams,
            arrival_rate, in_flight, completed_jobs
        )

    return sampled_metrics, completed_jobs

# Esegue una simulazione a orizzonte finito per un certo numero di volte
def finite_horizon_simulation(stop_time, num_repetitions):
    rngs.plantSeeds(SEED)
    all_replicas_metrics = []

    for _ in tqdm(range(num_repetitions), desc="Simulation in progress...", ascii="░▒▓█", ncols=100):
        metrics, completed_jobs = simulate_finite(stop_time, ARRIVAL_RATE, SERVICE_DEMANDS,
                                                  ARRIVAL_STREAM, SERVICE_STREAMS, TS_STEP)
        all_replicas_metrics.append(metrics)

        #########################################
        # Per il plot della sequenza delle visite
        if PLOT_VISITS:
            plot_job_visit_sequence(completed_jobs)
        #########################################

        time.sleep(0.05)

    if not PLOT_VISITS:
        save_finite_metrics(all_replicas_metrics, num_repetitions)
