# api.py
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from fastapi.concurrency import run_in_threadpool
import nexus  # !local module!
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Nexus API",
    version="0.0.1",
    description="prioritised LOD aggregation",
    contact={"name": "FID Philosophie", "email": "phil-finder@uni-koeln.de"},
    root_path="/nexus",
    docs_url="/",
    redoc_url="/redoc"
)

# List of allowed origins
origins = [
    "http://127.0.0.1:8000",            # Symfony/Twig dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,              # only allow these origins (not "*")
    allow_credentials=True,             # if you need cookies/authorization headers
    allow_methods=["POST"],             # limit to what you need
    allow_headers=["Content-Type"],     # you can add "Authorization", etc. if required
)

class In(BaseModel):
    mapping_profile: str = Field(
        description="Profile key that selects a preset mapping strategy.",
        examples=["person", "work", "event", "location", "corporation", "wikidata-entity"],
        default="person"
    )
    dict_identifiers: str = Field(
        description="Dictionary of resource identifiers. If you set add_identifiers true, you can simply provide the Wikidata identifier and Nexus will try to fetch available identifiers from other sources.",
        examples=["{'Wikidata':'Q352098'}","{'Wikidata': 'Q9312'}","{'Wikidata': 'Q9312', 'GND': '118559796', 'LCNAF': 'n79021614', 'VIAF': '82088490'}"],
        default={'Wikidata':'Q352098'}
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

@app.post("/run_nexus_endpoint")
async def run_nexus_endpoint(inp: In):
    result = await run_in_threadpool(
        nexus.run_nexus,
        inp.mapping_profile,
        inp.dict_identifiers,
        inp.add_identifiers,
        inp.flatten,
        "default"
    )
    return {"result": result}