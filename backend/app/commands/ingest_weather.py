import argparse
import sys

import httpx

from app.db.session import SessionLocal
from app.repositories.resorts import get_resort_by_id, get_resorts
from app.repositories.weather_reports import create_weather_report_if_missing
from app.services.weather import OpenMeteoProvider


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Importa condiciones actuales desde Open-Meteo."
    )
    parser.add_argument(
        "--resort-id",
        type=int,
        help="Importa solo una estacion. Por defecto importa todas.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db = SessionLocal()
    failures = 0

    try:
        if args.resort_id:
            resort = get_resort_by_id(db, args.resort_id)
            resorts = [resort] if resort else []
        else:
            resorts = get_resorts(db)

        if not resorts:
            print("No se encontraron estaciones para importar.")
            return 1

        with OpenMeteoProvider() as provider:
            for resort in resorts:
                try:
                    observation = provider.get_current(
                        latitude=resort["latitude"],
                        longitude=resort["longitude"],
                    )
                    report_id = create_weather_report_if_missing(
                        db,
                        resort_id=resort["id"],
                        observation=observation,
                    )
                    db.commit()
                except (httpx.HTTPError, ValueError) as error:
                    db.rollback()
                    failures += 1
                    print(f"ERROR {resort['name']}: {error}", file=sys.stderr)
                    continue

                result = (
                    f"creado informe {report_id}"
                    if report_id
                    else "sin cambios; observacion ya importada"
                )
                print(f"OK {resort['name']}: {result}")
    finally:
        db.close()

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
