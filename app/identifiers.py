import re


IDENTIFIER_PATTERNS = {
    "Wikidata": r"Q[1-9][0-9]*",

    "GND": (
        r"1[01234]?\d{7}[0-9X]"
        r"|[47]\d{6}-\d"
        r"|[1-9]\d{0,7}-[0-9X]"
        r"|3\d{7}[0-9X]"
    ),

    "VIAF": r"^[1-9](\d{1,8}|\d{18,21})$",

    "LCNAF": (
        r"(?:n|nb|nr|no|ns)"
        r"(?:[4-9][0-9]|00|01|20[0-2][0-9])"
        r"[0-9]{6}"
    ),

    "FactGrid": r"Q[1-9][0-9]*",

    "SEP": r"[0-9A-Za-z\-]+",
}


def validate_identifier(source_name: str, identifier: str) -> None:
    """Raise ValueError if the source or identifier format is invalid."""

    pattern = IDENTIFIER_PATTERNS.get(source_name)

    if pattern is None:
        raise ValueError(
            f"Unsupported identifier source: {source_name!r}"
        )

    if not isinstance(identifier, str):
        raise ValueError(
            f"Identifier for {source_name} must be a string"
        )

    if re.fullmatch(pattern, identifier, flags=re.ASCII) is None:
        raise ValueError(
            f"Invalid identifier format for {source_name}"
        )