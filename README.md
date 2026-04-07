# nexus_api

Python-based Linked Open Data aggregation service wrapped with **FastAPI**.
The service queries multiple authority sources (e.g. Wikidata, GND, VIAF, LCNAF), aggregates prioritized results, and returns structured **factlets** or flattened output.

Caching of HTTP responses is handled via **Redis**.

---

# Quick start (Docker recommended)

## 1) Clone repository

```bash
git clone <your-repository-url>
cd nexus_api
```

## 2) Create `.env`

Create a file:

```
.env
```

with contents:

```env
REDIS_HOST=redis
REDIS_PORT=6379
APP_HOST=0.0.0.0
APP_PORT=8000
```

---

## 3) Start services

Run:

```bash
docker compose up --build
```

This starts:

* FastAPI server
* Redis cache service

---

## 4) Open API documentation

Open in browser:

```
http://localhost:8000/
```

Alternative documentation:

```
http://localhost:8000/redoc
```

---

## 5) Test endpoint via curl

Example:

```bash
curl -X POST http://127.0.0.1:8000/run_nexus_endpoint \
  -H "Content-Type: application/json" \
  -d '{
    "nexus_mappings_json": "default",
    "mapping_profile": "person",
    "dict_identifiers": "{\"Wikidata\":\"Q9312\"}",
    "add_identifiers": true,
    "flatten": false
  }'
```

---

## 6) Stop services

```bash
docker compose down
```

---

# Local development setup (without Docker)

## Requirements

* Python ≥ 3.11
* Redis running locally

Example Redis start via Docker:

```bash
docker run --name nexus-redis -p 6379:6379 redis:7-alpine
```

---

## 1) Clone repository

```bash
git clone <your-repository-url>
cd nexus_api
```

---

## 2) Create virtual environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3) Install dependencies

```bash
pip install --upgrade pip
pip install .
```

Dependencies are defined in:

```
pyproject.toml
```

---

## 4) Configure environment variables

Create `.env`:

```env
REDIS_HOST=localhost
REDIS_PORT=6379
APP_PORT=8000
```

---

## 5) Start API server

```bash
python -m uvicorn nexus_api:app --reload --port 8000
```

---

## 6) API should now be running

Open:

```
http://127.0.0.1:8000/
```

or

```
http://127.0.0.1:8000/redoc
```

---

# Example API request

Example using **curl**:

```bash
curl -X POST http://127.0.0.1:8000/run_nexus_endpoint \
  -H "Content-Type: application/json" \
  -d '{
    "nexus_mappings_json": "default",
    "mapping_profile": "person",
    "dict_identifiers": "{\"Wikidata\": \"Q9312\", \"GND\": \"118559796\", \"LCNAF\": \"n79021614\", \"VIAF\": \"82088490\"}",
    "add_identifiers": true,
    "flatten": false
  }'
```

---

# Example request bodies

### With identifiers from multiple sources

```json
{
  "nexus_mappings_json": "default",
  "mapping_profile": "person",
  "dict_identifiers": "{'Wikidata': 'Q9312', 'GND': '118559796', 'LCNAF': 'n79021614', 'VIAF': '82088490'}",
  "add_identifiers": true,
  "flatten": false
}
```

---

### With only Wikidata identifier

```json
{
  "nexus_mappings_json": "default",
  "mapping_profile": "person",
  "dict_identifiers": "{'Wikidata': 'Q9312'}",
  "add_identifiers": true,
  "flatten": false
}
```

If:

```
add_identifiers == true
```

additional identifiers are automatically fetched from:

* GND
* VIAF
* LCNAF

via Wikidata.

---

# Output variants

## Factlets (`flatten=false`)

Returns structured provenance-rich objects.

Example input:

```json
{
  "nexus_mappings_json": "default",
  "mapping_profile": "person",
  "dict_identifiers": "{'Wikidata':'Q9312'}",
  "add_identifiers": true,
  "flatten": false
}
```

Returns:

<details>
<summary>expand response</summary>

