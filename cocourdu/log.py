"""Timestamped logger + a tiny progress tracker with ETA, for long Colab runs."""
import logging
import sys
import time


def get_logger(name: str = "cocourdu") -> logging.Logger:
    log = logging.getLogger(name)
    if not log.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(message)s", datefmt="%H:%M:%S"))
        log.addHandler(h); log.setLevel(logging.INFO); log.propagate = False
    return log


class Progress:
    """Call .step(n_done_in_step) after each chunk; logs rate, elapsed, ETA."""

    def __init__(self, total: int, log: logging.Logger, unit: str = "rows"):
        self.total, self.log, self.unit, self.done, self.t0 = total, log, unit, 0, time.time()

    def step(self, n: int, label: str = ""):
        self.done += n
        el = time.time() - self.t0
        rate = self.done / el if el else 0
        eta = (self.total - self.done) / rate if rate else float("inf")
        self.log.info(f"{label} {self.done:,}/{self.total:,} {self.unit} ({self.done / self.total:.1%}) · "
                      f"{rate:.1f} {self.unit}/s · elapsed {el / 60:.1f} min · ETA {eta / 60:.1f} min")
