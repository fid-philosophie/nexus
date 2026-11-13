# api.py
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from typing import Literal, Annotated
from . import nexus  # !local module!
from .config import settings # !local module!
from .input_parser import parse_identifiers_json
from .identifiers import validate_identifier

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
    description="LOD aggregation",
    contact=contact or None,
    docs_url="/",
    redoc_url="/redoc"
)

if settings.allow_origins:
    cors_methods = ["GET"]

    if settings.enable_custom_mappings:
        cors_methods.append("POST")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=False,
        allow_methods=cors_methods,
        allow_headers=["Content-Type"],
    )

async def get_identifiers(
    dict_identifiers: Annotated[
        str,
        Query(
            description=(
                "JSON object containing at least one resource identifier. "
                "Keys and values must be strings."
            ),
            examples=['{"Wikidata":"Q9312","GND":"118559796"}'],
        ),
    ],
) -> dict[str, str]:
    try:
        return parse_identifiers_json(dict_identifiers)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=(
                "dict_identifiers must be a non-empty JSON object "
                "with string values"
            ),
        ) from exc

class In(BaseModel):
    mapping_profile: Literal[
        "person",
        "work",
        "event",
        "place",
        "corporation",
        "wikidata-entity"
    ] = Field(
        default="person",
        description="Profile key that selects a preset mapping strategy."
    )
    dict_identifiers: dict[str, str] = Field(
        min_length=1,
        description="Dictionary of resource identifiers. If you set add_identifiers true, you can simply provide the Wikidata identifier and Nexus will try to fetch available identifiers from other sources.",
        examples=[
            {'Wikidata':'Q352098'},
            {'Wikidata': 'Q9312'},
            {'Wikidata': 'Q9312', 'GND': '118559796', 'LCNAF': 'n79021614', 'VIAF': '82088490'}
            ],
        default_factory=lambda: {'Wikidata':'Q352098'}
    )
    add_identifiers: bool = Field(
        description="If set true (and given a Wikidata identifier), Nexus will try to fetch identifiers from other resources.",
        examples=[True, False],
        default=True
    )
    flatten: bool = Field(
        description="If set true, a flattened output will be returned.",
        examples=[False, True],
        default=False
    )

class In_Entity(BaseModel):
    @field_validator("dict_identifiers", mode="after")
    @classmethod
    def check_identifiers(
        cls,
        value: dict[str, str] | None,
    ) -> dict[str, str] | None:

        if value is not None:
            for source_name, identifier in value.items():
                validate_identifier(source_name, identifier)

        return value
    mapping_profile: Literal[
        "corporation",
        "event",
        "hub_wikidata",
        "knowledgebox_deu",
        "person",
        "place",
        "project",
        "scholarly_edition",
        "wikidata_entity",
        "work",
    ] = Field(
        default="person",
        description="Profile key that selects a preset mapping strategy."
    )
    dict_identifiers: dict[str, str] = Field(
        min_length=1,
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
        default_factory=lambda: {"Wikidata": "Q352098"},
        validate_default=True,
    )
    add_identifiers: bool = Field(
        description="If set true (and given a Wikidata identifier), Nexus will try to fetch identifiers from other resources.",
        examples=[True, False],
        default=True
    )
    flatten: bool = Field(
        description="If set true, a flattened output will be returned.",
        examples=[False, True],
        default=False
    )

# class In_Corporation(BaseModel):
#     dict_identifiers: str = Field(
#         description="Dictionary of resource identifiers. If you set add_identifiers true, you can simply provide the Wikidata identifier and Nexus will try to fetch available identifiers from other sources.",
#         examples=["{'Wikidata':'Q352098'}","{'Wikidata': 'Q9312'}","{'Wikidata': 'Q9312', 'GND': '118559796', 'LCNAF': 'n79021614', 'VIAF': '82088490'}"],
#         default={'Wikidata':'Q2062620'}
#     )
#     add_identifiers: bool = Field(
#         description="If set true (and given a Wikidata identifier), Nexus will try to fetch identifiers from other resources.",
#         examples=[True, False],
#         default=True
#     )
#     flatten: bool = Field(
#         description="If set true, a flattened output will be returned.",
#         examples=[False, True],
#         default=False
#     )

