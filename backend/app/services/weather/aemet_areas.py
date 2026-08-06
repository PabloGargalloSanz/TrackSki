import unicodedata


AEMET_AREA_BY_REGION = {
    "andalucia": "61",
    "granada": "61",
    "aragon": "62",
    "huesca": "62",
    "teruel": "62",
    "zaragoza": "62",
    "catalonia": "69",
    "cataluna": "69",
    "catalunya": "69",
    "lleida": "69",
    "val d'aran": "69",
    "val d aran": "69",
}


def normalize_region(value: str | None) -> str:
    if not value:
        return ""

    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return without_accents.lower().strip()


def get_aemet_area_for_resort(resort: dict) -> str | None:
    if resort.get("country") != "Spain":
        return None

    region = normalize_region(resort.get("region"))
    return AEMET_AREA_BY_REGION.get(region)


def get_aemet_areas_for_resorts(resorts: list[dict]) -> list[str]:
    areas = {
        area
        for resort in resorts
        if (area := get_aemet_area_for_resort(resort)) is not None
    }
    return sorted(areas)
