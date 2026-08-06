import argparse
from zipfile import BadZipFile
from xml.etree.ElementTree import ParseError

import httpx

from app.core.config import settings
from app.db.session import SessionLocal
from app.jobs.result import JobResult, print_job_result
from app.repositories.weather_alerts import save_weather_alert
from app.services.weather import (
    AemetClient,
    is_actionable_alert,
    read_aemet_alert_package,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Descarga y guarda avisos meteorologicos de AEMET."
    )
    parser.add_argument(
        "--area",
        required=True,
        help="Codigo de comunidad autonoma de AEMET, por ejemplo 62 o 69.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run(area=args.area)
    print_job_result(result)
    return 0 if result.status == "success" else 1


def run(area: str) -> JobResult:
    if not settings.AEMET_API_KEY:
        return JobResult.failed("AEMET alerts", "Falta AEMET_API_KEY en el entorno.")

    try:
        with AemetClient(settings.AEMET_API_KEY) as client:
            package = client.get_latest_alerts(area)
        downloaded_alerts = read_aemet_alert_package(package)
        alerts = [
            alert for alert in downloaded_alerts if is_actionable_alert(alert)
        ]
    except (httpx.HTTPError, BadZipFile, ParseError, ValueError) as error:
        return JobResult.failed("AEMET alerts", error)

    db = SessionLocal()
    result = JobResult(
        job_name="AEMET alerts",
        processed=len(downloaded_alerts),
        skipped=len(downloaded_alerts) - len(alerts),
        message=(
            f"Guardados {len(alerts)} avisos accionables mediante upsert."
        ),
        metadata={
            "area": area,
            "saved": len(alerts),
        },
    )
    try:
        for alert in alerts:
            save_weather_alert(db, alert)
        db.commit()
    except Exception as error:
        db.rollback()
        return JobResult.failed("AEMET alerts", error)
    finally:
        db.close()

    return result


if __name__ == "__main__":
    raise SystemExit(main())
