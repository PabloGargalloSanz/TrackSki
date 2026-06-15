import argparse
import sys
from zipfile import BadZipFile
from xml.etree.ElementTree import ParseError

import httpx

from app.core.config import settings
from app.db.session import SessionLocal
from app.repositories.weather_alerts import save_weather_alert
from app.services.weather import (
    AemetClient,
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

    if not settings.AEMET_API_KEY:
        print("ERROR: falta AEMET_API_KEY en el entorno.", file=sys.stderr)
        return 1

    try:
        with AemetClient(settings.AEMET_API_KEY) as client:
            package = client.get_latest_alerts(args.area)
        alerts = read_aemet_alert_package(package)
    except (httpx.HTTPError, BadZipFile, ParseError, ValueError) as error:
        print(f"ERROR: no se pudieron obtener los avisos: {error}", file=sys.stderr)
        return 1

    db = SessionLocal()
    try:
        for alert in alerts:
            save_weather_alert(db, alert)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"OK: guardados {len(alerts)} avisos de AEMET para el area {args.area}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
