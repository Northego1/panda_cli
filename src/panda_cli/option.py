import types
import typing as t

import click
from pydantic import Field
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from panda_cli.parameters import DictParamType


_CLICK_META_KEY: t.Final[str] = "__click_meta__"


class OptionMeta(t.TypedDict, total=False):
    param_decls: t.Sequence[str] | None
    show_default: bool | str | None
    prompt: bool | str
    confirmation_prompt: bool | str
    prompt_required: bool
    hide_input: bool
    is_flag: bool | None
    flag_value: t.Any
    multiple: bool
    count: bool
    allow_from_autoenv: bool
    type: click.ParamType | t.Any | None
    help: str | None
    hidden: bool
    show_choices: bool
    show_envvar: bool
    deprecated: bool | str


def Option(
    *flags: str,
    default: t.Any = PydanticUndefined,
    description: str | None = None,
    show_default: bool | str | None = None,
    prompt: bool | str = False,
    confirmation_prompt: bool | str = False,
    prompt_required: bool = True,
    hide_input: bool = False,
    multiple: bool = False,
    flag_value: t.Any | None = None,
    count: bool = False,
    allow_from_autoenv: bool = True,
    type: click.ParamType | t.Any | None = None,
    help: str | None = None,
    hidden: bool = False,
    show_choices: bool = True,
    show_envvar: bool = False,
    deprecated: bool | str = False,
    **field_kwargs: t.Any,
) -> t.Any:
    meta = OptionMeta(
        param_decls=flags,
        show_default=show_default,
        prompt=prompt,
        confirmation_prompt=confirmation_prompt,
        prompt_required=prompt_required,
        hide_input=hide_input,
        multiple=multiple,
        count=count,
        allow_from_autoenv=allow_from_autoenv,
        type=type,
        help=help,
        flag_value=flag_value,
        hidden=hidden,
        show_choices=show_choices,
        show_envvar=show_envvar,
        deprecated=deprecated,
    )

    kw: dict[str, t.Any] = dict(description=description, **field_kwargs)
    if default is not PydanticUndefined:
        kw["default"] = default

    field = Field(**kw)
    object.__setattr__(field, "metadata", [*field.metadata, {_CLICK_META_KEY: meta}])
    return field


def get_field_option_meta(field: FieldInfo) -> OptionMeta:
    for item in field.metadata:
        if isinstance(item, dict) and _CLICK_META_KEY in item:
            return item[_CLICK_META_KEY]  # pyright: ignore[reportUnknownVariableType]
    return OptionMeta()


_TYPE_MAP_CLICK: t.Final[dict[t.Any, t.Any]] = {
    str: click.STRING,
    int: click.INT,
    float: click.FLOAT,
    bool: click.BOOL,
    bytes: click.STRING,
}


def resolve_click_type(annotation: t.Any) -> click.ParamType:
    origin = t.get_origin(annotation)

    if origin in (t.Union, types.UnionType):
        args = [a for a in t.get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            return resolve_click_type(args[0])

    if origin is t.Literal:
        return click.Choice([str(c) for c in t.get_args(annotation)])

    if origin in (list, tuple, set, frozenset):
        inner = t.get_args(annotation)  # type: ignore
        return resolve_click_type(inner[0]) if inner else click.STRING

    if origin is dict:
        d_args = t.get_args(annotation)
        key_t = _TYPE_MAP_CLICK.get(d_args[0], click.STRING) if d_args else click.STRING
        val_t = (
            _TYPE_MAP_CLICK.get(d_args[1], click.STRING)
            if len(d_args) > 1
            else click.STRING
        )
        return DictParamType(key_t, val_t)

    return _TYPE_MAP_CLICK.get(annotation, click.STRING)


def is_multiple(annotation: t.Any) -> bool:
    origin = t.get_origin(annotation)
    if origin in (t.Union, types.UnionType):
        args = [a for a in t.get_args(annotation) if a is not type(None)]
        return is_multiple(args[0]) if len(args) == 1 else False
    return origin in (list, tuple, set, frozenset, dict)


def is_bool_flag(annotation: t.Any) -> bool:
    origin = t.get_origin(annotation)
    if origin in (t.Union, types.UnionType):
        args = [a for a in t.get_args(annotation) if a is not type(None)]
        return is_bool_flag(args[0]) if len(args) == 1 else False
    return annotation is bool


def get_metavar(annotation: t.Any) -> str | None:
    origin = t.get_origin(annotation)

    # Unwrap Optional[X] / X | None
    if origin in (t.Union, types.UnionType):
        u_args = [a for a in t.get_args(annotation) if a is not type(None)]
        if len(u_args) == 1:
            return get_metavar(u_args[0])
        parts = [_TYPE_MAP_CLICK.get(a, click.STRING).name.upper() for a in u_args]
        return " | ".join(parts) if parts else None

    # dict[K, V] → KEY=VALUE
    if origin is dict:
        d_args = t.get_args(annotation)
        k = (
            _TYPE_MAP_CLICK.get(d_args[0], click.STRING).name.upper()
            if d_args
            else "KEY"
        )
        v = (
            _TYPE_MAP_CLICK.get(d_args[1], click.STRING).name.upper()
            if len(d_args) > 1
            else "VALUE"
        )
        return f"{k}={v}"

    # list[X] / set[X] → TYPE...
    if origin in (list, set, frozenset):
        it_args = t.get_args(annotation)
        inner = (
            _TYPE_MAP_CLICK.get(it_args[0], click.STRING).name.upper()
            if it_args
            else "TEXT"
        )
        return f"Iterable {inner}..."

    return None
