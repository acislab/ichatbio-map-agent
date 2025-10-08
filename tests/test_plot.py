import json

import pydantic
import pytest

from conftest import resource
from plot import make_validated_response_model, PropertyPaths
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


@pytest.mark.asyncio
async def test_extract_path_values():
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
