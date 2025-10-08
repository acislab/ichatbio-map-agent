import ichatbio.types
import pytest
from ichatbio.agent_response import (
    ArtifactResponse,
    ProcessBeginResponse,
    ProcessLogResponse,
    ResponseMessage,
)

import agent
from conftest import resource
from src.agent import MapAgent


@pytest.mark.httpx_mock(
    should_mock=lambda request: request.url == "https://artifact.test"
)
@pytest.mark.asyncio
async def test_make_geojson(context, messages, httpx_mock):
    content = resource("buried_list_of_lat_lons.json")
    httpx_mock.add_response(url="https://artifact.test", text=content)

    await MapAgent().run(
        context,
        "Get points colored by size",
        "plot",
        agent.Parameters(
            artifact=ichatbio.types.Artifact(
                local_id="#0000",
                description="na",
                mimetype="na",
                uris=["https://artifact.test"],
                metadata={},
            )
        ),
    )

    # Message objects are restricted to the following types:
    messages: list[ResponseMessage]

    # We can test all the agent's responses at once
    assert messages == [
        ProcessBeginResponse(summary="Creating map data", data=None),
        ProcessLogResponse(
            text="Retrieving artifact #0000 content from https://artifact.test",
            data=None,
        ),
        ProcessLogResponse(
            text="Using the following property paths",
            data={
                "latitude": ["points", "latitude"],
                "longitude": ["points", "longitude"],
                "color_by": ["points", "size"],
            },
        ),
        ArtifactResponse(
            mimetype="application/json",
            description="GeoJSON points extracted from artifact #0000",
            uris=None,
            content=b'{"type": "FeatureCollection", "features": [{"type": "Feature", "id": 0, "geometry": {"type": "Point", "coordinates": [10.7, 53.1]}, "properties": {"value": 1.0}}, {"type": "Feature", "id": 1, "geometry": {"type": "Point", "coordinates": [5.5, 3.3]}, "properties": {"value": 2.0}}, {"type": "Feature", "id": 2, "geometry": {"type": "Point", "coordinates": [70.0, 59.5]}, "properties": {"value": 3.0}}]}',
            metadata={"format": "geojson"},
        ),
    ]
