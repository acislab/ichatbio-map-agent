import json

import pydantic
import pytest

import plot
from conftest import resource
from plot import make_validated_response_model, PropertyPaths
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
    response = await plot.select_properties(schema)

    assert response == PropertyPaths(
        latitude=["points", "latitude"],
        longitude=["points", "longitude"],
        style_by=None,
    )
