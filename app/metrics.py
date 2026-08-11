from __future__ import annotations

from collections import defaultdict, deque
from statistics import fmean
from time import monotonic


class AppMetrics:
    """Lightweight in-memory operational metrics with no database writes."""

    def __init__(self) -> None:
        self.started_at = monotonic()
        self.counters: dict[str, int] = defaultdict(int)
        self.durations: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=200))

    def increment(self, name: str, amount: int = 1) -> None:
        self.counters[name] += amount

    def observe(self, name: str, seconds: float) -> None:
        self.durations[name].append(max(0.0, float(seconds)))

    def snapshot(self) -> dict[str, object]:
        timings = {}
        for name, values in self.durations.items():
            if values:
                timings[name] = {
                    "avg_ms": round(fmean(values) * 1000, 1),
                    "max_ms": round(max(values) * 1000, 1),
                    "samples": len(values),
                }
        return {
            "uptime_seconds": int(monotonic() - self.started_at),
            "counters": dict(self.counters),
            "timings": timings,
        }


metrics = AppMetrics()
