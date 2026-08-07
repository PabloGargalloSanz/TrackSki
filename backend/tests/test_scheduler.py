from unittest.mock import Mock
import unittest

from app.jobs.result import JobResult
from app.jobs.scheduler import ScheduledJob, run_due_jobs_once


class SchedulerTest(unittest.IsolatedAsyncioTestCase):
    async def test_runs_due_jobs_as_background_tasks(self) -> None:
        first_run = Mock(return_value=JobResult(job_name="first"))
        second_run = Mock(return_value=JobResult(job_name="second"))
        jobs = [
            ScheduledJob(name="first", interval_seconds=60, run=first_run),
            ScheduledJob(name="second", interval_seconds=60, run=second_run),
        ]

        tasks = await run_due_jobs_once(jobs)
        await self._wait_for_tasks(tasks)

        self.assertEqual(len(tasks), 2)
        first_run.assert_called_once_with()
        second_run.assert_called_once_with()
        self.assertFalse(jobs[0].running)
        self.assertFalse(jobs[1].running)
        self.assertGreater(jobs[0].next_run_at, 0)
        self.assertGreater(jobs[1].next_run_at, 0)

    async def test_does_not_overlap_same_job(self) -> None:
        job = ScheduledJob(
            name="roads",
            interval_seconds=60,
            run=Mock(return_value=JobResult(job_name="roads")),
            running=True,
        )

        tasks = await run_due_jobs_once([job])

        self.assertEqual(tasks, set())
        job.run.assert_not_called()

    async def _wait_for_tasks(self, tasks) -> None:
        for task in tasks:
            await task


if __name__ == "__main__":
    unittest.main()
