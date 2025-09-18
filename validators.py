import re


def digits_only(value: str) -> str:
    if not value:
        return value
    return re.sub(r"[^0-9]", "", value)


