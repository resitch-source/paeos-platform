"""GeoJSON validation helpers (Phase 2).

Pure, dependency-light validation for incoming GeoJSON geometries. The actual
conversion to PostGIS geometry is performed in the database via
``ST_GeomFromGeoJSON`` (see services), so no heavy geometry library is required
here. Storage CRS is WGS84 (EPSG:4326).
"""

from __future__ import annotations

import json
from typing import Any

from paeos_fx.core.errors import ValidationError

SRID_WGS84 = 4326

_VALID_TYPES = {
    "Point",
    "MultiPoint",
    "LineString",
    "MultiLineString",
    "Polygon",
    "MultiPolygon",
    "GeometryCollection",
}


def validate_geojson_geometry(
    geojson: dict[str, Any] | str, *, allowed_types: tuple[str, ...]
) -> dict[str, Any]:
    """Validate a GeoJSON geometry object and return it as a dict.

    Raises :class:`ValidationError` for malformed input or a disallowed type.
    Coordinates are only structurally checked here; topological validity is
    enforced by PostGIS on insert.
    """
    if isinstance(geojson, str):
        try:
            geojson = json.loads(geojson)
        except json.JSONDecodeError as exc:
            raise ValidationError("Geometry is not valid JSON.") from exc
    if not isinstance(geojson, dict):
        raise ValidationError("Geometry must be a GeoJSON object.")

    gtype = geojson.get("type")
    if gtype not in _VALID_TYPES:
        raise ValidationError(f"Unknown GeoJSON geometry type: {gtype!r}")
    if gtype not in allowed_types:
        raise ValidationError(
            f"Geometry type {gtype!r} not allowed here "
            f"(expected one of {allowed_types})."
        )
    if gtype != "GeometryCollection" and "coordinates" not in geojson:
        raise ValidationError("GeoJSON geometry is missing 'coordinates'.")
    return geojson


def to_geojson_string(geojson: dict[str, Any]) -> str:
    return json.dumps(geojson, separators=(",", ":"))
