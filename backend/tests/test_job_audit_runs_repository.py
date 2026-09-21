from datetime import datetime, timezone
from unittest.mock import Mock
import json
import unittest

from app.repositories.job_audit_runs import create_job_audit_run


class JobAuditRunsRepositoryTest(unittest.TestCase):
    def test_create_job_audit_run_maps_context(self) -> None:
        db = Mock()
        db.execute.return_value.scalar_one.return_value = 12
        started_at = datetime(2026, 9, 16, 10, 0, tzinfo=timezone.utc)
        finished_at = datetime(2026, 9, 16, 10, 1, tzinfo=timezone.utc)

        audit_run_id = create_job_audit_run(
            db,
            run_group_id="group-1",
            job_key="snow",
            provider="baqueira",
            target_type="resort",
            target_id="6",
            target_name="Baqueira Beret",
            status="failed",
            processed=1,
            skipped=1,
            error_message="No se encontraron datos reconocibles",
            metadata={"blocks_found": 0},
            started_at=started_at,
            finished_at=finished_at,
        )

        statement = str(db.execute.call_args.args[0])
        params = db.execute.call_args.args[1]
        self.assertEqual(audit_run_id, 12)
        self.assertIn("INSERT INTO job_audit_runs", statement)
        self.assertEqual(params["run_group_id"], "group-1")
        self.assertEqual(params["job_key"], "snow")
        self.assertEqual(params["provider"], "baqueira")
        self.assertEqual(params["target_type"], "resort")
        self.assertEqual(params["target_id"], "6")
        self.assertEqual(params["target_name"], "Baqueira Beret")
        self.assertEqual(params["status"], "failed")
        self.assertEqual(params["error_message"], "No se encontraron datos reconocibles")
        self.assertEqual(json.loads(params["metadata"]), {"blocks_found": 0})
        self.assertEqual(params["started_at"], started_at)
        self.assertEqual(params["finished_at"], finished_at)


if __name__ == "__main__":
    unittest.main()
