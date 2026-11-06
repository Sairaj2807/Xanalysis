"""Minimal interval scheduler with per-job status. Data refresh and model retraining have SEPARATE intervals."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

log = logging.getLogger(__name__)


@dataclass
class Job:
    name: str
    interval_s: float
    fn: Callable[[], object]
    next_run: float = 0.0
    last_status: str = "never"
    last_error: str | None = None
    runs: int = 0
    failures: int = 0


@dataclass
class Scheduler:
    jobs: dict[str, Job] = field(default_factory=dict)
    clock: Callable[[], float] = time.time

    def add(self, name: str, interval_s: float, fn: Callable[[], object], start_delay_s: float = 0.0) -> None:
        self.jobs[name] = Job(name, interval_s, fn, next_run=self.clock() + start_delay_s)

    def tick(self) -> list[str]:
        """Run every job that is due. A failing job never stops the others and is retried at its next interval."""
        ran = []
        now = self.clock()
        for j in self.jobs.values():
            if now < j.next_run:
                continue
            try:
                j.fn()
                j.last_status, j.last_error = "ok", None
            except Exception as e:                           # noqa: BLE001 - isolate job failures
                j.last_status, j.last_error = "failed", str(e)
                j.failures += 1
                log.error("job %s failed: %s", j.name, e)
            j.runs += 1
            j.next_run = now + j.interval_s
            ran.append(j.name)
        return ran

    def status(self) -> dict[str, dict]:
        return {n: {"status": j.last_status, "runs": j.runs, "failures": j.failures, "error": j.last_error,
                    "next_run": datetime.fromtimestamp(j.next_run, timezone.utc).isoformat()}
                for n, j in self.jobs.items()}

    def run_forever(self, poll_s: float = 30.0, max_ticks: int | None = None, sleep: Callable[[float], None] = time.sleep):
        n = 0
        while max_ticks is None or n < max_ticks:
            self.tick()
            n += 1
            sleep(poll_s)
