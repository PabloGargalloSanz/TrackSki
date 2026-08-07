import argparse
from zipfile import BadZipFile
from xml.etree.ElementTree import ParseError

import httpx

from app.core.config import settings
from app.db.session import SessionLocal
from app.jobs.result import JobResult, print_job_result
from app.repositories.resorts import get_resorts
from app.repositories.weather_alerts import save_weather_alert
from app.services.weather import (
    AemetClient,
    is_actionable_alert,
    read_aemet_alert_package,
)
from app.services.weather.aemet_areas import get_aemet_areas_for_resorts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Descarga y guarda avisos meteorologicos de AEMET."
    )
    parser.add_argument(
        "--area",
        action="append",
        help="Codigo de comunidad autonoma de AEMET, por ejemplo 62 o 69.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run(areas=args.area)
    print_job_result(result)
    return 0 if result.status == "success" else 1


def run(areas: list[str] | None = None) -> JobResult:
    if not settings.AEMET_API_KEY:
        return JobResult.failed("AEMET alerts", "Falta AEMET_API_KEY en el entorno.")

    db = SessionLocal()
    result = JobResult(
        job_name="AEMET alerts",
    )
    try:
        selected_areas = areas or get_aemet_areas_for_resorts(get_resorts(db))
        if not selected_areas:
            return JobResult.failed(
                "AEMET alerts",
                "No se encontraron areas AEMET para las estaciones configuradas.",
            )

        saved = 0
        with AemetClient(settings.AEMET_API_KEY) as client:
            for area in selected_areas:
                try:
                    package = client.get_latest_alerts(area)
                    downloaded_alerts = read_aemet_alert_package(package)
                    alerts = [
                        alert
                        for alert in downloaded_alerts
                        if is_actionable_alert(alert)
                    ]
                except (httpx.HTTPError, BadZipFile, ParseError, ValueError) as error:
                    result.errors.append(f"area {area}: {error}")
                    continue

                result.processed += len(downloaded_alerts)
                result.skipped += len(downloaded_alerts) - len(alerts)
                for alert in alerts:
                    save_weather_alert(db, alert)
                    saved += 1

        db.commit()
    except Exception as error:
        db.rollback()
        return JobResult.failed("AEMET alerts", error)
    finally:
        db.close()

    if result.errors:
        result.status = "partial"
    result.message = f"Guardados {saved} avisos accionables mediante upsert."
    result.metadata = {
        "areas": selected_areas,
        "saved": saved,
    }

    return result


if __name__ == "__main__":
    raise SystemExit(main())
