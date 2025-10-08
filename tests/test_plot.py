import json

import pydantic
import pytest

from conftest import resource
from plot import make_validated_response_model, PropertyPaths, render_points_as_geojson
from plot import read_path, select_properties
from util import extract_json_schema


def test_model():
    content = resource("buried_list_of_lat_lons.json")
    schema = extract_json_schema(json.loads(content))
    model = make_validated_response_model(schema)

    with pytest.raises(pydantic.ValidationError):
        model(response=PropertyPaths(latitude=["haha"], longitude=["haha"]))

    with pytest.raises(pydantic.ValidationError):
        model(response=PropertyPaths(latitude=["points"], longitude=["points"]))

    with pytest.raises(pydantic.ValidationError):
        model(response=PropertyPaths(latitude=["latitude"], longitude=["longitude"]))

    model(
        response=PropertyPaths(
            latitude=["points", "latitude"], longitude=["points", "longitude"]
        )
    )


@pytest.mark.asyncio
async def test_choose_paths():
    content = resource("buried_list_of_lat_lons.json")
    schema = extract_json_schema(json.loads(content))
    paths = await select_properties(schema)

    assert paths == PropertyPaths(
        latitude=["points", "latitude"],
        longitude=["points", "longitude"],
        style_by=None,
    )


def test_extract_path_values():
    data = json.loads(resource("buried_list_of_lat_lons.json"))

    paths = PropertyPaths(
        latitude=["points", "latitude"],
        longitude=["points", "longitude"],
        style_by=None,
    )

    lats = list(read_path(data, paths.latitude))
    lons = list(read_path(data, paths.longitude))

    assert lats == [53.1, 3.3, 59.5]
    assert lons == [10.7, 5.5, 70.0]


def test_read_complicated_path():
    data = {
        "items": [
            {"indexTerms": {"geopoint": {"lat": 40.09325, "lon": -122.22687}}},
            {"indexTerms": {"geopoint": {"lat": 0.9166666667, "lon": 19.1}}},
        ]
    }

    paths = PropertyPaths(
        latitude=["items", "indexTerms", "geopoint", "lat"],
        longitude=["items", "indexTerms", "geopoint", "lon"],
        style_by=None,
    )

    lats = list(read_path(data, paths.latitude))
    lons = list(read_path(data, paths.longitude))

    assert lats == [40.09325, 0.9166666667]


def test_render_points_as_geojson():
    geo = render_points_as_geojson(list(zip([53.1, 3.3, 59.5], [10.7, 5.5, 70.0])))

    assert geo == {
        "features": [
            {
                "geometry": {"coordinates": [53.1, 10.7], "type": "Point"},
                "id": 0,
                "properties": {},
                "type": "Feature",
            },
            {
                "geometry": {"coordinates": [3.3, 5.5], "type": "Point"},
                "id": 1,
                "properties": {},
                "type": "Feature",
            },
            {
                "geometry": {"coordinates": [59.5, 70.0], "type": "Point"},
                "id": 2,
                "properties": {},
                "type": "Feature",
            },
        ],
        "type": "FeatureCollection",
    }
