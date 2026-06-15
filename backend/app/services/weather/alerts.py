from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from tarfile import ReadError, open as open_tar
from zipfile import ZipFile, is_zipfile
from xml.etree import ElementTree

CAP_NAMESPACE = "urn:oasis:names:tc:emergency:cap:1.2"
CAP = {"cap": CAP_NAMESPACE}
ALERT_LEVELS = ("verde", "amarillo", "naranja", "rojo")
SEVERITY_LEVELS = {
    "Minor": "amarillo",
    "Moderate": "amarillo",
    "Severe": "naranja",
    "Extreme": "rojo",
}
ACTIONABLE_LEVELS = {"amarillo", "naranja", "rojo"}


@dataclass(frozen=True)
class WeatherAlert:
    identifier: str
    level: str
    event: str
    area: str
    onset: datetime | None
    expires: datetime | None
    headline: str | None
    description: str | None
    instruction: str | None
    source: str = "aemet"


def is_actionable_alert(
    alert: WeatherAlert,
    now: datetime | None = None,
) -> bool:
    reference_time = now or datetime.now(timezone.utc)
    return (
        alert.level in ACTIONABLE_LEVELS
        and (alert.expires is None or alert.expires > reference_time)
    )


def read_aemet_alerts(document: bytes) -> list[WeatherAlert]:
    alerts: list[WeatherAlert] = []
    root = ElementTree.fromstring(document)
    identifier = _required_text(root, "cap:identifier")
    info = _preferred_info(root)
    level = _alert_level(info)
    event = _required_text(info, "cap:event")

    for area in info.findall("cap:area", CAP):
        alerts.append(
            WeatherAlert(
                identifier=identifier,
                level=level,
                event=event,
                area=_required_text(area, "cap:areaDesc"),
                onset=_datetime_or_none(info, "cap:onset"),
                expires=_datetime_or_none(info, "cap:expires"),
                headline=_text_or_none(info, "cap:headline"),
                description=_text_or_none(info, "cap:description"),
                instruction=_text_or_none(info, "cap:instruction"),
            )
        )

    return alerts


def read_aemet_alert_package(package: bytes) -> list[WeatherAlert]:
    alerts: list[WeatherAlert] = []

    if is_zipfile(BytesIO(package)):
        with ZipFile(BytesIO(package)) as archive:
            for name in archive.namelist():
                if name.lower().endswith(".xml"):
                    alerts.extend(read_aemet_alerts(archive.read(name)))
        return alerts

    try:
        with open_tar(fileobj=BytesIO(package), mode="r:*") as archive:
            for member in archive.getmembers():
                if member.isfile() and member.name.lower().endswith(".xml"):
                    document = archive.extractfile(member)
                    if document:
                        alerts.extend(read_aemet_alerts(document.read()))
        return alerts
    except ReadError:
        return read_aemet_alerts(package)



def _preferred_info(root: ElementTree.Element) -> ElementTree.Element:
    infos = root.findall("cap:info", CAP)
    if not infos:
        raise ValueError("El aviso CAP no contiene informacion")

    return next(
        (
            info
            for info in infos
            if (_text_or_none(info, "cap:language") or "").lower().startswith("es")
        ),
        infos[0],
    )


def _alert_level(info: ElementTree.Element) -> str:
    searchable = []
    for tag in ("cap:parameter", "cap:eventCode"):
        for element in info.findall(tag, CAP):
            searchable.extend(text.lower() for text in element.itertext())

    for level in ALERT_LEVELS:
        if any(level in text for text in searchable):
            return level

    severity = _text_or_none(info, "cap:severity")
    return SEVERITY_LEVELS.get(severity or "", "desconocido")


def _datetime_or_none(
    element: ElementTree.Element,
    path: str,
) -> datetime | None:
    value = _text_or_none(element, path)
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def _required_text(element: ElementTree.Element, path: str) -> str:
    value = _text_or_none(element, path)
    if value is None:
        raise ValueError(f"Falta el campo CAP obligatorio {path}")
    return value


def _text_or_none(element: ElementTree.Element, path: str) -> str | None:
    value = element.findtext(path, default=None, namespaces=CAP)
    return value.strip() if value and value.strip() else None
