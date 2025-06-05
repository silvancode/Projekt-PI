import time
import math
import threading
import queue
import numba
import argparse
from tabulate import tabulate
from functools import reduce
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool

# Standardwerte für Anzahl Iterationen und Segmentgröße
MAX_ITER_DEFAULT = 100_000_000
BATCH_SIZE_DEFAULT = 5_000_000

# Globale Queue und Variable für Producer/Consumer-Muster
task_queue = queue.Queue()
pi_sum_global = 0.0
pi_lock = threading.Lock()

def producer(max_iteration, batch_size):
    """
    Teilt den Arbeitsbereich in Blöcke auf und legt diese als Tasks in die Queue.

    Jeder Task ist ein Tupel (start, end), das den Bereich [start, end) kennzeichnet.
    """
    num_batches = (max_iteration + batch_size - 1) // batch_size
    for batch_idx in range(num_batches):
        start = batch_idx * batch_size
        end = min((batch_idx + 1) * batch_size, max_iteration)
        task_queue.put((start, end))

def consumer():
    """
    Holt fortlaufend Tasks aus der Task-Queue und berechnet die Teilsummen.

    Verwendet dabei map, filter und reduce, um jeden Block effizient zu summieren.
    """
    global pi_sum_global

    while True:
        try:
            start, end = task_queue.get(block=False)
        except queue.Empty:
            break

        # Iterator über Indizes im aktuellen Intervall
        indices = range(start, end)
        # Filter (hier kein tatsächlicher Ausschluss)
        filtered_indices = filter(lambda i: True, indices)
        # Map: Berechnet für jeden Index i den Term (-1)^i * 4/(2*i + 1)
        mapped_terms = map(lambda i: ((-1 if i % 2 else 1) * 4.0 / (2 * i + 1)), filtered_indices)
        # Reduce: Summiert alle Terme des Blocks
        local_sum = reduce(lambda a, b: a + b, mapped_terms, 0.0)

        # Sicheres Hinzufügen zur globalen Summe
        with pi_lock:
            pi_sum_global += local_sum

        task_queue.task_done()

def calc_pi_producer_consumer(max_iteration, num_consumers=4, batch_size=BATCH_SIZE_DEFAULT):
    """
    Führt das Producer/Consumer-Pattern aus:
    1. Producer stellt Tasks in die Queue.
    2. Mehrere Consumer-Threads holen Tasks und berechnen Teilsummen.
    3. Rückgabe der Gesamtsumme von π.
    """
    global pi_sum_global
    pi_sum_global = 0.0  # Zurücksetzen vor neuem Lauf

    # Producer legt alle Tasks in die Queue
    producer(max_iteration, batch_size)

    # Starte Consumer-Threads
    threads = []
    for _ in range(num_consumers):
        t = threading.Thread(target=consumer)
        threads.append(t)
        t.start()

    # Warten bis alle Threads fertig sind
    for t in threads:
        t.join()

    return pi_sum_global


def calc_pi_sum(max_iteration):
    """
    Berechnet π seriell über die Leibniz-Reihe.

    sum = sum_{i=0..max_iteration-1} (-1)^i * 4/(2*i + 1)
    """
    k = 1
    total = 0.0
    for i in range(max_iteration):
        total += (-1 if (i % 2) else 1) * 4.0 / k
        k += 2
    return total


def relativ_error(measured_value):
    """
    Berechnet den relativen Prozentfehler gegenüber math.pi.
    """
    return 100 * (math.pi - measured_value) / measured_value
 
def calc_pi_sum_power_10(max_iteration):
    """
    Berechnet π serielle via Leibniz-Reihe, gibt Zwischenergebnisse bei 10^exponent-Schritten aus.

    Die Funktion führt die gleiche Summation durch, aktualisiert aber
    ergänzend Laufzeit und Fehler in regelmäßigen Abständen.
    """
    k = 1
    total = 0.0
    exponent = 0
    t = time.process_time_ns()
    for i in range(max_iteration):
        total += (-1 if (i % 2) else 1) * 4.0 / k
        k += 2
        if (i % (10 ** exponent)) == 0:
            exponent += 1
            # Zwischenergebnisse (können ignoriert werden)
            elapsed_time = (time.process_time_ns() - t) * 1e-9
            diff = math.pi - total
            quotient = total / math.pi
            rel_err = relativ_error(total)
            t = time.process_time_ns()
    # Letztes Segment (wird nicht weiter ausgegeben)
    return total


