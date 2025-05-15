import time
import math
import threading
import numba
import numpy as np
from tabulate import tabulate

from pi_leibnitz import calc_pi_sum, calc_pi_sum_power_10

def calc_pi_sum_thread(start_iteration, max_iteration, result_list, index):
    iteration = max_iteration - start_iteration
    k = 1 + 2*start_iteration
    sum = 0
    for i in range(iteration):
        j = start_iteration + i
        sum = sum + (-1 if (j%2) else +1)*4/k
        k = k+2
    result_list[index] = sum

def start_thread(max_iteration):
    threads = []
    results = [0] * 4  # Shared list to store results from threads

    # Start 4 threads, each calculating a part of the sum
    # Each thread will calculate the sum for 1 million iterations
    for i in range(0, 4):
        t = threading.Thread(target=calc_pi_sum_thread, args=(i*max_iter, (i+1)*max_iter, results, i))
        threads.append(t)
        t.start()

    for thread in threads:
        thread.join()

    total_sum = sum(results)
    return total_sum


@numba.njit(parallel=True)
def calc_pi_sum_numba(max_iteration):
    sum = 0.0
    for i in numba.prange(max_iteration):
        k = 2 * i + 1
        sign = -1 if i % 2 else 1
        sum += sign * 4.0 / k
    return sum


if __name__ == "__main__":
    max_iter = 100_000_000

    # Pi Approximation
    t = time.process_time()
    pi_approx = calc_pi_sum(max_iter)
    dt = time.process_time() - t
    diff = math.pi - pi_approx

    # Pi Approximation mit Power(10)
    t_pow10 = time.process_time()
    pi_pow10_approx = calc_pi_sum_power_10(max_iter)
    dt_pow10 = time.process_time() - t_pow10
    diff_power_10 = math.pi - pi_pow10_approx

    # GIL-Threads Approximation
    t1 = time.process_time()
    gil_pi_approx = start_thread(max_iter)
    dt1 = time.process_time() - t1
    diff_gil = math.pi - gil_pi_approx

    # Numba-Threads Approximation
    t2 = time.process_time()
    numba_pi_approx = calc_pi_sum_numba(max_iter)
    dt2 = time.process_time() - t2
    diff_numba = math.pi - numba_pi_approx

    # Tabellarische Ausgabe
    table = [
        ["Leibniz", pi_approx, diff, dt],
        ["Leibniz-Power(10)", pi_pow10_approx, diff_power_10, dt_pow10],
        ["GIL-Threads", gil_pi_approx, diff_gil, dt1],
        ["Numba-Threads", numba_pi_approx, diff_numba, dt2]
    ]
    headers = ["Methode", "Approximation von π", "Differenz zu π", "Zeit (Sekunden)"]

    print(tabulate(table, headers=headers, floatfmt=".20f"))