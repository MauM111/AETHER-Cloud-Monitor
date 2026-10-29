#!/usr/bin/env python3
"""AETHER repeatable CPU alert test (standard library only).

Run it on the same machine as AETHER (the Ubuntu VM) while aether_cloud_monitor.py is running:

    python3 latency_test.py --runs 3 --load-seconds 20

For each run it records the exact start time of a CPU load, how long AETHER takes to report
CRITICAL (detection delay) and how long it takes to return to NORMAL after the load stops
(recovery time). Results are printed and saved to latency_results.csv.
"""
import argparse
import csv
import json
import multiprocessing
import time
import urllib.request
from datetime import datetime


def burn(seconds):
    end = time.time() + seconds
    while time.time() < end:
        pass


def get_status(url):
    with urllib.request.urlopen(url, timeout=3) as r:
        return json.load(r)


def wait_for(url, wanted, timeout, poll):
    """Poll until status == wanted. Returns (seconds_waited, peak_cpu) or (None, peak_cpu)."""
    start, peak = time.time(), 0.0
    while time.time() - start < timeout:
        d = get_status(url)
        peak = max(peak, d.get('cpu', 0.0))
        if d.get('status') == wanted:
            return time.time() - start, peak
        time.sleep(poll)
    return None, peak


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', default='http://127.0.0.1:5000/api/status')
    ap.add_argument('--runs', type=int, default=3)
    ap.add_argument('--load-seconds', type=int, default=20)
    ap.add_argument('--poll', type=float, default=0.25)
    ap.add_argument('--rest', type=int, default=15, help='seconds to rest between runs')
    ap.add_argument('--out', default='latency_results.csv')
    a = ap.parse_args()

    print('Waiting for AETHER to report NORMAL before starting...')
    if wait_for(a.url, 'normal', 60, a.poll)[0] is None:
        raise SystemExit('AETHER did not report NORMAL within 60 s - check the service.')

    rows = []
    for n in range(1, a.runs + 1):
        cores = multiprocessing.cpu_count()
        procs = [multiprocessing.Process(target=burn, args=(a.load_seconds,)) for _ in range(cores)]
        t0 = time.time()
        start_clock = datetime.fromtimestamp(t0).strftime('%H:%M:%S')
        for p in procs:
            p.start()
        detect, peak = wait_for(a.url, 'critical', a.load_seconds + 10, a.poll)
        for p in procs:
            p.join()
        t_load_end = time.time()
        recover, _ = wait_for(a.url, 'normal', 60, a.poll)
        rec = None if recover is None else round(time.time() - t_load_end, 1)
        rows.append({'run': n, 'load_start': start_clock, 'cores_loaded': cores,
                     'peak_cpu_seen': peak,
                     'detection_s': None if detect is None else round(detect, 1),
                     'recovery_s': rec})
        print(rows[-1])
        if n < a.runs:
            time.sleep(a.rest)

    with open(a.out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    det = [r['detection_s'] for r in rows if r['detection_s'] is not None]
    rec = [r['recovery_s'] for r in rows if r['recovery_s'] is not None]
    print('\nRun | load start | cores | peak CPU | detection (s) | recovery (s)')
    for r in rows:
        print(f"{r['run']:>3} | {r['load_start']} | {r['cores_loaded']:>5} | {r['peak_cpu_seen']:>8} | {str(r['detection_s']):>13} | {str(r['recovery_s']):>12}")
    if det:
        print(f"\nDetection: min {min(det)} / mean {sum(det)/len(det):.1f} / max {max(det)} s")
    if rec:
        print(f"Recovery:  min {min(rec)} / mean {sum(rec)/len(rec):.1f} / max {max(rec)} s")
    print(f'Saved {a.out}')


if __name__ == '__main__':
    main()
