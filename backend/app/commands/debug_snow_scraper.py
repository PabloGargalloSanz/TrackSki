import argparse
from dataclasses import asdict
from pprint import pprint

from app.scrapers.snow.aramon import AramonSnowScraper
from app.scrapers.snow.base import SnowScraperResort


DEFAULT_ARAMON_URL = "https://www.formigal-panticosa.com/partes/parteNieve?prevision=0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Muestra por consola los datos extraidos por un scraper de nieve."
    )
    parser.add_argument(
        "--provider",
        choices=["aramon"],
        default="aramon",
        help="Scraper a ejecutar. Por defecto aramon.",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_ARAMON_URL,
        help="URL del parte de nieve a inspeccionar.",
    )
    parser.add_argument(
        "--resort-id",
        type=int,
        default=0,
        help="ID orientativo de la estacion. No se guarda en DB.",
    )
    parser.add_argument(
        "--name",
        default="Debug snow resort",
        help="Nombre orientativo de la estacion.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    resort = SnowScraperResort(
        resort_id=args.resort_id,
        name=args.name,
        url=args.url,
    )

    scraper = AramonSnowScraper()
    try:
        report = scraper.get_current(resort)
    finally:
        scraper.close()

    print(f"Scraper: {args.provider}")
    print(f"Estacion: {resort.name} ({resort.resort_id})")
    print(f"URL: {resort.url}")
    print("Datos extraidos:")
    pprint(asdict(report), sort_dicts=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
