import json

import dotenv
import instructor.retry
import pydantic
import pytest
from instructor import from_openai, AsyncInstructor
from openai import AsyncOpenAI
from pydantic import BaseModel
from typing_extensions import Self

from conftest import resource
from util import extract_json_schema

dotenv.load_dotenv()

SYSTEM_PROMPT = """\
Your task is to look at a JSON schema and map paths in the schema to variables that the user is interested in, as 
defined by a provided data model.

A path is a list of property names that point to a scalar property. For example,

latitude: ["records", "data", "geo", "latitude"]
"""


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


Path = list[str]


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
        latitude: Path

        @pydantic.model_validator(mode="after")
        def validate(self) -> Self:
            validate_path(self.latitude)
            return self

    return ResponseModel


def test_model():
    content = resource("buried_list_of_lat_lons.json")
    schema = extract_json_schema(json.loads(content))
    model = make_validated_response_model(schema)

    with pytest.raises(pydantic.ValidationError):
        model(latitude=["haha"])

    with pytest.raises(pydantic.ValidationError):
        model(latitude=["points"])

    with pytest.raises(pydantic.ValidationError):
        model(latitude=["latitude"])

    model(latitude=["points", "latitude"])


@pytest.mark.asyncio
async def test_choose_paths():
    content = resource("buried_list_of_lat_lons.json")
    schema = extract_json_schema(json.loads(content))
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
        response = await client.chat.completions.create(
            model="gpt-4.1-unfiltered",
            temperature=0,
            response_model=model,
            messages=messages,
            max_retries=1,
        )
    except instructor.retry.InstructorRetryException as e:
        raise

    assert response == model(latitude=["points", "latitude"])
