import typing as t
from pydantic import BaseModel, ConfigDict
import click
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from panda_cli.option import (
    get_field_option_meta,
    get_metavar,
    is_bool_flag,
    is_multiple,
    resolve_click_type,
)


class Config(BaseModel):
    fields_name_to_flag: bool = True


class Base(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    __cli_name__: t.ClassVar[str | None] = None
    config: t.ClassVar[Config] = Config()

    @classmethod
    def _cli_name(cls, field_name: str | None = None) -> str:
        return cls.__cli_name__ or field_name or cls.__name__.lower()

    @classmethod
    def run(cls, *args: t.Any) -> None:
        """Run CLI."""
        raise NotImplementedError

    def __call__(self) -> None:
        """Command entry point."""
        raise NotImplementedError

    @classmethod
    def _field_to_option(
        cls,
        field_name: str,
        field: FieldInfo,
        annotation: t.Any,
    ) -> click.Option:
        meta = get_field_option_meta(field)

        flags = list(meta.get("param_decls", None) or ())
        field_get_flag = f"--{field_name.replace('_', '-')}"
        if cls.config.fields_name_to_flag and field_get_flag not in flags:
            flags.append(field_get_flag)

        has_default = field.default is not PydanticUndefined
        default = (
            field.default
            if has_default
            else (field.default_factory() if field.default_factory else None)  # type: ignore
        )
        required = not has_default and field.default_factory is None  # type: ignore

        multiple = meta.get("multiple", is_multiple(annotation))
        is_flag = meta.get("is_flag", is_bool_flag(annotation) and not multiple)
        click_type = resolve_click_type(annotation)

        return click.Option(
            param_decls=flags,
            type=None if is_flag else click_type,
            default=default,
            required=required,
            multiple=multiple,
            is_flag=is_flag,
            **(
                {"flag_value": meta["flag_value"]}
                if meta.get("flag_value") is not None
                else {}
            ),  # pyright: ignore[reportTypedDictNotRequiredAccess]
            help=field.description,
            show_default=meta.get("show_default", has_default),
            prompt=meta.get("prompt", False),
            confirmation_prompt=meta.get("confirmation_prompt", False),
            prompt_required=meta.get("prompt_required", True),
            hide_input=meta.get("hide_input", False),
            count=meta.get("count", False),
            allow_from_autoenv=meta.get("allow_from_autoenv", True),
            hidden=meta.get("hidden", False),
            show_choices=meta.get("show_choices", True),
            show_envvar=meta.get("show_envvar", False),
            deprecated=meta.get("deprecated", False),
            metavar=get_metavar(annotation),
        )

    @classmethod
    def _parse_and_build_params(cls) -> list[click.Option]:
        hints = t.get_type_hints(cls)
        params: list[click.Option] = []
        for name, field in cls.model_fields.items():
            ann = hints.get(name, field.annotation)
            if isinstance(ann, type) and issubclass(ann, cls):
                continue
            params.append(cls._field_to_option(name, field, ann))
        return params


class BaseCommand(Base):
    @classmethod
    def run(cls, *args: t.Any) -> None:
        cls._build_command()(standalone_mode=True, *args)

    @classmethod
    def _build_command(cls, _field_name: str | None = None) -> click.Command:
        hints = t.get_type_hints(cls)

        def _callback(**kwargs: t.Any) -> t.Any:
            cleaned = {
                k: v
                for k, v in kwargs.items()
                if v is not None or cls.model_fields[k].default is not PydanticUndefined
            }
            converted: dict[str, t.Any] = {}
            for k, v in cleaned.items():
                ann = hints.get(k)
                if t.get_origin(ann) is dict and isinstance(v, tuple):
                    converted[k] = dict(v)
                else:
                    converted[k] = v

            instance = cls(**converted)
            return instance()

        return click.Command(
            name=cls._cli_name(_field_name),
            params=cls._parse_and_build_params(),  # type: ignore
            callback=_callback,
            help=cls.__doc__,
        )


class BaseGroup(Base):
    @classmethod
    def run(cls, *args: t.Any) -> None:
        cls._build_group()(standalone_mode=True, *args)

    @classmethod
    def _build_group(cls, _field_name: str | None = None) -> click.Group:
        hints = t.get_type_hints(cls)

        group_params: list[click.Option] = []
        subcommands: list[click.Command] = []
        option_fields: set[str] = set()

        for field_name, field in cls.model_fields.items():
            ann = hints.get(field_name, field.annotation)

            if isinstance(ann, type) and issubclass(ann, BaseGroup):
                subcommands.append(ann._build_group(field_name))

            elif isinstance(ann, type) and issubclass(ann, BaseCommand):
                subcommands.append(ann._build_command(field_name))  # pyright: ignore[reportPrivateUsage]

            else:
                group_params.append(cls._field_to_option(field_name, field, ann))

        def _callback(**kwargs: t.Any) -> t.Any:
            filtered = {k: v for k, v in kwargs.items() if k in option_fields}
            if not filtered:
                return
            converted: dict[str, t.Any] = {}
            for k, v in filtered.items():
                ann = hints.get(k)
                if t.get_origin(ann) is dict and isinstance(v, tuple):
                    converted[k] = dict(v)
                else:
                    converted[k] = v
            return cls(**converted)()

        group = click.Group(
            name=cls._cli_name(_field_name),
            params=group_params,
            callback=_callback,
            invoke_without_command=True,
            help=cls.__doc__,
        )
        for cmd in subcommands:
            group.add_command(cmd)

        return group
