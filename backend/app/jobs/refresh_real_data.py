import argparse
from collections.abc import Callable

from app.commands import ingest_alerts, ingest_weather
from app.jobs import import_dgt_datex2_incidents
from app.jobs.result import JobResult, print_job_result

JobRunner = Callable[[], JobResult]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Refresca datos reales de meteorologia, avisos y carreteras."
    )
    parser.add_argument("--all", action="store_true", help="Ejecuta todos los jobs.")
    parser.add_argument("--weather", action="store_true", help="Ejecuta Open-Meteo.")
    parser.add_argument("--alerts", action="store_true", help="Ejecuta avisos AEMET.")
    parser.add_argument("--roads", action="store_true", help="Ejecuta incidencias DGT.")
    parser.add_argument(
        "--area",
        help=(
            "Area AEMET para avisos, por ejemplo 62. Obligatoria si se ejecuta "
            "AEMET; mas adelante se resolvera por estacion."
        ),
    )
    parser.add_argument(
        "--resort-id",
        type=int,
        help="Importa meteorologia solo para una estacion.",
    )
    return parser.parse_args()


def selected_jobs(args: argparse.Namespace) -> list[tuple[str, JobRunner]]:
    run_all = args.all
    jobs: list[tuple[str, JobRunner]] = []

    if run_all or args.weather:
        jobs.append(("weather", lambda: ingest_weather.run(resort_id=args.resort_id)))
    if run_all or args.alerts:
        jobs.append(("alerts", lambda: _run_alerts(args.area)))
    if run_all or args.roads:
        jobs.append(("roads", import_dgt_datex2_incidents.run))

    return jobs


def _run_alerts(area: str | None) -> JobResult:
    if not area:
        return JobResult.failed(
            "AEMET alerts",
            "Falta --area para AEMET. El area depende de la zona/estacion.",
        )

    return ingest_alerts.run(area=area)


def run(args: argparse.Namespace) -> list[JobResult]:
    if not any([args.all, args.weather, args.alerts, args.roads]):
        return [
            JobResult.failed(
                "refresh_real_data",
                "Selecciona al menos una opcion: --all, --weather, --alerts o --roads.",
            )
        ]

    results: list[JobResult] = []

    for job_key, runner in selected_jobs(args):
        try:
            results.append(runner())
        except Exception as error:
            results.append(JobResult.failed(job_key, error))

    return results


def main() -> int:
    args = parse_args()
    results = run(args)

    print("Refresh real data finished")
    print()
    for index, result in enumerate(results):
        if index:
            print()
        print_job_result(result)

    return 1 if any(result.status == "failed" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
