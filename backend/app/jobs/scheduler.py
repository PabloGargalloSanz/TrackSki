import asyncio
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from app.commands import ingest_alerts, ingest_weather
from app.jobs import import_dgt_datex2_incidents
from app.jobs.result import JobResult, print_job_result


@dataclass
class ScheduledJob:
    name: str
    interval_seconds: int
    run: Callable[[], JobResult]
    next_run_at: float = 0
    running: bool = False


def main() -> int:
    asyncio.run(_main())
    return 0


async def _main() -> None:
    tick_seconds = _env_int("DATA_JOBS_TICK_SECONDS", 60)
    jobs = build_scheduled_jobs()
    pending_tasks: set[asyncio.Task[None]] = set()

    print("TrackSki data jobs scheduler started", flush=True)
    for job in jobs:
        print(f"- {job.name}: cada {job.interval_seconds}s", flush=True)

    while True:
        pending_tasks |= await run_due_jobs_once(jobs)
        pending_tasks = {task for task in pending_tasks if not task.done()}
        await asyncio.sleep(tick_seconds)


def build_scheduled_jobs() -> list[ScheduledJob]:
    return [
        ScheduledJob(
            name="weather",
            interval_seconds=_env_int("DATA_JOBS_WEATHER_INTERVAL_SECONDS", 1800),
            run=ingest_weather.run,
        ),
        ScheduledJob(
            name="alerts",
            interval_seconds=_env_int("DATA_JOBS_ALERTS_INTERVAL_SECONDS", 1800),
            run=ingest_alerts.run,
        ),
        ScheduledJob(
            name="roads",
            interval_seconds=_env_int("DATA_JOBS_ROADS_INTERVAL_SECONDS", 900),
            run=import_dgt_datex2_incidents.run,
        ),
    ]


async def run_due_jobs_once(jobs: list[ScheduledJob]) -> set[asyncio.Task[None]]:
    now = asyncio.get_running_loop().time()
    tasks = set()

    for job in jobs:
        if job.running or now < job.next_run_at:
            continue

        job.running = True
        job.next_run_at = now + job.interval_seconds
        tasks.add(asyncio.create_task(_run_job(job)))

    return tasks


async def _run_job(job: ScheduledJob) -> None:
    started_at = datetime.now(timezone.utc).isoformat()
    print(f"[{started_at}] Ejecutando job {job.name}", flush=True)

    try:
        result = await asyncio.to_thread(job.run)
    except Exception as error:
        result = JobResult.failed(job.name, error)
    finally:
        job.running = False

    print_job_result(result)


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError:
        return default

    return value if value > 0 else default


if __name__ == "__main__":
    raise SystemExit(main())
