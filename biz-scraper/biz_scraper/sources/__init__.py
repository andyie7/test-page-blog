from .generic import HtmlSource
from .places import PlacesSource

SOURCE_TYPES = {"html": HtmlSource, "places": PlacesSource}


def build_source(cfg: dict):
    try:
        return SOURCE_TYPES[cfg["type"]](cfg)
    except KeyError as e:
        raise ValueError(f"Bad source config {cfg.get('name')!r}: missing/unknown {e}") from e
