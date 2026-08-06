from dataclasses import dataclass, field
from typing import Any


@dataclass
class JobResult:
    job_name: str
    status: str = "success"
    processed: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
    message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def failed(cls, job_name: str, error: Exception | str) -> "JobResult":
        return cls(
            job_name=job_name,
            status="failed",
            errors=[str(error)],
            message=str(error),
        )


def print_job_result(result: JobResult) -> None:
    print(f"{result.job_name}:")
    print(f"- status: {result.status}")
    print(f"- processed: {result.processed}")
    print(f"- inserted: {result.inserted}")
    print(f"- updated: {result.updated}")
    print(f"- skipped: {result.skipped}")
    if result.message:
        print(f"- message: {result.message}")
    if result.errors:
        print(f"- errors: {'; '.join(result.errors)}")
    for key, value in result.metadata.items():
        print(f"- {key}: {value}")