# class In_Event(BaseModel):
#     dict_identifiers: str = Field(
#         description="Dictionary of resource identifiers. If you set add_identifiers true, you can simply provide the Wikidata identifier and Nexus will try to fetch available identifiers from other sources.",
#         examples=["{'Wikidata':'Q352098'}","{'Wikidata': 'Q9312'}","{'Wikidata': 'Q9312', 'GND': '118559796', 'LCNAF': 'n79021614', 'VIAF': '82088490'}"],
#         default={'Wikidata':'Q3087660'}
#     )
#     add_identifiers: bool = Field(
#         description="If set true (and given a Wikidata identifier), Nexus will try to fetch identifiers from other resources.",
#         examples=[True, False],
#         default=True
#     )
#     flatten: bool = Field(
#         description="If set true, a flattened output will be returned.",
#         examples=[False, True],
#         default=False
#     )

# class In_Hub_Wikidata(BaseModel):
#     dict_identifiers: str = Field(
#         description="Dictionary of resource identifiers. If you set add_identifiers true, you can simply provide the Wikidata identifier and Nexus will try to fetch available identifiers from other sources.",
#         examples=["{'Wikidata':'Q352098'}","{'Wikidata': 'Q9312'}","{'Wikidata': 'Q9312', 'GND': '118559796', 'LCNAF': 'n79021614', 'VIAF': '82088490'}"],
#         default={'Wikidata':'Q9312'}
#     )
#     add_identifiers: bool = Field(
#         description="If set true (and given a Wikidata identifier), Nexus will try to fetch identifiers from other resources.",
#         examples=[True, False],
#         default=True
#     )
#     flatten: bool = Field(
#         description="If set true, a flattened output will be returned.",
#         examples=[False, True],
#         default=False
#     )

# class In_Knowledgebox_Deu(BaseModel):
#     dict_identifiers: str = Field(
#         description="Dictionary of resource identifiers. If you set add_identifiers true, you can simply provide the Wikidata identifier and Nexus will try to fetch available identifiers from other sources.",
#         examples=["{'Wikidata':'Q352098'}","{'Wikidata': 'Q9312'}","{'Wikidata': 'Q9312', 'GND': '118559796', 'LCNAF': 'n79021614', 'VIAF': '82088490'}"],
#         default={'Wikidata':'Q9312'}
#     )
#     add_identifiers: bool = Field(
#         description="If set true (and given a Wikidata identifier), Nexus will try to fetch identifiers from other resources.",
#         examples=[True, False],
#         default=True
#     )
#     flatten: bool = Field(
#         description="If set true, a flattened output will be returned.",
#         examples=[False, True],
#         default=False
#     )

# class In_Person(BaseModel):
#     dict_identifiers: dict[str, str] = Field(
#         min_length=1,
#         description="Dictionary of resource identifiers. If you set add_identifiers true, you can simply provide the Wikidata identifier and Nexus will try to fetch available identifiers from other sources.",
#         examples=[
#             {'Wikidata':'Q352098'},
#             {'Wikidata': 'Q9312'},
#             {'Wikidata': 'Q9312', 'GND': '118559796', 'LCNAF': 'n79021614', 'VIAF': '82088490'}
#             ],
#         default_factory=lambda: {'Wikidata':'Q352098'}
#     )

#     add_identifiers: bool = Field(
#         description="If set true (and given a Wikidata identifier), Nexus will try to fetch identifiers from other resources.",
#         examples=[True, False],
#         default=True
#     )
#     flatten: bool = Field(
#         description="If set true, a flattened output will be returned.",
#         examples=[False, True],
#         default=False
#     )

