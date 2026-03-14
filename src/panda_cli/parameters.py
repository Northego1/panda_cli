import click
import typing as t


class DictParamType(click.ParamType):
    name = "KEY=VALUE"

    def __init__(self, key_type: click.ParamType, val_type: click.ParamType) -> None:
        self.key_type = key_type
        self.val_type = val_type

    def convert(
        self,
        value: t.Any,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> tuple[t.Any, t.Any]:
        if isinstance(value, tuple):
            return value
        if "=" not in value:
            self.fail(f"Expected KEY=VALUE, got {value!r}", param, ctx)
        key, _, val = value.partition("=")
        return (
            self.key_type.convert(key.strip(), param, ctx),
            self.val_type.convert(val.strip(), param, ctx),
        )
