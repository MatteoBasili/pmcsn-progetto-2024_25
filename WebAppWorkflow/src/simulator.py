import heapq
import time

from tqdm import tqdm

from sim_config import *
from src.sim_entities import *
from src.sim_utils import *


def simulate_batch(b, arrival_rate, service_demands, service_streams,
                   initial_servers=None, initial_evq=None,
                   initial_t=0.0, initial_in_flight=None,
                   initial_arrival_queue=None):
    """
    Simulate until `b` arrivals **and** `b` completions are processed.
    This function only updates the system state, without computing statistics.

    Returns:
        completed_jobs: list of Job objects completed in this batch
        servers, in_flight, evq, t: updated system state after the call
        arrival_queue: remaining arrivals not yet processed
    """
    t = float(initial_t)

    # Initialize servers
    if initial_servers is None:
        servers = {name: PSServer(name) for name in ['A', 'B', 'P']}
    else:
        servers = initial_servers

    # Event queues
    evq = [] if initial_evq is None else initial_evq  # heapq for departures
    in_flight = {} if initial_in_flight is None else initial_in_flight
    arrival_queue = [] if initial_arrival_queue is None else initial_arrival_queue  # list for arrivals

    completed_jobs = []
    processed_arrivals = 0

    def schedule_departure(sname, now):
        srv = servers[sname]
        srv.version += 1
        td = srv.next_departure_time(now)
        if td is not None:
            heapq.heappush(evq, Event(td, 'departure', (sname, srv.version)))

    # Ensure at least one arrival is scheduled
    if not arrival_queue:
        t_next_arr = t + interarrival_time(arrival_rate)
        arrival_queue.append(Event(t_next_arr, 'arrival', None))

    # Main loop
    while (processed_arrivals < b or len(completed_jobs) < b) and (arrival_queue or evq):
        # Decide next event to process
        next_arrival_time = arrival_queue[0].time if arrival_queue else float('inf')
        next_departure_time = evq[0].time if evq else float('inf')

        if processed_arrivals >= b:
            # We cannot process more arrivals in this batch
            next_event_type = 'departure'
        else:
            # Take the earliest
            if next_arrival_time <= next_departure_time:
                next_event_type = 'arrival'
            else:
                next_event_type = 'departure'

        # Process event
        if next_event_type == 'arrival':
            ev = arrival_queue.pop(0)
            t = ev.time
            processed_arrivals += 1

            job = Job(t)
            in_flight[job.id] = job
            meanA = service_demands['A'][job.current_class]
            st = exp_sample(meanA, service_streams['A'])
            servers['A'].process_arrival(job, st, t)
            job.history.append(('A', t, None))
            schedule_departure('A', t)

            # Schedule next arrival
            t_next_arr = t + interarrival_time(arrival_rate)
            arrival_queue.append(Event(t_next_arr, 'arrival', None))

        else:  # departure
            ev = heapq.heappop(evq)
            t = ev.time
            sname, ev_version = ev.payload
            srv = servers[sname]

            job = srv.process_completion(t, ev_version)
            if job is None:
                continue  # stale event

            # Update job history
            for i in range(len(job.history) - 1, -1, -1):
                if job.history[i][0] == sname and job.history[i][2] is None:
                    job.history[i] = (job.history[i][0], job.history[i][1], t)
                    break

            schedule_departure(sname, t)

            # Routing
            nextn = next_node_after(sname, job)
            if nextn == 'CS':
                new_class = do_class_switch(job)
                mean = service_demands['A'][new_class]
                st = exp_sample(mean, service_streams['A'])
                servers['A'].process_arrival(job, st, t)
                job.history.append(('A', t, None))
                schedule_departure('A', t)

            elif nextn in ['B', 'P']:
                mean = service_demands[nextn][job.current_class]
                st = exp_sample(mean, service_streams[nextn])
                servers[nextn].process_arrival(job, st, t)
                job.history.append((nextn, t, None))
                schedule_departure(nextn, t)

            elif nextn == 'SINK':
                job.finish = t
                completed_jobs.append(job)
                in_flight.pop(job.id, None)

    # Update server stats
    for srv in servers.values():
        srv.update_progress(t)

    return completed_jobs, servers, in_flight, evq, t, arrival_queue

