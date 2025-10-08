from typing import Optional, Self, Iterator

import geojson
import pydantic
from instructor import from_openai, retry, AsyncInstructor
from openai import AsyncOpenAI
from pydantic import BaseModel

from util import JSON

Path = list[str]


class GiveUp(BaseModel):
    reason: str


class PropertyPaths(BaseModel):
    latitude: Path
    longitude: Path
    style_by: Optional[Path] = None


def trace_path_in_schema(schema: dict, target_path: list[str], index=0):
    if index < len(target_path):
        match schema.get("type"):
            case "object":
                next_property = schema["properties"].get(target_path[index])
                if next_property:
                    return trace_path_in_schema(next_property, target_path, index + 1)
            case "array":
                return trace_path_in_schema(schema["items"], target_path, index)

    return target_path[:index], schema


def make_validated_response_model(schema: dict, allowed_types=("number", "string")):
    def validate_path(path: list[str]):
        trace, terminal_schema = trace_path_in_schema(schema, path)

        if trace != path:
            terminal_type = terminal_schema["type"]
            raise ValueError(
                f'Path does not exist in provided schema. Tip: {terminal_type} at path {trace} does not contain a property named "{path[len(trace)]}"'
            )

        if terminal_schema["type"] not in allowed_types:
            terminal_type = terminal_schema["type"]
            raise ValueError(
                f'Path {trace} in the schema has invalid type "{terminal_type}"; expected {allowed_types}'
            )

        return path

    class ResponseModel(BaseModel):
        response: GiveUp | PropertyPaths

        @pydantic.model_validator(mode="after")
        def validate(self) -> Self:
            match self.response:
                case PropertyPaths() as paths:
                    validate_path(paths.latitude)
                    validate_path(paths.longitude)
                    if paths.style_by:
                        validate_path(paths.style_by)
            return self

    return ResponseModel


SYSTEM_PROMPT = """\
Your task is to look at a JSON schema and map paths in the schema to variables that the user is interested in, as 
defined by a provided data model.

A path is a list of property names that point to a scalar property. For example,

latitude: ["records", "data", "geo", "latitude"]
"""


async def select_properties(schema: dict):
    model = make_validated_response_model(schema)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Here is the schema of my data:\n\n{schema}",
        },
    ]

    client: AsyncInstructor = from_openai(AsyncOpenAI())
    try:
        generation = await client.chat.completions.create(
            model="gpt-4.1-unfiltered",
            temperature=0,
            response_model=model,
            messages=messages,
            max_retries=5,
        )
    except retry.InstructorRetryException as e:
        raise

    return generation.response


def read_path(content: JSON, path: list[str]) -> Iterator[float]:
    layer = content[path[0]]
    match layer:
        case list() as records:
            for record in records:
                yield from read_path(record, path[1:])
        case dict() as record:
            yield from read_path(layer, path[1:])
        case _ as property if len(path) == 1:
            try:
                yield float(property)
            except ValueError:
                yield None


def render_points_as_geojson(
    coordinates: list[(float, float)], properties: list[dict] = None
) -> geojson.FeatureCollection:
    if properties is None:
        properties = ({} for _ in coordinates)

    geo = geojson.FeatureCollection(
        [
            geojson.Feature(id=i, geometry=geojson.Point((lat, lon)), properties=props)
            for i, ((lat, lon), props) in enumerate(zip(coordinates, properties))
        ]
    )

    return geo