# class In_Place(BaseModel):
#     dict_identifiers: str = Field(
#         description="Dictionary of resource identifiers. If you set add_identifiers true, you can simply provide the Wikidata identifier and Nexus will try to fetch available identifiers from other sources.",
#         examples=["{'Wikidata':'Q352098'}","{'Wikidata': 'Q9312'}","{'Wikidata': 'Q9312', 'GND': '118559796', 'LCNAF': 'n79021614', 'VIAF': '82088490'}"],
#         default={'Wikidata':'Q4120832'}
#     )
#     add_identifiers: bool = Field(
#         description="If set true (and given a Wikidata identifier), Nexus will try to fetch identifiers from other resources.",
#         examples=[True, False],
#         default=True
#     )
#     flatten: bool = Field(
#         description="If set true, a flattened output will be returned.",
#         examples=[False, True],
#         default=False
#     )

# class In_Project(BaseModel):
#     dict_identifiers: str = Field(
#         description="Dictionary of resource identifiers. If you set add_identifiers true, you can simply provide the Wikidata identifier and Nexus will try to fetch available identifiers from other sources.",
#         examples=["{'Wikidata':'Q352098'}","{'Wikidata': 'Q9312'}","{'Wikidata': 'Q9312', 'GND': '118559796', 'LCNAF': 'n79021614', 'VIAF': '82088490'}"],
#         default={'Wikidata':'Q1225026'}
#     )
#     add_identifiers: bool = Field(
#         description="If set true (and given a Wikidata identifier), Nexus will try to fetch identifiers from other resources.",
#         examples=[True, False],
#         default=True
#     )
#     flatten: bool = Field(
#         description="If set true, a flattened output will be returned.",
#         examples=[False, True],
#         default=False
#     )

# class In_Wikidata_Entity(BaseModel):
#     dict_identifiers: str = Field(
#         description="Dictionary of resource identifiers. If you set add_identifiers true, you can simply provide the Wikidata identifier and Nexus will try to fetch available identifiers from other sources.",
#         examples=["{'Wikidata':'Q352098'}","{'Wikidata': 'Q9312'}","{'Wikidata': 'Q9312', 'GND': '118559796', 'LCNAF': 'n79021614', 'VIAF': '82088490'}"],
#         default={'Wikidata':'Q9312'}
#     )
#     add_identifiers: bool = Field(
#         description="If set true (and given a Wikidata identifier), Nexus will try to fetch identifiers from other resources.",
#         examples=[True, False],
#         default=True
#     )
#     flatten: bool = Field(
#         description="If set true, a flattened output will be returned.",
#         examples=[False, True],
#         default=False
#     )

# class In_Work(BaseModel):
#     dict_identifiers: str = Field(
#         description="Dictionary of resource identifiers. If you set add_identifiers true, you can simply provide the Wikidata identifier and Nexus will try to fetch available identifiers from other sources.",
#         examples=["{'Wikidata':'Q352098'}","{'Wikidata': 'Q9312'}","{'Wikidata': 'Q9312', 'GND': '118559796', 'LCNAF': 'n79021614', 'VIAF': '82088490'}"],
#         default={'Wikidata':'Q139893710'}
#     )
#     add_identifiers: bool = Field(
#         description="If set true (and given a Wikidata identifier), Nexus will try to fetch identifiers from other resources.",
#         examples=[True, False],
#         default=True
#     )
#     flatten: bool = Field(
#         description="If set true, a flattened output will be returned.",
#         examples=[False, True],
#         default=False
#     )

if settings.enable_custom_mappings: # should only be enabled in safe environments (e.g. running the API locally)
    @app.post("/custom_mapping")
    async def nexus_custom_mapping(inp: In):
        result = await run_in_threadpool(
            nexus.run_nexus,
            inp.mapping_profile,
            inp.dict_identifiers,
            inp.add_identifiers,
            inp.flatten,
            "default"
        )
        return {"result": result}

