# Parallele Berechnung von π

## Überblick

Dieses Projekt enthält ein Python-Skript `pi.py`, das die Zahl π (Pi) mithilfe der Leibniz-Reihe approximiert. Es bietet mehrere parallele Rechenvarianten, um die Performance auf Mehrkernsystemen zu demonstrieren.

### Hauptfunktionen

- **Serielle Leibniz-Berechnung**: Summation der Leibniz-Reihe.
    
- **Leibniz-Power(10)**: Serielle Variante mit periodischen Zwischenausgaben (aber ohne Rückgabe).
    
- **GIL-Threads**: Statische Aufteilung in k Python-Threads, die feste Teilbereiche der Summation berechnen.
    
- **Producer/Consumer-Threads**: Dynamische Aufteilung per Queue, Map/Filter/Reduce in den Worker-Threads.
    
- **Numba (parallel)**: Numba-JIT-kompilierte Schleife mit `prange`, die ohne GIL in C-ähnlichem Tempo rechnet.
    
- **Thread Pool**: `ThreadPoolExecutor` teilt Aufgaben (Segmente) zu.
    
- **Process Pool (lokal)**: `multiprocessing.Pool` berechnet Segmente parallel in mehreren Prozessen.
    

## Voraussetzungen

- Python 3.7+ (empfohlen: 3.9)
    
- Installierte Pakete (siehe `requirements.txt`):
    

## Installation

1. Repository klonen oder Dateien kopieren:
    
    ```bash
    git clone https://github.com/silvancode/Projekt-PI.git
    cd Projekt-PI
    ```
    
2. Virtuelle Umgebung erstellen (empfohlen):
    
    ```bash
    python3 -m venv venv
    source venv/bin/activate   # Linux/macOS
    venv\Scripts\activate    # Windows
    ```
    
3. Abhängigkeiten installieren:
    
    ```bash
    pip install -r requirements.txt
    ```

## Aufbau von `pi.py`

Das Skript ist wie folgt strukturiert:

1. **Imports & Konstanten**
    
    - Importiert `time, math, threading, queue, numba, argparse, tabulate, functools.reduce, ThreadPoolExecutor, Pool`.
        
    - Konstanten: `MAX_ITER_DEFAULT = 100_000_000`, `BATCH_SIZE_DEFAULT = 5_000_000`.
        
2. **Producer/Consumer-Pattern**
    
    - `producer(max_iteration, batch_size)`: Teilt den Arbeitsbereich in Blöcke (`start`, `end`) und legt diese in eine `queue.Queue()`.
        
    - `consumer()`: Holt solange Tasks, berechnet Teilsummen per Map/Filter/Reduce, schreibt thread-sicher in `pi_sum_global`.
        
    - `calc_pi_producer_consumer(max_iteration, num_consumers, batch_size)`: Setzt Producer und Consumer-Threads parallel ein.
        
3. **Serielle Leibniz-Berechnung**
    
    - `calc_pi_sum(max_iteration)`: Summe der Leibniz-Reihe ohne Parallelisierung.
        
4. **Leibniz-Power-of-10-Zwischenausgaben**
    
    - `calc_pi_sum_power_10(max_iteration)`: Führt dieselbe Summation durch, gibt periodisch Laufzeit und Fehler aus, liefert aber nur das Endergebnis.
        
5. **Statische Thread-Aufteilung (GIL)**
    
    - `calc_pi_sum_thread(start, end, result_list, index)`: Berechnet Teilsumme im Bereich `[start, end)`.
        
    - `start_thread(max_iteration, num_threads)`: Teilt den gesamten Bereich in `num_threads` feste Abschnitte und startet für jeden Bereich einen Thread.
        
6. **Numba-Variante**
    
    - `calc_pi_sum_numba(max_iteration)`: Numba-JIT-kompilierte Funktion mit `prange` zum Wegfall des GIL.
        
