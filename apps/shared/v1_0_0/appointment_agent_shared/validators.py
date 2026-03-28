from datetime import datetime


def require_non_empty(value: str, field_name: str) -> None:
    if not value or not str(value).strip():
        raise ValueError("{} must not be empty".format(field_name))


def validate_iso_datetime(value: str, field_name: str) -> None:
    require_non_empty(value, field_name)
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception as exc:
        raise ValueError("{} must be ISO-8601 compatible".format(field_name)) from exc
