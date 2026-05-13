"""Tests for hookshot.scheduler."""

import time
import pytest
from hookshot.scheduler import Scheduler, ScheduledJob, ScheduleError


@pytest.fixture
def scheduler():
    s = Scheduler()
    yield s
    s.cancel_all()


def test_schedule_job_starts(scheduler):
    calls = []
    scheduler.schedule("req-1", 0.05, lambda rid: calls.append(rid))
    time.sleep(0.18)
    assert len(calls) >= 2
    assert all(c == "req-1" for c in calls)


def test_cancel_stops_job(scheduler):
    calls = []
    scheduler.schedule("req-2", 0.05, lambda rid: calls.append(rid))
    time.sleep(0.12)
    scheduler.cancel("req-2")
    count_after_cancel = len(calls)
    time.sleep(0.12)
    assert len(calls) == count_after_cancel


def test_cancel_unknown_raises(scheduler):
    with pytest.raises(ScheduleError, match="no job found"):
        scheduler.cancel("ghost-id")


def test_duplicate_schedule_raises(scheduler):
    scheduler.schedule("req-3", 0.1, lambda rid: None)
    with pytest.raises(ScheduleError, match="already scheduled"):
        scheduler.schedule("req-3", 0.1, lambda rid: None)


def test_invalid_interval_raises():
    with pytest.raises(ScheduleError, match="positive"):
        ScheduledJob("req-x", 0, lambda rid: None)


def test_list_jobs(scheduler):
    scheduler.schedule("req-4", 0.1, lambda rid: None)
    jobs = scheduler.list_jobs()
    assert len(jobs) == 1
    assert jobs[0]["request_id"] == "req-4"
    assert jobs[0]["running"] is True


def test_cancel_all(scheduler):
    scheduler.schedule("req-5", 0.1, lambda rid: None)
    scheduler.schedule("req-6", 0.1, lambda rid: None)
    scheduler.cancel_all()
    assert scheduler.list_jobs() == []


def test_run_count_increments(scheduler):
    calls = []
    job = scheduler.schedule("req-7", 0.05, lambda rid: calls.append(rid))
    time.sleep(0.18)
    assert job.run_count >= 2


def test_last_error_captured(scheduler):
    def bad_callback(rid):
        raise RuntimeError("boom")

    job = scheduler.schedule("req-8", 0.05, bad_callback)
    time.sleep(0.12)
    assert job.last_error == "boom"


def test_to_dict_shape(scheduler):
    job = scheduler.schedule("req-9", 0.1, lambda rid: None)
    d = job.to_dict()
    assert set(d.keys()) == {"request_id", "interval", "run_count", "running", "last_error"}
