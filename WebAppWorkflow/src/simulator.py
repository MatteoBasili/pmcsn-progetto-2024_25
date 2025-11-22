import heapq
import time
from collections import namedtuple

from tqdm import tqdm

from lib.DES import rngs
from sim_config import SIM_TIME, ARRIVAL_RATE, service_demands, SERVICE_STREAMS, NUM_REPETITIONS, SEED, TS_STEP
from .utils import exp_sample, interarrival_time, next_node_after, do_class_switch, print_line, \
    save_response_times_matrix_csv, save_mean_curve_csv

# -------------------------------------------------------
#               Job and Event Definitions
# -------------------------------------------------------
Event = namedtuple('Event', ['time', 'etype', 'payload'])

class Job:
    _id = 0
    def __init__(self, t_arrival):
        self.id = Job._id; Job._id += 1
        self.birth = t_arrival
        self.current_class = 'Class1'
        self.history = []
        self.remaining = None
        self.server = None
        self.finish = None


# -------------------------------------------------------
#                   Processor-Sharing Node
# -------------------------------------------------------
class PSServer:
    def __init__(self, name):
        self.name = name
        self.jobs = []
        self.last_t = 0.0
        self.cumulative_busy_time = 0.0
        self.area_num_in_system = 0.0
        self.total_service_time = 0.0
        self.num_arrivals = 0
        self.num_departures = 0
        self.version = 0

    def _update_progress(self, now):
        dt = now - self.last_t
        if dt <= 0:
            self.last_t = now
            return
        n = len(self.jobs)
        if n > 0:
            per_job = dt / n
            for job in self.jobs:
                job.remaining -= per_job
            self.cumulative_busy_time += dt
        self.area_num_in_system += n * dt
        self.last_t = now

    def arrival(self, job, service_time, now):
        self._update_progress(now)
        job.remaining = service_time
        job.server = self.name
        self.jobs.append(job)
        self.num_arrivals += 1

    def remove_job(self, job, now):
        self._update_progress(now)
        if job in self.jobs:
            self.jobs.remove(job)
        self.num_departures += 1
        job.server = None

    def next_departure_time(self, now):
        if not self.jobs:
            return None
        n = len(self.jobs)
        min_time = min(job.remaining * n for job in self.jobs)
        return now + min_time

    def job_to_complete(self):
        return min(self.jobs, key=lambda j: j.remaining) if self.jobs else None


# -------------------------------------------------------
#                     Simulation Engine
# -------------------------------------------------------
def simulate(sim_time, arrival_rate, service_demands, service_streams):
    Job._id = 0
    t = 0.0
    evq = []

    servers = {name: PSServer(name) for name in ['A','B','P']}
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
        t = ev.time
        if t > sim_time:
            break

        if ev.etype == 'arrival':
            job = Job(t)
            in_flight[job.id] = job
            meanA = service_demands['A']['Class1']
            st = exp_sample(meanA, service_streams['A'])
            servers['A'].arrival(job, st, t)
            job.history.append(('A', t, None))
            schedule_departure('A', t)

            # schedule next arrival
            t_next_arr = t + interarrival_time(arrival_rate)
            heapq.heappush(evq, Event(t_next_arr, 'arrival', None))

        elif ev.etype == 'departure':
            sname, ev_version = ev.payload
            srv = servers[sname]
            if ev_version != srv.version:
                continue

            srv._update_progress(t)
            job = srv.job_to_complete()
            if job is None:
                continue

            srv.remove_job(job, t)
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
                servers['A'].arrival(job, st, t)
                job.history.append(('A', t, None))
                schedule_departure('A', t)

            elif nextn in ['B', 'P']:
                mean = service_demands[nextn][job.current_class]
                st = exp_sample(mean, service_streams[nextn])
                servers[nextn].arrival(job, st, t)
                job.history.append((nextn, t, None))
                schedule_departure(nextn, t)

            elif nextn == 'SINK':
                job.finish = t
                completed_jobs.append(job)
                in_flight.pop(job.id, None)

    for srv in servers.values():
        srv._update_progress(sim_time)

    n_completed = len(completed_jobs)
    avg_rt = sum(job.finish - job.birth for job in completed_jobs) / n_completed if n_completed else 0.0
    stats = {
        'completed_jobs': n_completed,
        'avg_response_time_s': avg_rt,
        'throughput_rps': n_completed / sim_time
    }
    for sname, srv in servers.items():
        util = srv.cumulative_busy_time / sim_time
        avg_n = srv.area_num_in_system / sim_time
        stats[f'{sname}_utilization'] = util
        stats[f'{sname}_avg_n'] = avg_n
        stats[f'{sname}_arrivals'] = srv.num_arrivals
        stats[f'{sname}_departures'] = srv.num_departures

    return stats, completed_jobs

def finite_horizon_run(stop_time, repetition, response_times_ts, num_ts):
    stats, completed_jobs = simulate(stop_time, ARRIVAL_RATE, service_demands, SERVICE_STREAMS)

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

# Esegue una simulazione ad orizzonte finito per un certo numero di volte
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
    stats, jobs = simulate(SIM_TIME, ARRIVAL_RATE, service_demands, SERVICE_STREAMS)
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
