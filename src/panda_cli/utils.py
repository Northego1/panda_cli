import typing as t


def is_dictable_tuple(obj: t.Any) -> bool:
    if not isinstance(obj, tuple):
        return False
    try:
        dict(obj)
        return True
    except (TypeError, ValueError):
        return False