import heapq

from tqdm import tqdm

from sim_config import PLOT_VISITS, SEED, ARRIVAL_RATE, SERVICE_DEMANDS, ARRIVAL_STREAM, SERVICE_STREAMS, TS_STEP, \
    SCENARIO
from src.entities import *
from src.utils import *


def schedule_departure(sname, now, servers, compl_q):
    srv = servers[sname]
    srv.version += 1
    td = srv.next_departure_time(now)
    if td is not None:
        heapq.heappush(compl_q, CompletionEvent(td, (sname, srv.version)))

def handle_arrival(clock, compl_q, servers, service_demands, arrival_stream, service_streams,
                   arrival_rate, in_flight):
    # Schedule next arrival
    t_next_arr = clock.current + interarrival_time(arrival_rate, arrival_stream)

    job = Job(clock.current)
    in_flight[job.id] = job
    mean = service_demands['A'][job.current_class]
    st = exp_sample(mean, service_streams['A'])

    #########################################
    # Per il plot della sequenza delle visite
    if PLOT_VISITS:
        st = mean
        t_next_arr = clock.current + 3  # un arrivo ogni tre secondi
    #########################################

    job.requested_service['A'] = job.requested_service.get('A', 0.0) + st

    # aggiorna visita e history
    job.visit_count['A'] = job.visit_count.get('A', 0) + 1
    visit_number = job.visit_count['A']
    job.history.append(('A', job.current_class, visit_number, clock.current, None))

    servers['A'].process_arrival(job, st)
    schedule_departure('A', clock.current, servers, compl_q)

    clock.update_arrival(t_next_arr)

def handle_departure(t, compl_q, servers, service_demands,
                     service_streams, in_flight, completed_jobs):
    ev = heapq.heappop(compl_q)
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

    schedule_departure(sname, t, servers, compl_q)

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

        job.requested_service['A'] = job.requested_service.get('A', 0.0) + st

        # aggiorna visita e history
        job.visit_count['A'] = job.visit_count.get('A', 0) + 1
        visit_number = job.visit_count['A']
        job.history.append(('A', job.current_class, visit_number, t, None))

        servers['A'].process_arrival(job, st)
        schedule_departure('A', t, servers, compl_q)

    elif nextn in ['B', 'P']:
        mean = service_demands[nextn][job.current_class]
        st = exp_sample(mean, service_streams[nextn])

        #########################################
        # Per il plot della sequenza delle visite
        if PLOT_VISITS:
            st = mean
        #########################################

        job.requested_service[nextn] = job.requested_service.get(nextn, 0.0) + st

        # aggiorna visita e history
        job.visit_count[nextn] = job.visit_count.get(nextn, 0) + 1
        visit_number = job.visit_count[nextn]
        job.history.append((nextn, job.current_class, visit_number, t, None))

        servers[nextn].process_arrival(job, st)
        schedule_departure(nextn, t, servers, compl_q)

    elif nextn == 'SINK':
        job.finish = t
        completed_jobs.append(job)
        in_flight.pop(job.id, None)

def simulate_batch(max_completed_jobs, arrival_rate, service_demands, arrival_stream, service_streams,
                   servers, compl_q,
                   clock, in_flight):

    completed_jobs = []

    # Ensure at least one arrival is scheduled
    if clock.arrival is None:
        t_next_arr = clock.current + interarrival_time(arrival_rate, arrival_stream)
        clock.update_arrival(t_next_arr)
        clock.update_next(clock.arrival)

    # Main loop
    while len(completed_jobs) < max_completed_jobs:
        clock.update_current(clock.next)

        # Update server stats
        for srv in servers.values():
            srv.update_progress(clock.current)

        # Process event
        if clock.current == clock.arrival:
            handle_arrival(clock, compl_q, servers, service_demands, arrival_stream, service_streams,
                           arrival_rate, in_flight)
        else:
            handle_departure(clock.current, compl_q, servers, service_demands,
                             service_streams, in_flight, completed_jobs)

        if compl_q:
            compl_ev = compl_q[0]
            compl_t = compl_ev.time
            next_ev = min(compl_t, clock.arrival)

        else:
            next_ev = clock.arrival

        clock.update_next(next_ev)

    return completed_jobs, servers, in_flight, compl_q, clock

