from pydantic import TypeAdapter


Identifiers = dict[str, str]
_identifier_adapter = TypeAdapter(Identifiers)


def parse_identifiers_json(value: str) -> Identifiers:
    identifiers = _identifier_adapter.validate_json(value)

    if not identifiers:
        raise ValueError("At least one identifier is required")

    return identifiers