# @app.get("/entity")
# async def nexus_entity(inp: In_Entity = Depends()):
#     result = await run_in_threadpool(
#         nexus.run_nexus,
#         inp.mapping_profile,
#         inp.dict_identifiers,
#         inp.add_identifiers,
#         inp.flatten,
#         "default"
#     )
#     return {"result": result}

@app.post("/entity")
async def nexus_entity(inp: In_Entity):
    result = await run_in_threadpool(
        nexus.run_nexus,
        inp.mapping_profile,
        inp.dict_identifiers,
        inp.add_identifiers,
        inp.flatten,
        "default",
    )
    return {"result": result}

# @app.get("/corporation")
# async def nexus_corporation(inp: In_Corporation = Depends()):
#     result = await run_in_threadpool(
#         nexus.run_nexus,
#         "corporation",
#         inp.dict_identifiers,
#         inp.add_identifiers,
#         inp.flatten,
#         "default"
#     )
#     return {"result": result}

# @app.get("/event")
# async def nexus_event(inp: In_Event = Depends()):
#     result = await run_in_threadpool(
#         nexus.run_nexus,
#         "event",
#         inp.dict_identifiers,
#         inp.add_identifiers,
#         inp.flatten,
#         "default"
#     )
#     return {"result": result}

# @app.get("/hub_wikidata")
# async def nexus_hub_wikidata(inp: In_Hub_Wikidata = Depends()):
#     result = await run_in_threadpool(
#         nexus.run_nexus,
#         "hub_wikidata",
#         inp.dict_identifiers,
#         inp.add_identifiers,
#         inp.flatten,
#         "default"
#     )
#     return {"result": result}

# @app.get("/knowledgebox_deu")
# async def nexus_knowledgebox_deu(inp: In_Knowledgebox_Deu = Depends()):
#     result = await run_in_threadpool(
#         nexus.run_nexus,
#         "knowledgebox_deu",
#         inp.dict_identifiers,
#         inp.add_identifiers,
#         inp.flatten,
#         "default"
#     )
#     return {"result": result}

# # @app.get("/person")
# # async def nexus_person(inp: In_Person = Depends()):
# #     result = await run_in_threadpool(
# #         nexus.run_nexus,
# #         "person",
# #         inp.dict_identifiers,
# #         inp.add_identifiers,
# #         inp.flatten,
# #         "default"
# #     )
# #     return {"result": result}


# @app.get("/person")
# async def nexus_person(
#     identifiers: Annotated[dict[str, str], Depends(get_identifiers)],
#     add_identifiers: bool = True,
#     flatten: bool = False,
# ):
#     result = await run_in_threadpool(
#         nexus.run_nexus,
#         "person",
#         identifiers,
#         add_identifiers,
#         flatten,
#         "default",
#     )

#     return {"result": result}

# @app.get("/place")
# async def nexus_place(inp: In_Place = Depends()):
#     result = await run_in_threadpool(
#         nexus.run_nexus,
#         "place",
#         inp.dict_identifiers,
#         inp.add_identifiers,
#         inp.flatten,
#         "default"
#     )
#     return {"result": result}

# @app.get("/project")
# async def nexus_project(inp: In_Project = Depends()):
#     result = await run_in_threadpool(
#         nexus.run_nexus,
#         "project",
#         inp.dict_identifiers,
#         inp.add_identifiers,
#         inp.flatten,
#         "default"
#     )
#     return {"result": result}

# @app.get("/wikidata_entity")
# async def nexus_wikidata_entity(inp: In_Wikidata_Entity = Depends()):
#     result = await run_in_threadpool(
#         nexus.run_nexus,
#         "wikidata_entity",
#         inp.dict_identifiers,
#         inp.add_identifiers,
#         inp.flatten,
#         "default"
#     )
#     return {"result": result}

# @app.get("/work")
# async def nexus_work(inp: In_Work = Depends()):
#     result = await run_in_threadpool(
#         nexus.run_nexus,
#         "work",
#         inp.dict_identifiers,
#         inp.add_identifiers,
#         inp.flatten,
#         "default"
#     )
#     return {"result": result}