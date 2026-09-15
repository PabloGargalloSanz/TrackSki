import argparse

import httpx

from app.db.session import SessionLocal
from app.jobs.result import JobResult, print_job_result
from app.repositories.resorts import get_resorts
from app.repositories.snow_reports import create_snow_report_if_missing
from app.scrapers.snow.aramon import ARAMON_RESORTS, AramonSnowScraper
from app.scrapers.snow.base import SnowScraperResort


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Importa partes de nieve desde scrapers configurados."
    )
    parser.add_argument(
        "--provider",
        choices=["aramon"],
        default="aramon",
        help="Proveedor a importar. Por defecto aramon.",
    )
    parser.add_argument(
        "--resort-name",
        help="Importa una estacion concreta usando el nombre existente en la DB.",
    )
    parser.add_argument(
        "--url",
        help="URL del parte de nieve. Requiere --resort-name.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run(
        provider=args.provider,
        resort_name=args.resort_name,
        url=args.url,
    )
    print_job_result(result)
    return 0 if result.status in {"success", "partial"} else 1


def run(
    provider: str = "aramon",
    resort_name: str | None = None,
    url: str | None = None,
) -> JobResult:
    result = JobResult(job_name="Snow reports")

    if provider != "aramon":
        result.status = "failed"
        result.message = f"Proveedor no soportado: {provider}"
        return result

    if bool(resort_name) != bool(url):
        result.status = "failed"
        result.message = "Para importar una estacion concreta indica --resort-name y --url."
        return result

    db = SessionLocal()
    try:
        db_resorts = {resort["name"]: resort for resort in get_resorts(db)}
        configured_resorts = (
            [SnowScraperResort(resort_id=0, name=resort_name, url=url)]
            if resort_name and url
            else ARAMON_RESORTS
        )

        scraper = AramonSnowScraper()
        try:
            for configured_resort in configured_resorts:
                result.processed += 1
                resort = db_resorts.get(configured_resort.name)
                if not resort:
                    result.skipped += 1
                    result.errors.append(
                        f"{configured_resort.name}: estacion no encontrada en DB"
                    )
                    continue

                try:
                    report = scraper.get_current(
                        SnowScraperResort(
                            resort_id=resort["id"],
                            name=configured_resort.name,
                            url=configured_resort.url,
                        )
                    )
                    report_id = create_snow_report_if_missing(
                        db,
                        resort_id=resort["id"],
                        report=report,
                    )
                    db.commit()
                except (httpx.HTTPError, ValueError) as error:
                    db.rollback()
                    result.skipped += 1
                    result.errors.append(f"{configured_resort.name}: {error}")
                    continue

                if report_id:
                    result.inserted += 1
                else:
                    result.skipped += 1
        finally:
            scraper.close()

        if result.errors:
            result.status = "partial"

        result.metadata["provider"] = provider
        return result
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