7. **Thread Pool**
    
    - `worker_proc(task)`: Pickle-fähige Hilfsfunktion, berechnet Teilsumme für ein Task `(start, end)`.
        
    - `calc_pi_thread_pool(max_iteration, num_threads, batch_size)`: Erstellt Task-Liste, nutzt `ThreadPoolExecutor.map(worker_proc, tasks)`.
        
8. **Process Pool (lokal)**
    
    - `calc_pi_process_pool(max_iteration, num_processes, batch_size)`: Höchst ähnliche Implementierung mit `multiprocessing.Pool`, ruft ebenfalls `worker_proc` auf.
        
9. **`main()`**** & CLI-Argumente**
    
    - `-i, --iterations`: Anzahl der Iterationen (Standard: 100000000).
        
    - `--with-gil`: Statische GIL-Threads (Parameter `-t, --threads`).
        
    - `--with-thread`: Producer/Consumer-Threads (Parameter `-t, --threads`, `-s, --seg-size`).
        
    - `--with-numba`: Numba-Parallelausführung.
        
    - `--with-process`: Lokaler Process-Pool (Parameter `-p, --processes`, `-s, --seg-size`).
        
    - `--pool K`: Thread-Pool mit K Threads (Parameter `-s, --seg-size`).
        
    - `--only-pi`: Gibt nur den π-Wert aus (für externe Aufrufe); verwendet `calc_pi_process_pool`.
        
    - `-s, --seg-size`: Segmentgröße für Pool-Methoden (Standard: 5000000).
        
    - `-t, --threads`: Anzahl der Threads (Standard: 4).
        
    - `-p, --processes`: Anzahl der Prozesse (Standard: 4).
        

Am Ende sammelt `main()` alle aktivierten Methoden in `results_table` und gibt eine Tabelle aus mit Spalten:

- Methode
    
- Approximation von π
    
- Differenz zu π
    
- Zeit (s)
    

## Verwendung / Beispiele

### 1. Serielle Berechnung

```bash
python pi.py -i 1000000
```

- Näherung mit 1 000 000 Iterationen (Leibniz), zeigt Differenz und Laufzeit.
    

### 2. Power-of-10-Zwischenausgaben

```bash
python pi.py -i 1000000
```

- Führt dieselbe serielle Summation durch, zeigt periodisch Laufzeit und Fehler, liefert Endergebnis.
    

### 3. GIL-Threads (z. B. 4 Threads)

```bash
python pi.py -i 5000000 --with-gil -t 4
```

- Teilt 5 000 000 Iterationen auf 4 Threads auf.
    

### 4. Producer/Consumer-Threads (z. B. 4 Threads, Segmentsize 1 000 000)

```bash
python pi.py -i 10000000 --with-thread -t 4 -s 1000000
```

- Bildet Segmente zu je 1 000 000 Iterationen, verteilt dynamisch auf 4 Threads.
    

### 5. Numba (parallel)

```bash
python pi.py -i 2000000 --with-numba
```

- Rechnet 2 000 000 Iterationen parallel ohne GIL.
    

### 6. Thread-Pool (K = 8, Segmentsize 500 000)

```bash
python pi.py -i 8000000 --pool 8 -s 500000
```

- Zerlegt in 16 Segmente à 500 000, rechnet mit 8 Threads.
    

### 7. Process-Pool (p = 4, Segmentsize 2 000 000)

```bash
python pi.py -i 8000000 --with-process -p 4 -s 2000000
```

- Zerlegt in 4 Segmente à 2 000 000, rechnet mit 4 Prozessen.
    

### 8. Nur π-Wert ausgeben (für externe Aufrufe)

```bash
python pi.py -i 5000000 --only-pi
```

- Gibt nur eine Fließkommazahl mit π-Wert zurück, ohne Tabelle.
    

## Projektstruktur

```
Projekt-Parallel-PI/
├── pi.py                  # Hauptskript
├── requirements.txt       # Python-Abhängigkeiten
└── README.md              # Dokumentation
```

---
