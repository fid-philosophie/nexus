# api.py
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from typing import Literal, Annotated
from . import nexus  # !local module!
from .config import settings # !local module!
from .input_parser import parse_identifiers_json
from .identifiers import validate_identifier

import json
from pathlib import Path
from typing import Any, Self

from jsonschema import ValidationError as MappingValidationError
from jsonschema import validate
from pydantic import ConfigDict, Field, model_validator

MAPPINGS_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "schema"
    / "nexus_mappings_schema.json"
)

with MAPPINGS_SCHEMA_PATH.open("r", encoding="utf-8") as file:
    MAPPINGS_SCHEMA = json.load(file)

# load default mappings/profiles from mappings folder:
MAPPINGS_DIR = (
    Path(__file__).resolve().parent.parent
    / "mappings"
)

DEFAULT_MAPPINGS = nexus.generate_nexus_mappings_json(
    str(MAPPINGS_DIR)
)

# Check the loaded mapping document against the existing schema.
validate(
    instance=DEFAULT_MAPPINGS,
    schema=MAPPINGS_SCHEMA,
)

# Index the mappings by their actual profile names.
MAPPINGS_BY_PROFILE: dict[str, dict[str, Any]] = {}

for profile in DEFAULT_MAPPINGS["mappings"]:
    profile_name = profile["mappingProfile"]

    if profile_name in MAPPINGS_BY_PROFILE:
        raise RuntimeError(
            f"Duplicate mapping profile: {profile_name!r}"
        )

    MAPPINGS_BY_PROFILE[profile_name] = profile

PROFILE_NAMES = sorted(MAPPINGS_BY_PROFILE)

DEFAULT_PROFILE_NAME = "person"

if DEFAULT_PROFILE_NAME not in MAPPINGS_BY_PROFILE:
    raise RuntimeError(
        f"Default mapping profile {DEFAULT_PROFILE_NAME!r} not found."
    )

DEFAULT_MAPPING_PROFILE = MAPPINGS_BY_PROFILE[DEFAULT_PROFILE_NAME]

# example data for custom mapping:
CUSTOM_MAPPING_EXAMPLE = {
    "mapping_profile": DEFAULT_MAPPING_PROFILE["mappingProfile"],
    "dict_identifiers": {
        "Wikidata": "Q9312",
        "GND": "118559796",
    },
    "add_identifiers": False,
    "flatten": True,
    "nexus_mappings_json": {
        "mappings": [DEFAULT_MAPPING_PROFILE],
    },
}

contact = {
    key: value
    for key, value in {
        "name": settings.api_contact_name.strip(),
        "email": settings.api_contact_email.strip(),
    }.items()
    if value
}

app = FastAPI(
    title="Nexus API",
    version="0.9.0",
    description=(
    "Nexus aggregates linked open data using configurable source priorities "
    "and falls back to sources with a lower priority when a field value "
    "is unavailable."
    ),
    contact=contact or None,
    docs_url="/",
    redoc_url="/redoc"
)

api_router = APIRouter()


if settings.allow_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=False,
        allow_methods=["POST"],
        allow_headers=["Content-Type"],
    )

class In(BaseModel):
    dict_identifiers: dict[str, str] = Field(
        default_factory=lambda: {"Wikidata": "Q352098"},
        min_length=1,
        validate_default=True,
        description=(
            "Dictionary of resource identifiers. "
            "If you set add_identifiers true, you can simply provide "
            "the Wikidata identifier and Nexus will try to fetch "
            "available identifiers from other sources."
        ),
        examples=[
            {"Wikidata": "Q352098"},
            {"Wikidata": "Q9312"},
            {
                "Wikidata": "Q9312",
                "GND": "118559796",
                "LCNAF": "n79021614",
                "VIAF": "82088490",
            },
        ],
    )

    add_identifiers: bool = Field(
        default=False,
        description=(
            "If set true and a Wikidata identifier is given, "
            "Nexus will try to fetch identifiers from other resources."
        ),
        examples=[True, False],
    )

    flatten: bool = Field(
        default=False,
        description=(
            "If set true, a flattened output will be returned."
        ),
        examples=[False, True],
    )

    @field_validator("dict_identifiers", mode="after")
    @classmethod
    def check_identifiers(
        cls,
        value: dict[str, str],
    ) -> dict[str, str]:
        for source_name, identifier in value.items():
            validate_identifier(source_name, identifier)

        return value


