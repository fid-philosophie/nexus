# nexus

Python-based Linked Open Data aggregation service wrapped with **FastAPI**.
The service queries multiple authority sources (e.g. Wikidata, GND, VIAF, LCNAF), aggregates prioritized results, and returns structured **factlets** or flattened output.

Caching of incoming responses is handled via **Redis**.

---

## How to get started

### 1) Clone repository

```bash
git clone git@github.com:fid-philosophie/nexus.git
cd nexus
```

### 2) Copy/create .env from .env.example

#### MacOS / Linux

```bash
cp -n .env.example .env
```

#### Windows PowerShell

```bash
if (-Not (Test-Path .env)) {
    Copy-Item .env.example .env
}
```


### 3) Configure .env


- `ENABLE_CUSTOM_MAPPINGS=True` will enable directly posting custom JSON into the API, so make sure to have the API running in a safe environment - if you run a fork the safer way will be to simply add new mappings in the `mappings` folder

- Use Setup 1 if you already have a Redis instance running and you wnat to use taht, otherwise go with Setup 2

- 

### 4) Start the API

```bash
docker compose up --build
```


### 5) Test endpoint via curl


```bash
curl -X POST http://127.0.0.1:8000/v1/entity \
  -H "Content-Type: application/json" \
  -d '{
    "mapping_profile": "person",
    "dict_identifiers": {
      "Wikidata": "Q9312"
    },
    "add_identifiers": true,
    "flatten": false
  }'
```
- this will give you data aggregated via the `mappings/person.json` profile
- `"add_identifiers": true` adds identifiers for additional sources (e.g. GND) via Wikidata identifier properties

### 6) Or test via the OpenAPI docs interface

- open http://127.0.0.1:8000 via your browser


### 7) Stop the API

```bash
docker compose down
```


## Input: example request bodies

### With identifiers from multiple sources

```json
{
  "mapping_profile": "person",
  "dict_identifiers": {"Wikidata": "Q9312", "GND": "118559796", "LCNAF": "n79021614", "VIAF": "82088490"},
  "add_identifiers": false,
  "flatten": false
}
```

---

### With only a Wikidata identifier

```json
{
  "mapping_profile": "person",
  "dict_identifiers": {"Wikidata": "Q9312"},
  "add_identifiers": true,
  "flatten": false
}
```


## Output

