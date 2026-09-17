"""Shared model-level validators.

JSONFields accept anything that parses as JSON, so without these an editor can
persist a value the templates cannot iterate — which surfaces as a 500 on a
public page rather than a form error in the admin.
"""
from django.core.exceptions import ValidationError

MAX_ENTRIES = 50
MAX_ENTRY_LENGTH = 300


def validate_string_list(value):
    """Require a modestly-sized list of plain strings."""
    if not isinstance(value, list):
        raise ValidationError("Enter a JSON list, for example [\"First\", \"Second\"].")
    if len(value) > MAX_ENTRIES:
        raise ValidationError(f"At most {MAX_ENTRIES} entries (got {len(value)}).")
    for index, entry in enumerate(value, start=1):
        if not isinstance(entry, str):
            raise ValidationError(f"Entry {index} must be text, not {type(entry).__name__}.")
        if len(entry) > MAX_ENTRY_LENGTH:
            raise ValidationError(
                f"Entry {index} is {len(entry)} characters; the maximum is {MAX_ENTRY_LENGTH}."
            )