# -------------------------------------------------------
#                     Simulation Engine
# -------------------------------------------------------
def simulate(sim_time, arrival_rate, service_demands, service_streams):
    Job._id = 0
    t = 0.0
    evq = []

    servers = {name: PSServer(name) for name in ['A','B','P']}
    arrived_jobs = 0
    completed_jobs = []
    in_flight = {}

    def schedule_departure(sname, now):
        srv = servers[sname]
        srv.version += 1
        td = srv.next_departure_time(now)
        if td is not None:
            heapq.heappush(evq, Event(td, 'departure', (sname, srv.version)))

    # first arrival
    t_next_arr = t + interarrival_time(arrival_rate)
    heapq.heappush(evq, Event(t_next_arr, 'arrival', None))

    while evq:
        ev = heapq.heappop(evq)
        '''
        print("\n--- DEBUG: Server states ---")
        for sname, srv in servers.items():
            print(f"Server {sname}: {len(srv.jobs)} jobs")
            for j in srv.jobs:
                print(f"   Job {j.id}: remaining={j.remaining:.6f}, birth={j.birth:.4f}, class={j.current_class}")
        print("-------------------------------------------")

        print("\n--- DEBUG: Event popped ---")
        print("Current time:", t)
        print("Processing event:", ev)
        print("Remaining events in queue:")
        for e in evq:
            print("   ", e)
        '''
        t = ev.time
        if t > sim_time:
            break

        if ev.etype == 'arrival':
            arrived_jobs += 1
            job = Job(t)
            in_flight[job.id] = job
            meanA = service_demands['A'][job.current_class]
            st = exp_sample(meanA, service_streams['A'])
            servers['A'].process_arrival(job, st, t)
            job.history.append(('A', t, None))
            schedule_departure('A', t)

            # schedule next arrival
            t_next_arr = t + interarrival_time(arrival_rate)
            heapq.heappush(evq, Event(t_next_arr, 'arrival', None))

        elif ev.etype == 'departure':
            sname, ev_version = ev.payload
            srv = servers[sname]

            job = srv.process_completion(t, ev_version)
            if job is None:
                continue

            # Aggiorna la history del job
            for i in range(len(job.history) - 1, -1, -1):
                if job.history[i][0] == sname and job.history[i][2] is None:
                    job.history[i] = (job.history[i][0], job.history[i][1], t)
                    break

            schedule_departure(sname, t)

            nextn = next_node_after(sname, job)
            if nextn == 'CS':
                new_class = do_class_switch(job)
                mean = service_demands['A'][new_class]
                st = exp_sample(mean, service_streams['A'])
                servers['A'].process_arrival(job, st, t)
                job.history.append(('A', t, None))
                schedule_departure('A', t)

            elif nextn in ['B', 'P']:
                mean = service_demands[nextn][job.current_class]
                st = exp_sample(mean, service_streams[nextn])
                servers[nextn].process_arrival(job, st, t)
                job.history.append((nextn, t, None))
                schedule_departure(nextn, t)

            elif nextn == 'SINK':
                job.finish = t
                completed_jobs.append(job)
                in_flight.pop(job.id, None)

    for srv in servers.values():
        srv.update_progress(sim_time)

    n_completed = len(completed_jobs)
    avg_rt = sum(job.finish - job.birth for job in completed_jobs) / n_completed if n_completed else 0.0
    stats = {
        'completed_jobs': n_completed,
        'avg_response_time_s': avg_rt,
        'throughput_rps': n_completed / (sim_time if sim_time > 0 else 1.0)
    }
    for sname, srv in servers.items():
        util = srv.cumulative_busy_time / (sim_time if sim_time > 0 else 1.0)
        avg_n = srv.area_num_in_system / (sim_time if sim_time > 0 else 1.0)
        stats[f'{sname}_utilization'] = util
        stats[f'{sname}_avg_n'] = avg_n
        stats[f'{sname}_arrivals'] = srv.num_arrivals
        stats[f'{sname}_departures'] = srv.num_departures

    return stats, completed_jobs

