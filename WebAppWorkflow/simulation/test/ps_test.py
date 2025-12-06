from src.entities import PSServer, Job


def test_processor_sharing():
    print("\n===========================")
    print(f"TEST PROCESSOR SHARING (PS)")
    print("===========================\n")


    # -------------------------
    # CASO 1 — 1 JOB
    # -------------------------
    srv = PSServer("A")
    j1 = Job(0.0)
    service_time = 10.0
    print(f">>> CASO 1: 1 job (ID = {j1.id}) nel server {srv.name} con tempo di servizio pari a {service_time} secondi\n")

    srv.process_arrival(j1, service_time)

    print("[Avanziamo nel tempo di 5 secondi]\n")
    delta_t = 5.0
    srv.update_progress(delta_t)

    print("--> Valori attesi:")
    print("-   Remaining = 5.0")
    print("-   Next departure time = 10.0")
    print("-   Job to complete = 0\n")

    print("--> Risultati:")
    print("-   Remaining:", j1.remaining)
    print("-   Next departure time at:", srv.next_departure_time(delta_t))
    print("-   Job to complete:", srv._job_to_complete().id, "\n")

    print("---------------------------\n")


    # -------------------------
    # CASO 2 — 2 JOB
    # -------------------------
    srv = PSServer("B")
    j1 = Job(0.0)
    j2 = Job(0.0)
    service_time1 = 15.0
    service_time2 = 10.0
    print(f">>> CASO 2: 2 job che arrivano al server {srv.name} nello stesso istante")
    print(f"-   Primo job (ID = {j1.id}) con tempo di servizio pari a {service_time1} secondi")
    print(f"-   Secondo job (ID = {j2.id}) con tempo di servizio pari a {service_time2} secondi\n")

    srv.process_arrival(j1, service_time1)
    srv.process_arrival(j2, service_time2)

    print("[Avanziamo nel tempo di 10 secondi]\n")
    delta_t = 10.0
    srv.update_progress(delta_t)

    print("--> Valori attesi:")
    print("-   Remaining (Job 1, Job 2) = (10.0, 5.0)")
    print("-   Next departure time = 20.0")
    print("-   Job to complete = 2\n")

    print("--> Risultati:")
    print(f"-   Remaining (Job 1, Job 2): ({j1.remaining}, {j2.remaining})")
    print("-   Next departure time at:", srv.next_departure_time(delta_t))
    print("-   Job to complete:", srv._job_to_complete().id, "\n")

    print("---------------------------\n")


    # -------------------------
    # CASO 3 — 3 JOB
    # -------------------------
    srv = PSServer("P")
    t1 = 0.0
    t2 = 0.8
    t3 = 1.3
    j1 = Job(t1)
    j2 = Job(t2)
    j3 = Job(t3)
    service_time1 = 7.6
    service_time2 = 8.0
    service_time3 = 6.5
    print(f">>> CASO 3: 3 job nel server {srv.name}")
    print(f"-   Primo job (ID = {j1.id}), con tempo di servizio pari a {service_time1} secondi, arriva all'istante {t1} (s)")
    print(f"-   Secondo job (ID = {j2.id}) con tempo di servizio pari a {service_time2} secondi, arriva all'istante {t2} (s)")
    print(f"-   Terzo job (ID = {j3.id}) con tempo di servizio pari a {service_time3} secondi, arriva all'istante {t3} (s)\n")

    srv.process_arrival(j1, service_time1)

    print("[Avanziamo nel tempo di 13 secondi]\n")
    delta_t = 13.0
    srv.update_progress(t2)
    srv.process_arrival(j2, service_time2)
    srv.update_progress(t3)
    srv.process_arrival(j3, service_time3)
    srv.update_progress(delta_t)

    print("--> Valori attesi:")
    print("-   Remaining (Job 1, Job 2, Job 3) = (2.65, 3.85, 2.6)")
    print("-   Next departure time = 20.8")
    print("-   Job to complete = 5\n")

    print("--> Risultati:")
    print(f"-   Remaining (Job 1, Job 2, Job 3): ({j1.remaining}, {j2.remaining}, {j3.remaining})")
    print("-   Next departure time at:", srv.next_departure_time(delta_t))
    print("-   Job to complete:", srv._job_to_complete().id, "\n")

    print("---------------------------\n")

    print("✅ Test Processor Sharing completato.\n")


# Esegui il test
test_processor_sharing()
