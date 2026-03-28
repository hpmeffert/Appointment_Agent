from uuid import uuid4


def new_id(prefix: str) -> str:
    cleaned_prefix = prefix.strip().replace(" ", "_")
    return "{}_{}".format(cleaned_prefix, uuid4().hex[:16])