### Flattened output (`flatten=true`)

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
    "wikidata_id": [
      "Q9312"
    ],
    "gnd_id": [
      "118559796"
    ],
    "preferred_name": [
      "Immanuel Kant"
    ],
    "birth_date": [
      "+1724-04-22T00:00:00Z"
    ],
    "birth_place": [
      "Q22071"
    ],
    "death_date": [
      "+1804-02-12T00:00:00Z"
    ],
    "death_place": [
      "Q22071"
    ],
    "occupation": [
      "Philosoph"
    ],
    "influenced_by": [
      "Q37160",
      "Q82049",
      "Q76510",
      "Q6527",
      "Q316367",
      "Q935",
      "Q859",
      "Q63081",
      "Q41568",
      "Q9191",
      "Q9047",
      "Q9353",
      "Q309818",
      "Q35802"
    ],
    "field_of_work": [
      "Q468127",
      "Q1878871",
      "Q1878870"
    ],
    "movement": [
      "Q679842",
      "Q12539"
    ],
    "SEP_ID": [
      "kant"
    ],
    "SEP_Preamble": "Immanuel Kant (1724–1804) is the central figure in modern philosophy. He synthesized early modern rationalism and empiricism, set the terms for much of nineteenth and twentieth century philosophy, and continues to exercise a significant influence today in metaphysics, epistemology, ethics, political philosophy, aesthetics, and other fields. The fundamental idea of Kant’s “critical philosophy” – especially in his three Critiques: the Critique of Pure Reason (1781, 1787), the Critique of Practical Reason (1788), and the Critique of the Power of Judgment (1790) – is human autonomy. He argues that the human understanding is the source of the general laws of nature that structure all our experience; and that human reason gives itself the moral law, which is our basis for belief in God, freedom, and immortality. Therefore, scientific knowledge, morality, and religious belief are mutually consistent and secure because they all rest on the same foundation of human autonomy, which is also the final end of nature according to the teleological worldview of reflecting judgment that Kant introduces to unify the theoretical and practical parts of his philosophical system."
  }
}
```

### Factlets output (`flatten=false`)

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

```json
{
  "result": [
    {
      "name": "wikidata_id",
      "description": "...",
      "value": [
        "Q9312"
      ],
      "timestamp": "2026-11-17T11:26:35.247+00:00",
      "fuzzy_isA": [],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614",
        "FactGrid": "Q14211",
        "SEP": "kant"
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
      "timestamp": "2026-11-17T11:26:35.247+00:00",
      "fuzzy_isA": [],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614",
        "FactGrid": "Q14211",
        "SEP": "kant"
      },
      "source_uri": "https://www.wikidata.org/wiki/Special:EntityData/Q9312.json",
      "source_name": "Wikidata",
      "source_property": "P227",
      "source_date": "",
      "source_path": "$.entities.*.claims.P227[0].mainsnak.datavalue.value"
    },
    {
      "name": "preferred_name",
      "description": "...",
      "value": [
        "Immanuel Kant"
      ],
      "timestamp": "2026-11-17T11:26:35.249+00:00",
      "fuzzy_isA": [],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614",
        "FactGrid": "Q14211",
        "SEP": "kant"
      },
      "source_uri": "https://database.factgrid.de/wiki/Special:EntityData/Q14211.json",
      "source_name": "FactGrid",
      "source_property": "labels.en",
      "source_date": "",
      "source_path": "$.entities.*.labels.en.value"
    },
    {
      "name": "birth_date",
      "description": "...",
      "value": [
        "+1724-04-22T00:00:00Z"
      ],
      "timestamp": "2026-11-17T11:26:35.251+00:00",
      "fuzzy_isA": [
        "https://www.cidoc-crm.org/cidoc-crm/E52_Time-Span",
        "https://schema.org/birthDate",
        "https://schema.org/Date"
      ],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614",
        "FactGrid": "Q14211",
        "SEP": "kant"
      },
      "source_uri": "https://database.factgrid.de/wiki/Special:EntityData/Q14211.json",
      "source_name": "FactGrid",
      "source_property": "P77",
      "source_date": "",
      "source_path": "$.entities.*.claims.P77[0].mainsnak.datavalue.value.time"
    },
    {
      "name": "birth_place",
      "description": "...",
      "value": [
        "Q22071"
      ],
      "timestamp": "2026-11-17T11:26:35.252+00:00",
      "fuzzy_isA": [
        "https://schema.org/Place"
      ],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614",
        "FactGrid": "Q14211",
        "SEP": "kant"
      },
      "source_uri": "https://database.factgrid.de/wiki/Special:EntityData/Q14211.json",
      "source_name": "FactGrid",
      "source_property": "P82",
      "source_date": "",
      "source_path": "$.entities.*.claims.P82[0].mainsnak.datavalue.value.id"
    },
    {
      "name": "death_date",
      "description": "...",
      "value": [
        "+1804-02-12T00:00:00Z"
      ],
      "timestamp": "2026-11-17T11:26:35.252+00:00",
      "fuzzy_isA": [
        "https://www.cidoc-crm.org/cidoc-crm/E52_Time-Span",
        "https://schema.org/deathDate",
        "https://schema.org/Date"
      ],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614",
        "FactGrid": "Q14211",
        "SEP": "kant"
      },
      "source_uri": "https://database.factgrid.de/wiki/Special:EntityData/Q14211.json",
      "source_name": "FactGrid",
      "source_property": "P38",
      "source_date": "",
      "source_path": "$.entities.*.claims.P38[0].mainsnak.datavalue.value.time"
    },
    {
      "name": "death_place",
      "description": "...",
      "value": [
        "Q22071"
      ],
      "timestamp": "2026-11-17T11:26:35.253+00:00",
      "fuzzy_isA": [
        "https://schema.org/Place"
      ],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614",
        "FactGrid": "Q14211",
        "SEP": "kant"
      },
      "source_uri": "https://database.factgrid.de/wiki/Special:EntityData/Q14211.json",
      "source_name": "FactGrid",
      "source_property": "P168",
      "source_date": "",
      "source_path": "$.entities.*.claims.P168[0].mainsnak.datavalue.value.id"
    },
    {
      "name": "occupation",
      "description": "...",
      "value": [
        "Philosoph"
      ],
      "timestamp": "2026-11-17T11:26:35.254+00:00",
      "fuzzy_isA": [
        "https://schema.org/Occupation"
      ],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614",
        "FactGrid": "Q14211",
        "SEP": "kant"
      },
      "source_uri": "https://lobid.org/gnd/118559796.json",
      "source_name": "GND",
      "source_property": "professionOrOccupation",
      "source_date": "",
      "source_path": "$.professionOrOccupation[0].label"
    },
    {
      "name": "influenced_by",
      "description": "...",
      "value": [
        "Q37160",
        "Q82049",
        "Q76510",
        "Q6527",
        "Q316367",
        "Q935",
        "Q859",
        "Q63081",
        "Q41568",
        "Q9191",
        "Q9047",
        "Q9353",
        "Q309818",
        "Q35802"
      ],
      "timestamp": "2026-11-17T11:26:35.255+00:00",
      "fuzzy_isA": [
        "..."
      ],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614",
        "FactGrid": "Q14211",
        "SEP": "kant"
      },
      "source_uri": "https://www.wikidata.org/wiki/Special:EntityData/Q9312.json",
      "source_name": "Wikidata",
      "source_property": "P737",
      "source_date": "",
      "source_path": "$.entities.*.claims.P737.*.mainsnak.datavalue.value.id"
    },
    {
      "name": "field_of_work",
      "description": "...",
      "value": [
        "Q468127",
        "Q1878871",
        "Q1878870"
      ],
      "timestamp": "2026-11-17T11:26:35.255+00:00",
      "fuzzy_isA": [
        "..."
      ],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614",
        "FactGrid": "Q14211",
        "SEP": "kant"
      },
      "source_uri": "https://database.factgrid.de/wiki/Special:EntityData/Q14211.json",
      "source_name": "FactGrid",
      "source_property": "P452",
      "source_date": "",
      "source_path": "$.entities.*.claims.P452[*].mainsnak.datavalue.value.id"
    },
    {
      "name": "movement",
      "description": "...",
      "value": [
        "Q679842",
        "Q12539"
      ],
      "timestamp": "2026-11-17T11:26:35.256+00:00",
      "fuzzy_isA": [
        "..."
      ],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614",
        "FactGrid": "Q14211",
        "SEP": "kant"
      },
      "source_uri": "https://www.wikidata.org/wiki/Special:EntityData/Q9312.json",
      "source_name": "Wikidata",
      "source_property": "P135",
      "source_date": "",
      "source_path": "$.entities.*.claims.P135[*].mainsnak.datavalue.value.id"
    },
    {
      "name": "SEP_ID",
      "description": "...",
      "value": [
        "kant"
      ],
      "timestamp": "2026-11-17T11:26:35.260+00:00",
      "fuzzy_isA": [
        ""
      ],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614",
        "FactGrid": "Q14211",
        "SEP": "kant"
      },
      "source_uri": "https://www.wikidata.org/wiki/Special:EntityData/Q9312.json",
      "source_name": "Wikidata",
      "source_property": "P3123",
      "source_date": "",
      "source_path": "$.entities.*.claims.P3123[0].mainsnak.datavalue.value"
    },
    {
      "name": "SEP_Preamble",
      "description": "...",
      "value": "Immanuel Kant (1724–1804) is the central figure in modern philosophy. He synthesized early modern rationalism and empiricism, set the terms for much of nineteenth and twentieth century philosophy, and continues to exercise a significant influence today in metaphysics, epistemology, ethics, political philosophy, aesthetics, and other fields. The fundamental idea of Kant’s “critical philosophy” – especially in his three Critiques: the Critique of Pure Reason (1781, 1787), the Critique of Practical Reason (1788), and the Critique of the Power of Judgment (1790) – is human autonomy. He argues that the human understanding is the source of the general laws of nature that structure all our experience; and that human reason gives itself the moral law, which is our basis for belief in God, freedom, and immortality. Therefore, scientific knowledge, morality, and religious belief are mutually consistent and secure because they all rest on the same foundation of human autonomy, which is also the final end of nature according to the teleological worldview of reflecting judgment that Kant introduces to unify the theoretical and practical parts of his philosophical system.",
      "timestamp": "2026-11-17T11:26:35.262+00:00",
      "fuzzy_isA": [
        ""
      ],
      "subject": {
        "Wikidata": "Q9312",
        "GND": "118559796",
        "VIAF": "82088490",
        "LCNAF": "n79021614",
        "FactGrid": "Q14211",
        "SEP": "kant"
      },
      "source_uri": "https://plato.stanford.edu/entries/kant",
      "source_name": "SEP",
      "source_property": "preamble",
      "source_date": "",
      "source_path": "normalize-space(string(//*[@id='preamble']))"
    }
  ]
}
```

</details>