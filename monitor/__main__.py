import argparse, time, traceback
from .runner import main as run_once

def run_forever(interval: int):
    while True:
        try:
            run_once()
        except Exception:
            traceback.print_exc()
        time.sleep(interval)

def parse_args():
    p = argparse.ArgumentParser(description="Alpes Site Monitor")
    p.add_argument("--interval", type=int, default=0,
                   help="Intervalo em segundos entre execuções. 0 = roda uma vez e sai.")
    return p.parse_args()

def main():
    args = parse_args()
    if args.interval and args.interval > 0:
        run_forever(args.interval)
    else:
        run_once()

if __name__ == "__main__":
    main()
