import httpx
from genson import SchemaBuilder
from genson.schema.strategies import Object
from ichatbio.agent_response import IChatBioAgentProcess
from ichatbio.types import Artifact

JSON = dict | list | str | int | float | None
"""JSON-serializable primitive types that work with functions like json.dumps(). Note that dicts and lists may contain
content that is not JSON-serializable."""


def contains_non_null_content(content: JSON):
    """
    Returns True only if the JSON-serializable content contains a non-empty value. For example, returns True for [[1]]
    and False for [[]].
    """
    match content:
        case None:
            return False
        case list() as l:
            return any([contains_non_null_content(v) for v in l])
        case dict() as d:
            return any([contains_non_null_content(v) for k, v in d.items()])
        case _:
            return True


# JSON schema extraction


class NoRequiredObject(Object):
    KEYWORDS = tuple(kw for kw in Object.KEYWORDS if kw != "required")

    # Remove "required" from the output if present
    def to_schema(self):
        schema = super().to_schema()
        if "required" in schema:
            del schema["required"]
        return schema


class NoRequiredSchemaBuilder(SchemaBuilder):
    """SchemaBuilder that does not use the "required" keyword, which roughly doubles the length of the schema string,
    and also isn't very helpful for our purposes."""

    EXTRA_STRATEGIES = (NoRequiredObject,)


def extract_json_schema(content: str) -> dict:
    builder = NoRequiredSchemaBuilder()
    builder.add_object(content)
    schema = builder.to_schema()
    return schema


async def retrieve_artifact_content(
    artifact: Artifact, process: IChatBioAgentProcess
) -> JSON:
    async with httpx.AsyncClient(follow_redirects=True) as internet:
        for url in artifact.get_urls():
            await process.log(
                f"Retrieving artifact {artifact.local_id} content from {url}"
            )
            response = await internet.get(url)
            if response.is_success:
                return response.json()  # TODO: catch exception?
            else:
                await process.log(
                    f"Failed to retrieve artifact content: {response.reason_phrase} ({response.status_code})"
                )
                raise ValueError()
        else:
            await process.log("Failed to find artifact content")
            raise ValueError()
