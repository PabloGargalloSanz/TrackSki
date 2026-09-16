import argparse
from datetime import datetime, timezone
from uuid import uuid4

import httpx
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.jobs.result import JobResult, print_job_result
from app.repositories.job_audit_runs import create_job_audit_run
from app.repositories.resorts import get_resorts
from app.repositories.snow_reports import create_snow_report_if_missing
from app.scrapers.snow.aramon import ARAMON_RESORTS, AramonSnowScraper
from app.scrapers.snow.astun_candanchu import (
    ASTUN_CANDANCHU_RESORTS,
    AstunCandanchuSnowScraper,
)
from app.scrapers.snow.baqueira import BAQUEIRA_RESORTS, BaqueiraSnowScraper
from app.scrapers.snow.base import SnowScraperResort


def scraper_configs():
    return {
        "aramon": (AramonSnowScraper, ARAMON_RESORTS),
        "astun_candanchu": (AstunCandanchuSnowScraper, ASTUN_CANDANCHU_RESORTS),
        "baqueira": (BaqueiraSnowScraper, BAQUEIRA_RESORTS),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Importa partes de nieve desde scrapers configurados."
    )
    parser.add_argument(
        "--provider",
        choices=["all", *scraper_configs().keys()],
        default="all",
        help="Proveedor a importar. Por defecto all.",
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
    provider: str = "all",
    resort_name: str | None = None,
    url: str | None = None,
    audit_run_group_id: str | None = None,
) -> JobResult:
    result = JobResult(job_name="Snow reports")

    configs = scraper_configs()
    if provider not in {"all", *configs.keys()}:
        result.status = "failed"
        result.message = f"Proveedor no soportado: {provider}"
        return result

    if bool(resort_name) != bool(url):
        result.status = "failed"
        result.message = "Para importar una estacion concreta indica --resort-name y --url."
        return result

    db = SessionLocal()
    try:
        run_group_id = audit_run_group_id or str(uuid4())
        db_resorts = {resort["name"]: resort for resort in get_resorts(db)}
        providers = [provider] if provider != "all" else list(configs)
        result.metadata["providers"] = ", ".join(providers)

        for selected_provider in providers:
            scraper_class, default_resorts = configs[selected_provider]
            configured_resorts = (
                [SnowScraperResort(resort_id=0, name=resort_name, url=url)]
                if resort_name and url
                else default_resorts
            )

            scraper = scraper_class()
            try:
                for configured_resort in configured_resorts:
                    started_at = datetime.now(timezone.utc)
                    result.processed += 1
                    resort = db_resorts.get(configured_resort.name)
                    if not resort:
                        error_message = (
                            f"{configured_resort.name}: estacion no encontrada en DB"
                        )
                        result.skipped += 1
                        result.errors.append(error_message)
                        _store_snow_audit_run(
                            db,
                            run_group_id=run_group_id,
                            provider=selected_provider,
                            target_name=configured_resort.name,
                            status="failed",
                            processed=1,
                            skipped=1,
                            error_message=error_message,
                            started_at=started_at,
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
                    except (httpx.HTTPError, SQLAlchemyError, ValueError) as error:
                        db.rollback()
                        error_message = f"{configured_resort.name}: {error}"
                        result.skipped += 1
                        result.errors.append(error_message)
                        _store_snow_audit_run(
                            db,
                            run_group_id=run_group_id,
                            provider=selected_provider,
                            target_id=str(resort["id"]),
                            target_name=configured_resort.name,
                            status="failed",
                            processed=1,
                            skipped=1,
                            error_message=error_message,
                            started_at=started_at,
                        )
                        continue

                    if report_id:
                        result.inserted += 1
                        item_inserted = 1
                        item_skipped = 0
                    else:
                        result.skipped += 1
                        item_inserted = 0
                        item_skipped = 1

                    _store_snow_audit_run(
                        db,
                        run_group_id=run_group_id,
                        provider=selected_provider,
                        target_id=str(resort["id"]),
                        target_name=configured_resort.name,
                        status="success",
                        processed=1,
                        inserted=item_inserted,
                        skipped=item_skipped,
                        metadata={"report_inserted": bool(report_id)},
                        started_at=started_at,
                    )
            finally:
                scraper.close()

        if result.errors:
            result.status = "partial"

        return result
    finally:
        db.close()


def _store_snow_audit_run(
    db,
    *,
    run_group_id: str,
    provider: str,
    target_name: str,
    status: str,
    processed: int,
    inserted: int = 0,
    updated: int = 0,
    skipped: int = 0,
    target_id: str | None = None,
    error_message: str | None = None,
    metadata: dict | None = None,
    started_at: datetime,
) -> None:
    try:
        create_job_audit_run(
            db,
            run_group_id=run_group_id,
            job_key="snow",
            provider=provider,
            target_type="resort",
            target_id=target_id,
            target_name=target_name,
            status=status,
            processed=processed,
            inserted=inserted,
            updated=updated,
            skipped=skipped,
            error_message=error_message,
            metadata=metadata,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
        )
        db.commit()
    except Exception:
        db.rollback()


if __name__ == "__main__":
    raise SystemExit(main())
