"""Loads the generated datasets in data/ (see scripts/build_data.py)."""

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=None)
def global_data():
    return json.loads((DATA_DIR / "global.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def countries():
    """All economies, sorted by display name."""
    return json.loads((DATA_DIR / "countries.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def countries_by_iso3():
    return {c["iso3"]: c for c in countries()}


def country(iso3):
    return countries_by_iso3().get(iso3)


def world_population():
    return global_data()["world_population"]
