import json
from typing import Iterable

from pydantic import BaseModel

from conftest import resource
from util import extract_json_schema


class MapCoordinateProperties(BaseModel):
    path_to_records_list: str
    record_latitude: str
    record_longitude: str


Path: list[str]


# def find_records_arrays(
#     schema: dict, path: Iterable[str] = ()
# ) -> Iterator[SchemaRecords]:
#     match schema["type"]:
#         case "array":
#             yield SchemaRecords(path, schema)
#         case "object":
#             for property_name, property_schema in schema["properties"].items():
#                 yield from find_records_arrays(property_schema, (*path, property_name))
#         case _:
#             return


def find_properties(schema: dict, path: Iterable[str] = ()) -> MapCoordinateProperties:
    match schema["type"]:
        case "object":
            latitude = None
            longitude = None
            for property_name, property_schema in schema["properties"].items():
                match property_name:
                    case "number" | "string":
                        if "latitude" in property_name.lower():
                            latitude = property_name
                        elif "longitude" in property_name.lower():
                            longitude = property_name
            if latitude and longitude:
                yield


def test_extract_schema():
    content = resource("list_of_lat_lons.json")

    schema = extract_json_schema(json.loads(content))

    assert schema == {
        "$schema": "http://json-schema.org/schema#",
        "items": {
            "properties": {
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
            },
            "type": "object",
        },
        "type": "array",
    }


def test_extract_schema_for_buried_data():
    content = resource("buried_list_of_lat_lons.json")

    schema = extract_json_schema(json.loads(content))

    assert schema == {
        "$schema": "http://json-schema.org/schema#",
        "properties": {
            "points": {
                "items": {
                    "properties": {
                        "latitude": {"type": "number"},
                        "longitude": {"type": "number"},
                    },
                    "type": "object",
                },
                "type": "array",
            },
            "version": {"type": "integer"},
        },
        "type": "object",
    }


def test_extract_schema_for_list_of_buried_lat_lons():
    content = resource("list_of_buried_lat_lons.json")

    schema = extract_json_schema(json.loads(content))

    assert schema == {
        "$schema": "http://json-schema.org/schema#",
        "items": {
            "properties": {
                "point": {
                    "properties": {
                        "latitude": {"type": "number"},
                        "longitude": {"type": "number"},
                    },
                    "type": "object",
                }
            },
            "type": "object",
        },
        "type": "array",
    }


def test_extract_schema_from_list_of_lat_lon_strings():
    content = resource("list_of_lat_lon_strings.json")

    schema = extract_json_schema(json.loads(content))

    assert schema == {
        "$schema": "http://json-schema.org/schema#",
        "items": {
            "properties": {
                "latitude": {"type": "string"},
                "longitude": {"type": "string"},
            },
            "type": "object",
        },
        "type": "array",
    }
