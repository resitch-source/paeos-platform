import pytest

from paeos_fx.agri.geometry import validate_geojson_geometry
from paeos_fx.core.errors import ValidationError

pytestmark = pytest.mark.unit

POINT = {"type": "Point", "coordinates": [120.98, 14.6]}
POLYGON = {
    "type": "Polygon",
    "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]],
}


def test_valid_point():
    out = validate_geojson_geometry(POINT, allowed_types=("Point",))
    assert out["type"] == "Point"


def test_valid_polygon_from_string():
    import json

    out = validate_geojson_geometry(json.dumps(POLYGON), allowed_types=("Polygon",))
    assert out["type"] == "Polygon"


def test_disallowed_type_rejected():
    with pytest.raises(ValidationError):
        validate_geojson_geometry(POINT, allowed_types=("Polygon", "MultiPolygon"))


def test_unknown_type_rejected():
    with pytest.raises(ValidationError):
        validate_geojson_geometry({"type": "Wormhole", "coordinates": []},
                                  allowed_types=("Point",))


def test_missing_coordinates_rejected():
    with pytest.raises(ValidationError):
        validate_geojson_geometry({"type": "Point"}, allowed_types=("Point",))


def test_invalid_json_rejected():
    with pytest.raises(ValidationError):
        validate_geojson_geometry("{not json", allowed_types=("Point",))
