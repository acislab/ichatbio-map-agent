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
    paths = await select_properties("Extract point data", schema)

    assert paths == PropertyPaths(
        latitude=["points", "latitude"],
        longitude=["points", "longitude"],
        color_by=None,
    )


def test_extract_path_values():
    data = json.loads(resource("buried_list_of_lat_lons.json"))

    paths = PropertyPaths(
        latitude=["points", "latitude"],
        longitude=["points", "longitude"],
        color_by=None,
    )

    lats = list(read_path(data, paths.latitude))
    lons = list(read_path(data, paths.longitude))

    assert lats == [53.1, 3.3, 59.5]
    assert lons == [10.7, 5.5, 70.0]


def test_read_complicated_path_one():
    data = {
        "items": [
            {"indexTerms": {"geopoint": {"lat": 40.09325, "lon": -122.22687}}},
            {"indexTerms": {"geopoint": {"lat": 0.9166666667, "lon": 19.1}}},
        ]
    }

    paths = PropertyPaths(
        latitude=["items", "indexTerms", "geopoint", "lat"],
        longitude=["items", "indexTerms", "geopoint", "lon"],
        color_by=None,
    )

    lats = list(read_path(data, paths.latitude))
    lons = list(read_path(data, paths.longitude))

    assert lats == [40.09325, 0.9166666667]
    assert lons == [-122.22687, 19.1]


def test_read_complicated_path_with_string_values():
    data = {
        "items": [
            {
                "data": {
                    "dwc:decimalLatitude": "23.075",
                    "dwc:decimalLongitude": "-99.225",
                }
            },
            {
                "data": {
                    "dwc:decimalLatitude": "23.1083333",
                    "dwc:decimalLongitude": "-99.2416667",
                }
            },
        ]
    }

    paths = PropertyPaths(
        latitude=["items", "data", "dwc:decimalLatitude"],
        longitude=["items", "data", "dwc:decimalLongitude"],
        color_by=None,
    )

    lats = list(read_path(data, paths.latitude))
    lons = list(read_path(data, paths.longitude))

    assert lats == [23.075, 23.1083333]
    assert lons == [-99.225, -99.2416667]


def test_missing_properties():
    data = {
        "items": [
            {
                "data": {
                    "dwc:decimalLatitude": "23.075",
                    "dwc:decimalLongitude": "-99.225",
                }
            },
            {"data": {}},
        ]
    }

    paths = PropertyPaths(
        latitude=["items", "data", "dwc:decimalLatitude"],
        longitude=["items", "data", "dwc:decimalLongitude"],
        color_by=None,
    )

    lats = list(read_path(data, paths.latitude))
    lons = list(read_path(data, paths.longitude))

    assert lats == [23.075, None]
    assert lons == [-99.225, None]


def test_render_points_as_geojson():
    geo = render_points_as_geojson(
        coordinates=list(zip([53.1, 3.3, 59.5], [10.7, 5.5, 70.0])),
        values=[0.1, 0.2, 0.3],
    )

    assert geo == {
        "features": [
            {
                "geometry": {"coordinates": [10.7, 53.1], "type": "Point"},
                "id": 0,
                "properties": {"value": 0.1},
                "type": "Feature",
            },
            {
                "geometry": {"coordinates": [5.5, 3.3], "type": "Point"},
                "id": 1,
                "properties": {"value": 0.2},
                "type": "Feature",
            },
            {
                "geometry": {"coordinates": [70.0, 59.5], "type": "Point"},
                "id": 2,
                "properties": {"value": 0.3},
                "type": "Feature",
            },
        ],
        "type": "FeatureCollection",
    }