def calc_pi_sum_thread(start_iteration, max_iteration, result_list, index):
    """
    Hilfsfunktion für statische Thread-Aufteilung:
    Berechnet Teilsumme von start_iteration bis max_iteration-1 und speichert in result_list[index].
    """
    length = max_iteration - start_iteration
    k = 1 + 2 * start_iteration
    sum_val = 0.0
    for i in range(length):
        j = start_iteration + i
        sum_val += ((-1) if (j % 2) else 1) * 4.0 / k
        k += 2
    result_list[index] = sum_val


def start_thread(max_iteration, num_threads=4):
    """
    Statische Aufteilung in num_threads Abschnitte:
    Jeder Thread berechnet einen Fixbereich der Leibniz-Summe.
    """
    threads = []
    results = [0.0] * num_threads  # Platz für Teilsummen

    for i in range(num_threads):
        start = i * (max_iteration // num_threads)
        end = (i + 1) * (max_iteration // num_threads) if i < num_threads - 1 else max_iteration
        t = threading.Thread(
            target=calc_pi_sum_thread,
            args=(start, end, results, i)
        )
        threads.append(t)
        t.start()

    for thread in threads:
        thread.join()

    return sum(results)

@numba.njit(parallel=True)
def calc_pi_sum_numba(max_iteration):
    """
    Numba-basierte Berechnung ohne GIL:
    Nutzt prange für parallele Schleife.
    """
    sum_val = 0.0
    for i in numba.prange(max_iteration):
        k = 2 * i + 1
        sign = -1 if (i % 2) else 1
        sum_val += sign * 4.0 / k
    return sum_val

# Pickle-fähige Worker-Funktion für Pools
def worker_proc(task):
    """
    Berechnet Teilsumme für den Bereich [start, end).
    """
    start, end = task
    local = 0.0
    k = 1 + 2 * start
    for i in range(start, end):
        sign = -1 if (i % 2) else 1
        local += sign * 4.0 / k
        k += 2
    return local


def calc_pi_thread_pool(max_iteration, num_threads=4, batch_size=BATCH_SIZE_DEFAULT):
    """
    Berechnet π mithilfe eines ThreadPool:
    Zerlegt die Gesamtiteration in Segmente (Segmente = batch_size) und nutzt executor.map.
    """
    tasks = []
    num_batches = (max_iteration + batch_size - 1) // batch_size
    for batch_idx in range(num_batches):
        start = batch_idx * batch_size
        end = min((batch_idx + 1) * batch_size, max_iteration)
        tasks.append((start, end))

    total = 0.0
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for partial in executor.map(worker_proc, tasks):
            total += partial
    return total


def calc_pi_process_pool(max_iteration, num_processes=4, batch_size=BATCH_SIZE_DEFAULT):
    """
    Berechnet π mithilfe eines lokalen ProcessPool:
    Zerlegt die Gesamtiteration in Segmente und nutzt multiprocessing.Pool.
    """
    tasks = []
    num_batches = (max_iteration + batch_size - 1) // batch_size
    for batch_idx in range(num_batches):
        start = batch_idx * batch_size
        end = min((batch_idx + 1) * batch_size, max_iteration)
        tasks.append((start, end))

    total = 0.0
    with Pool(processes=num_processes) as pool:
        for partial in pool.map(worker_proc, tasks):
            total += partial
    return total


def main():
    parser = argparse.ArgumentParser(description="Parallele Berechnung von π mit unterschiedlichen Methoden.")
    parser.add_argument('-i', '--iterations', type=int, default=MAX_ITER_DEFAULT,
                        help='Anzahl Iterationen der Leibniz-Reihe (Standard: 100000000)')
    parser.add_argument('--with-gil', action='store_true', help='Berechne statisch auf k GIL-Threads')
    parser.add_argument('--with-thread', action='store_true', help='Producer/Consumer-Threads nutzen')
    parser.add_argument('--with-numba', action='store_true', help='Berechnung mit Numba (parallel, ohne GIL)')
    parser.add_argument('--with-process', action='store_true', help='Berechnung mit lokalem Process-Pool')
    parser.add_argument('--pool', type=int, metavar='K', help='Thread-Pool mit K Threads nutzen')
    parser.add_argument('--hosts', type=str, help='**Nicht funktionsfähig**: Verteilt auf mehrere Hosts')
    parser.add_argument('--only-pi', action='store_true', help='Nur den π-Wert ausgeben (für Remote-Aufrufe)')
    parser.add_argument('-s', '--seg-size', type=int, default=BATCH_SIZE_DEFAULT,
                        help='Segmentgröße für Thread/Process-Pool (Standard: 5000000)')
    parser.add_argument('-t', '--threads', type=int, default=4, help='Anzahl Threads (Standard: 4)')
    parser.add_argument('-p', '--processes', type=int, default=4, help='Anzahl Prozesse (Standard: 4)')
    args = parser.parse_args()

    max_iter = args.iterations
    batch_size = args.seg_size
    num_threads = args.threads
    num_processes = args.processes

    # Wenn nur π-Wert ausgegeben werden soll, nutzen wir den lokalen Process-Pool
    if args.only_pi:
        pi_only = calc_pi_process_pool(max_iter, num_processes, batch_size)
        print(f"{pi_only:.20f}")
        return

    results_table = []

    # 1. Serielle Leibniz-Berechnung
    t0 = time.process_time()
    pi_basic = calc_pi_sum(max_iter)
    dt0 = time.process_time() - t0
    diff0 = math.pi - pi_basic
    results_table.append(("Leibniz (seriell)", pi_basic, diff0, dt0))

    # 2. Leibniz mit Power-of-10-Zwischenausgaben (Fehlende Rückgabe)
    t1 = time.process_time()
    pi_pow10 = calc_pi_sum(max_iter)  # Platzhalter: gleiche Funktion wie seriell
    dt1 = time.process_time() - t1
    diff1 = math.pi - pi_pow10
    results_table.append(("Leibniz-Power(10)", pi_pow10, diff1, dt1))

    # 3. Statistische GIL-Threads
    if args.with_gil:
        t2 = time.process_time()
        pi_gil = start_thread(max_iter, num_threads)
        dt2 = time.process_time() - t2
        diff2 = math.pi - pi_gil
        results_table.append((f"GIL-Threads (k={num_threads})", pi_gil, diff2, dt2))

    # 4. Producer/Consumer-Threads
    if args.with_thread:
        t3 = time.process_time()
        pi_pc = calc_pi_producer_consumer(max_iter, num_threads, batch_size)
        dt3 = time.process_time() - t3
        diff3 = math.pi - pi_pc
        results_table.append((f"Producer/Consumer (k={num_threads})", pi_pc, diff3, dt3))

    # 5. Numba (parallel, ohne GIL)
    if args.with_numba:
        t4 = time.process_time()
        pi_numba = calc_pi_sum_numba(max_iter)
        dt4 = time.process_time() - t4
        diff4 = math.pi - pi_numba
        results_table.append(("Numba (parallel)", pi_numba, diff4, dt4))

    # 6. Thread-Pool
    if args.pool:
        t5 = time.process_time()
        pi_pool = calc_pi_thread_pool(max_iter, args.pool, batch_size)
        dt5 = time.process_time() - t5
        diff5 = math.pi - pi_pool
        results_table.append((f"Thread-Pool (K={args.pool})", pi_pool, diff5, dt5))

    # 7. Lokaler Process-Pool
    if args.with_process:
        t6 = time.process_time()
        pi_proc = calc_pi_process_pool(max_iter, num_processes, batch_size)
        dt6 = time.process_time() - t6
        diff6 = math.pi - pi_proc
        results_table.append((f"Process-Pool (p={num_processes})", pi_proc, diff6, dt6))

    # Hinweis: Mehrere Hosts-Funktion ist nicht implementiert und wird ignoriert

    # Ausgabe der Ergebnisse
    headers = ["Methode", "Approximation von π", "Differenz zu π", "Zeit (s)"]
    print(tabulate(results_table, headers=headers, floatfmt=".20f"))

if __name__ == "__main__":
    main()
