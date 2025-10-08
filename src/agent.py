import json
from typing import override

import dotenv
from ichatbio.agent import IChatBioAgent
from ichatbio.agent_response import ResponseContext, IChatBioAgentProcess
from ichatbio.server import build_agent_app
from ichatbio.types import AgentCard, AgentEntrypoint, Artifact
from pydantic import BaseModel
from starlette.applications import Starlette

from plot import (
    select_properties,
    PropertyPaths,
    GiveUp,
    read_path,
    render_points_as_geojson,
)
from util import retrieve_artifact_content, extract_json_schema


class Parameters(BaseModel):
    artifact: Artifact


class MapAgent(IChatBioAgent):
    """
    A simple example agent with a single entrypoint.
    """

    @override
    def get_agent_card(self) -> AgentCard:
        return AgentCard(
            name="Map Agent",
            description="Visualizes geographic data on interactive maps.",
            icon=None,
            url="http://localhost:9999",
            entrypoints=[
                AgentEntrypoint(
                    id="plot",
                    description="Generates GeoJSON data from JSON artifacts that contain geographic data.",
                    parameters=Parameters,
                )
            ],
        )

    @override
    async def run(
        self,
        context: ResponseContext,
        request: str,
        entrypoint: str,
        params: Parameters,
    ):
        # Start a process to log the agent's actions
        async with context.begin_process(summary="Creating map data") as process:
            process: IChatBioAgentProcess

            content = await retrieve_artifact_content(params.artifact, process)
            schema = extract_json_schema(content)

            match await select_properties(request, schema):
                case PropertyPaths() as paths:
                    # TODO: do all of these at the same time to ensure alignment
                    await process.log(
                        "Using the following property paths",
                        data={
                            "latitude": paths.latitude,
                            "longitude": paths.longitude,
                            "color_by": paths.color_by,
                        },
                    )
                    latitudes = read_path(content, paths.latitude)
                    longitudes = read_path(content, paths.longitude)
                    if paths.color_by:
                        extra_values = read_path(content, paths.color_by)
                    else:
                        extra_values = None

                    coords = list(zip(latitudes, longitudes))
                    geo = render_points_as_geojson(coords, extra_values)

                    await process.create_artifact(
                        mimetype="application/json",
                        description=f"GeoJSON points extracted from artifact {params.artifact.local_id}",
                        content=json.dumps(geo).encode("utf-8"),
                        metadata={"format": "geojson"},
                    )

                case GiveUp(reason=reason):
                    await process.log(f"Failed to generate map parameters: {reason}")
                    return


def create_app() -> Starlette:
    dotenv.load_dotenv()
    agent = MapAgent()
    app = build_agent_app(agent)
    return app