```
{
  "result": [
    {
      "name": "wikidata_id",
      "description": "...",
      "value": [
        "Q9312"
      ],
      "timestamp": 1757935746.5351136,
      "fuzzy_isA": [],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614"
      },
      "source_uri": "https://www.wikidata.org/wiki/Special:EntityData/Q9312.json",
      "source_name": "Wikidata",
      "source_property": "title",
      "source_date": "",
      "source_path": "$.entities.*.title"
    },
    {
      "name": "gnd_id",
      "description": "...",
      "value": [
        "118559796"
      ],
      "timestamp": 1757935746.551301,
      "fuzzy_isA": [],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614"
      },
      "source_uri": "https://www.wikidata.org/wiki/Special:EntityData/Q9312.json",
      "source_name": "Wikidata",
      "source_property": "P227",
      "source_date": "",
      "source_path": "$.entities.*.claims.P227.[0].mainsnak.datavalue.value"
    },
    {
      "name": "preferred_name",
      "description": "...",
      "value": [
        "Kant, Immanuel"
      ],
      "timestamp": 1757935746.5654197,
      "fuzzy_isA": [],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614"
      },
      "source_uri": "https://lobid.org/gnd/118559796.json",
      "source_name": "GND",
      "source_property": "preferredName",
      "source_date": "",
      "source_path": "$.preferredName"
    },
    {
      "name": "birth_date",
      "description": "...",
      "value": [
        "1724-04-22"
      ],
      "timestamp": 1757935746.5778215,
      "fuzzy_isA": [
        "https://www.cidoc-crm.org/cidoc-crm/E52_Time-Span",
        "https://schema.org/birthDate",
        "https://schema.org/Date"
      ],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614"
      },
      "source_uri": "https://lobid.org/gnd/118559796.json",
      "source_name": "GND",
      "source_property": "dateOfBirth",
      "source_date": "",
      "source_path": "$.dateOfBirth.[0]"
    },
    {
      "name": "birth_place",
      "description": "...",
      "value": [
        "Königsberg"
      ],
      "timestamp": 1757935746.5901995,
      "fuzzy_isA": [
        "https://schema.org/Place"
      ],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614"
      },
      "source_uri": "https://lobid.org/gnd/118559796.json",
      "source_name": "GND",
      "source_property": "placeOfBirth",
      "source_date": "",
      "source_path": "$.placeOfBirth.[0].label"
    },
    {
      "name": "death_date",
      "description": "...",
      "value": [
        "1804-02-12"
      ],
      "timestamp": 1757935746.6037624,
      "fuzzy_isA": [
        "https://www.cidoc-crm.org/cidoc-crm/E52_Time-Span",
        "https://schema.org/deathDate",
        "https://schema.org/Date"
      ],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614"
      },
      "source_uri": "https://lobid.org/gnd/118559796.json",
      "source_name": "GND",
      "source_property": "dateOfDeath",
      "source_date": "",
      "source_path": "$.dateOfDeath.[0]"
    },
    {
      "name": "death_place",
      "description": "...",
      "value": [
        "Königsberg"
      ],
      "timestamp": 1757935746.6215339,
      "fuzzy_isA": [
        "https://schema.org/Place"
      ],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614"
      },
      "source_uri": "https://lobid.org/gnd/118559796.json",
      "source_name": "GND",
      "source_property": "placeOfDeath",
      "source_date": "",
      "source_path": "$.placeOfDeath.[0].label"
    },
    {
      "name": "occupation",
      "description": "...",
      "value": [
        "Philosoph"
      ],
      "timestamp": 1757935746.638694,
      "fuzzy_isA": [
        "https://schema.org/Occupation"
      ],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614"
      },
      "source_uri": "https://lobid.org/gnd/118559796.json",
      "source_name": "GND",
      "source_property": "professionOrOccupation",
      "source_date": "",
      "source_path": "$.professionOrOccupation.[0].label"
    },
    {
      "name": "field_of_work",
      "description": "...",
      "value": [
        "Q9471",
        "Q35277",
        "Q9465"
      ],
      "timestamp": 1757935746.666455,
      "fuzzy_isA": [
        "..."
      ],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614"
      },
      "source_uri": "https://www.wikidata.org/wiki/Special:EntityData/Q9312.json",
      "source_name": "Wikidata",
      "source_property": "P101",
      "source_date": "",
      "source_path": "$.entities.*.claims.P101.[*].mainsnak.datavalue.value.id"
    },
    {
      "name": "movement",
      "description": "...",
      "value": [
        "Q679842",
        "Q12539"
      ],
      "timestamp": 1757935746.6809,
      "fuzzy_isA": [
        "..."
      ],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614"
      },
      "source_uri": "https://www.wikidata.org/wiki/Special:EntityData/Q9312.json",
      "source_name": "Wikidata",
      "source_property": "P135",
      "source_date": "",
      "source_path": "$.entities.*.claims.P135.[*].mainsnak.datavalue.value.id"
    }
  ]
}
```

</details>

---

## Flattened output (`flatten=true`)

Returns simplified key-value aggregation.

Example input:

```json
{
  "nexus_mappings_json": "default",
  "mapping_profile": "person",
  "dict_identifiers": "{'Wikidata':'Q9312'}",
  "add_identifiers": true,
  "flatten": true
}
```

Example output:

```json
{
  "result": {
    "wikidata_id": ["Q9312"],
    "gnd_id": ["118559796"],
    "preferred_name": ["Kant, Immanuel"],
    "birth_date": ["1724-04-22"],
    "birth_place": ["Königsberg"],
    "death_date": ["1804-02-12"],
    "death_place": ["Königsberg"],
    "occupation": ["Philosoph"],
    "field_of_work": ["Q9471", "Q35277", "Q9465"],
    "movement": ["Q679842", "Q12539"]
  }
}
```

---

# Environment variables

| Variable   | Purpose        |
| ---------- | -------------- |
| REDIS_HOST | Redis hostname |
| REDIS_PORT | Redis port     |
| APP_PORT   | API port       |

Docker default:

```
REDIS_HOST=redis
```

Local default:

```
REDIS_HOST=localhost
```

---

# Notes

## Redis requirement

Redis is required because the application caches HTTP requests.

Startup fails intentionally if Redis is unavailable:

```
Redis ping: True
```

must succeed.

---

## Reverse proxy setups

If running behind a proxy mounted at `/nexus`, keep:

```python
root_path="/nexus"
```

Otherwise remove it for local development simplicity.

---

# Development workflow summary

Run locally:

```
uvicorn nexus_api:app --reload
```

Run containerized:

```
docker compose up --build
```