class In_Entity(In):
    mapping_profile: str = Field(
        default=DEFAULT_PROFILE_NAME,
        validate_default=True,
        description=(
            "Profile key that selects a preset mapping strategy."
        ),
        json_schema_extra={
            "enum": PROFILE_NAMES,
        },
    )

    @field_validator("mapping_profile", mode="after")
    @classmethod
    def check_mapping_profile(cls, value: str) -> str:
        if value not in MAPPINGS_BY_PROFILE:
            raise ValueError(
                "Unknown mapping profile. Choose one of: "
                + ", ".join(PROFILE_NAMES)
            )

        return value

class In_CustomMapping(In):
    model_config = ConfigDict(
        validate_default=True,
        json_schema_extra={
            "examples": [CUSTOM_MAPPING_EXAMPLE],
        },
    )

    mapping_profile: str = Field(
        default=CUSTOM_MAPPING_EXAMPLE["mapping_profile"],
        min_length=1,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Name of the profile contained in the custom mapping.",
    )

    dict_identifiers: dict[str, str] = Field(
        default=CUSTOM_MAPPING_EXAMPLE["dict_identifiers"],
        min_length=1,
        description=(
            "Dictionary of resource identifiers. "
            "If add_identifiers is true, additional identifiers "
            "can be retrieved using the Wikidata identifier."
        ),
    )

    add_identifiers: bool = Field(
        default=CUSTOM_MAPPING_EXAMPLE["add_identifiers"],
        description=(
            "If true and a Wikidata identifier is given, "
            "try to retrieve identifiers for additional sources."
        ),
    )

    flatten: bool = Field(
        default=CUSTOM_MAPPING_EXAMPLE["flatten"],
        description=(
            "If true, return field values without provenance metadata."
        ),
    )

    nexus_mappings_json: dict[str, Any] = Field(
        default=CUSTOM_MAPPING_EXAMPLE["nexus_mappings_json"],
        description=(
            "Complete Nexus mapping document containing a mappings array."
        ),
    )

    @model_validator(mode="after")
    def check_custom_mapping(self) -> Self:
        try:
            validate(
                instance=self.nexus_mappings_json,
                schema=MAPPINGS_SCHEMA,
            )
        except MappingValidationError as exc:
            raise ValueError(
                f"Invalid custom mapping at {exc.json_path}: {exc.message}"
            ) from exc

        matching_profiles = sum(
            profile["mappingProfile"] == self.mapping_profile
            for profile in self.nexus_mappings_json["mappings"]
        )

        if matching_profiles != 1:
            raise ValueError(
                "mapping_profile must identify exactly one profile "
                "in nexus_mappings_json"
            )

        return self

if settings.enable_custom_mappings: # should only be enabled in safe environments (e.g. running the API locally)
    @api_router.post("/custom_mapping", operation_id="custom_mapping_v1")
    async def nexus_custom_mapping(inp: In_CustomMapping):
        result = await run_in_threadpool(
            nexus.run_nexus,
            inp.mapping_profile,
            inp.dict_identifiers,
            inp.add_identifiers,
            inp.flatten,
            inp.nexus_mappings_json,
        )
        return {"result": result}

@api_router.post("/entity", operation_id="entity_v1")
async def nexus_entity(inp: In_Entity):
    result = await run_in_threadpool(
        nexus.run_nexus,
        inp.mapping_profile,
        inp.dict_identifiers,
        inp.add_identifiers,
        inp.flatten,
        DEFAULT_MAPPINGS,
    )
    return {"result": result}

app.include_router(api_router, prefix="/v1")