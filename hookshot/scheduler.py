"""Scheduled replay: run a saved request on a recurring interval."""

import threading
import time
from typing import Callable, Optional


class ScheduleError(Exception):
    pass


class ScheduledJob:
    def __init__(self, request_id: str, interval: float, callback: Callable):
        if interval <= 0:
            raise ScheduleError("interval must be a positive number of seconds")
        self.request_id = request_id
        self.interval = interval
        self.callback = callback
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.run_count = 0
        self.last_error: Optional[str] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            raise ScheduleError("job is already running")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self.interval + 1)

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.callback(self.request_id)
                self.run_count += 1
                self.last_error = None
            except Exception as exc:
                self.last_error = str(exc)
            self._stop_event.wait(self.interval)

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "interval": self.interval,
            "run_count": self.run_count,
            "running": self.is_running(),
            "last_error": self.last_error,
        }


class Scheduler:
    def __init__(self):
        self._jobs: dict[str, ScheduledJob] = {}

    def schedule(self, request_id: str, interval: float, callback: Callable) -> ScheduledJob:
        if request_id in self._jobs and self._jobs[request_id].is_running():
            raise ScheduleError(f"a job for request {request_id!r} is already scheduled")
        job = ScheduledJob(request_id, interval, callback)
        self._jobs[request_id] = job
        job.start()
        return job

    def cancel(self, request_id: str) -> None:
        job = self._jobs.get(request_id)
        if job is None:
            raise ScheduleError(f"no job found for request {request_id!r}")
        job.stop()
        del self._jobs[request_id]

    def list_jobs(self) -> list[dict]:
        return [job.to_dict() for job in self._jobs.values()]

    def cancel_all(self) -> None:
        for job in list(self._jobs.values()):
            job.stop()
        self._jobs.clear()