def find_batch_b(k, b_values):
    rngs.plantSeeds(SEED)

    for b in b_values:
        print(f"\n>>> Batch size b = {b}")
        print("Simulation in progress...")

        servers = {name: PSServer(name) for name in ['A', 'B', 'P']}
        compl_q = []
        in_flight = {}
        clock = Clock()

        batch_rts = []

        for _ in range(k):
            completed_batch, servers, in_flight, compl_q, clock = simulate_batch(
                b,
                ARRIVAL_RATE,
                SERVICE_DEMANDS,
                ARRIVAL_STREAM,
                SERVICE_STREAMS,
                servers,
                compl_q,
                clock,
                in_flight
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

        print("Completed")

        path = save_batch_rts(batch_rts, b, SCENARIO)
        print(f"✔ Dati salvati in {path}")

def infinite_horizon_simulation(k, b):
    rngs.plantSeeds(SEED)

    # inizializzo sistema
    servers = {name: PSServer(name) for name in ['A', 'B', 'P']}
    compl_q = []
    in_flight = {}
    clock = Clock()
    last_completion_time = 0.0

    batch_stats = []

    for _ in tqdm(range(k), desc="Simulation in progress...", ascii="░▒▓█", ncols=100):
        completed_batch, servers, in_flight, compl_q, clock = simulate_batch(
            b,
            ARRIVAL_RATE,
            SERVICE_DEMANDS,
            ARRIVAL_STREAM,
            SERVICE_STREAMS,
            servers,
            compl_q,
            clock,
            in_flight
        )

        # calcolo durata batch
        batch_start = last_completion_time
        batch_end = clock.current
        duration = batch_end - batch_start
        last_completion_time = batch_end

        # --- Compute metrics ---
        metrics = compute_metrics_infinite(
            servers,
            completed_batch,
            duration
        )

        batch_stats.append(metrics)

        # Reset server statistics for next batch
        for srv in servers.values():
            srv.reset_statistics()

    print("Completed")

    save_infinite_metrics(batch_stats, SCENARIO)

def simulate_finite(stop_time, arrival_rate, service_demands, arrival_stream, service_streams, ts_step):
    Job._id = 0
    clock = Clock()
    next_sample_time = 0.0

    servers = {name: PSServer(name) for name in ['A','B','P']}
    compl_q = []
    completed_jobs = []
    in_flight = {}

    # Lista finale di campioni: ogni elemento è un dict con tutte le metriche
    sampled_metrics = []

    # first arrival
    t_next_arr = clock.current + interarrival_time(arrival_rate, arrival_stream)

    #########################################
    # Per il plot della sequenza delle visite
    if PLOT_VISITS:
        t_next_arr = clock.current + 3   # un arrivo ogni tre secondi
    #########################################

    clock.update_arrival(t_next_arr)
    clock.update_next(clock.arrival)

    while clock.next <= stop_time:
        clock.update_current(clock.next)

        for srv in servers.values():
            srv.update_progress(clock.current)

        # --- SAMPLING ---
        while next_sample_time <= clock.current:
            metrics = compute_metrics_finite(servers, completed_jobs, clock.current, in_flight)
            sampled_metrics.append(metrics)
            next_sample_time += ts_step

        # Process event
        if clock.current == clock.arrival:
            handle_arrival(clock, compl_q, servers, service_demands, arrival_stream, service_streams,
                           arrival_rate, in_flight)
        else:
            handle_departure(clock.current, compl_q, servers, service_demands,
                             service_streams, in_flight, completed_jobs)

        if compl_q:
            compl_ev = compl_q[0]
            compl_t = compl_ev.time
            next_ev = min(compl_t, clock.arrival)

        else:
            next_ev = clock.arrival

        clock.update_next(next_ev)

    for srv in servers.values():
        srv.update_progress(stop_time)

    while next_sample_time <= stop_time:
        metrics = compute_metrics_finite(servers, completed_jobs, stop_time, in_flight)
        sampled_metrics.append(metrics)
        next_sample_time += ts_step

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

    print("Completed")

    if not PLOT_VISITS:
        save_finite_metrics(all_replicas_metrics, num_repetitions, SCENARIO)
