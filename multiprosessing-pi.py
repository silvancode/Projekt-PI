import math
import time
from multiprocessing import Process, Manager, Queue

def partial_sum(start: int, end: int, out_q: Queue):
    """Berechnet die Leibniz-Summe von Index start bis end-1 und legt das Ergebnis in out_q."""
    s = 0.0
    for i in range(start, end):
        k = 2*i + 1
        s += (-1.0 if (i % 2) else 1.0) * 4.0 / k
    out_q.put(s)

def calc_pi_with_processes(total_iterations: int, n_procs: int) -> float:
    chunk = total_iterations // n_procs
    manager = Manager()
    queue = manager.Queue()
    processes = []
    
    # Erzeuge und starte die Prozesse
    for i in range(n_procs):
        start = i * chunk
        end = (i+1) * chunk if i < n_procs-1 else total_iterations
        p = Process(target=partial_sum, args=(start, end, queue))
        p.start()
        processes.append(p)
    
    # Warte, bis alle fertig sind
    for p in processes:
        p.join()
    
    # Sammle alle Teilsummen
    total = 0.0
    while not queue.empty():
        total += queue.get()
    return total

if __name__ == "__main__":
    N = 1_000_000
    P = 4
    t0 = time.perf_counter()
    pi_approx = calc_pi_with_processes(N, P)
    dt = time.perf_counter() - t0

    print(f"Annäherung: {pi_approx:.20f}")
    print(f"Abweichung: {pi_approx - math.pi:.3e}")
    print(f"Benötigte Zeit: {dt:.2f} s mit {P} Prozessen")

from multiprocessing import Pool

def part(args):
    start, end = args
    s = 0.0
    for i in range(start, end):
        s += (-1.0 if i%2 else 1.0)*4.0/(2*i+1)
    return s

if __name__ == "__main__":
    with Pool() as pool:
        ranges = [(i * (N // P), (i + 1) * (N // P) if i < P - 1 else N) for i in range(P)]
        parts = pool.map(part, ranges, chunksize=1<<10)
    pi = math.fsum(parts)
