# -------------------------------------------------------
#               Job and Event Definitions
# -------------------------------------------------------
class Event:
    __slots__ = ("time", "etype", "payload")

    def __init__(self, time, etype, payload):
        self.time = time
        self.etype = etype
        self.payload = payload

    def __lt__(self, other):
        return self.time < other.time

    def __repr__(self):
        return f"Event(time={self.time}, etype={self.etype}, payload={self.payload})"

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
        self.server_times = {}
        self.visit_count = {}


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
        self.num_arrivals = 0
        self.num_departures = 0
        self.version = 0

    def update_progress(self, now):
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

    def process_arrival(self, job, service_time):
        job.remaining = service_time
        job.server = self.name
        self.jobs.append(job)
        self.num_arrivals += 1

    def _remove_job(self, job):
        if job in self.jobs:
            self.jobs.remove(job)
        self.num_departures += 1
        job.server = None

    def process_completion(self, ev_version):
        if ev_version != self.version:
            return None

        job = self._job_to_complete()
        if job is None:
            return None

        self._remove_job(job)

        return job

    def next_departure_time(self, now):
        if not self.jobs:
            return None
        n = len(self.jobs)
        min_time = min(job.remaining * n for job in self.jobs)
        return now + min_time

    def _job_to_complete(self):
        return min(self.jobs, key=lambda j: j.remaining) if self.jobs else None

    def reset_statistics(self):
        self.cumulative_busy_time = 0.0
        self.area_num_in_system = 0.0
        self.num_arrivals = 0
        self.num_departures = 0