def infinite_horizon_simulation(k, b):
    rngs.plantSeeds(SEED)

    # inizializzo sistema
    servers = {name: PSServer(name) for name in ['A', 'B', 'P']}
    evq = []
    in_flight = {}
    arrival_queue = []
    t = 0.0
    last_completion_time = 0.0

    batch_stats = []

    for bi in tqdm(range(k), desc="Simulation in progress...", ascii="░▒▓█", ncols=100):
        completed_batch, servers, in_flight, evq, t, arrival_queue = simulate_batch(
            b=b,
            arrival_rate=ARRIVAL_RATE,
            service_demands=SERVICE_DEMANDS,
            service_streams=SERVICE_STREAMS,
            initial_servers=servers,
            initial_evq=evq,
            initial_t=t,
            initial_in_flight=in_flight,
            initial_arrival_queue=arrival_queue
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

    # statistiche aggregate su tutti i batch
    aggregated = {}
    aggregated['mean_rt'] = sum(b['mean_rt'] for b in batch_stats) / k
    aggregated['throughput_rps'] = sum(b['throughput_rps'] for b in batch_stats) / k
    for sname in ['A', 'B', 'P']:
        aggregated[f'{sname}_util'] = sum(b[f'{sname}_util'] for b in batch_stats) / k
        aggregated[f'{sname}_avg_n'] = sum(b[f'{sname}_avg_n'] for b in batch_stats) / k
        aggregated[f'{sname}_arrivals'] = sum(b[f'{sname}_arrivals'] for b in batch_stats) / k
        aggregated[f'{sname}_departures'] = sum(b[f'{sname}_departures'] for b in batch_stats) / k

    final_state = (servers, evq, in_flight, arrival_queue, t)

    # Stampo i risultati aggregati
    print("\n=== Aggregated Statistics Over All Batches ===")
    for key, value in aggregated.items():
        print(f"{key}: {value}")

    return batch_stats, aggregated, final_state

def finite_horizon_run(stop_time, repetition, response_times_ts, num_ts):
    stats, completed_jobs = simulate(stop_time, ARRIVAL_RATE, SERVICE_DEMANDS, SERVICE_STREAMS)

    # Sort jobs by finish time
    completed_sorted = sorted(completed_jobs, key=lambda j: j.finish)

    idx = 0
    n = len(completed_sorted)

    for slot in range(num_ts):
        t_slot = slot * TS_STEP

        # include all jobs completed before t_slot
        while idx < n and completed_sorted[idx].finish <= t_slot:
            idx += 1

        if idx == 0:
            # no completed jobs yet
            response_times_ts[repetition][slot] = 0.0
        else:
            # compute average response time up to this time
            s = 0.0
            for j in completed_sorted[:idx]:
                s += (j.finish - j.birth)
            response_times_ts[repetition][slot] = s / idx

# Esegue una simulazione a orizzonte finito per un certo numero di volte
def finite_horizon_simulation(stop_time):
    rngs.plantSeeds(SEED)
    num_ts = int(stop_time // TS_STEP) + 1
    response_times_ts = [
        [0.0] * num_ts for _ in range(NUM_REPETITIONS)
    ]

    #statistics = [[0.0] * NUM_BLOCKS for _ in range(NUM_REPETITIONS)]
    #statistics_fin = [[[0.0 for _ in range(NUM_BLOCKS)] for _ in range(NUM_TIME_SLOTS)] for _ in range(NUM_REPETITIONS)]
    #repetitions_costs = [0.0] * NUM_REPETITIONS
    #continuous_delays = [[[0.0 for _ in range(NUM_BLOCKS)] for _ in range(FIVE_MINUTES_IN_DAY + 1)] for _ in range(NUM_REPETITIONS)]

    #arrivi = [0] * NUM_REPETITIONS


    for r in tqdm(range(NUM_REPETITIONS), desc="Simulation in progress...", ascii="░▒▓█", ncols=100):
        finite_horizon_run(stop_time, r, response_times_ts, num_ts)
        time.sleep(0.05)

    mean_curve = [0.0] * num_ts
    for ts in range(num_ts):
        for r in range(NUM_REPETITIONS):
            mean_curve[ts] += response_times_ts[r][ts]
        mean_curve[ts] /= NUM_REPETITIONS

    save_response_times_matrix_csv(response_times_ts, TS_STEP)
    save_mean_curve_csv(mean_curve, TS_STEP)

    #write_mean_delays_finite(continuous_delays)
    #write_delays_csv_finite(statistics_fin)
    #write_delays_csv_finite(statistics)
    #print_results_finite(repetitions_costs)

if __name__ == '__main__':
    print("Simulazione: ARRIVAL_RATE=%.3f req/s, SIM_TIME=%.0f s" % (ARRIVAL_RATE, SIM_TIME))
    stats, jobs = simulate(SIM_TIME, ARRIVAL_RATE, SERVICE_DEMANDS, SERVICE_STREAMS)
    for k, v in stats.items():
        if isinstance(v, float):
            print(f"{k}: {v:.6f}")
        else:
            print(f"{k}: {v}")
        # show un esempio history di un job completato
    if jobs:
        print("\nEsempio di job completato (history):")
        j0 = jobs[0]
        print("Job id", j0.id, "birth", j0.birth, "finish", j0.finish)
        for s, enter, leave in j0.history:
            print(f"  {s}: enter {enter:.6f}, leave {leave:.6f}")
