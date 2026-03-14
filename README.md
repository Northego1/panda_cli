# panda-cli

A lightweight declarative CLI framework built on top of Click and Pydantic.

Define commands as Python classes, describe arguments with type hints,
and build CLI trees using simple class composition.

---

## Features

- Declarative CLI commands
- Type-safe arguments
- Automatic CLI tree generation
- Built-in validation via Pydantic
- Minimal boilerplate
- Nested command groups

---

## Installation

```bash
pip install panda-cli
```


## Quick Example
```python
from panda_cli import BaseCommand, Option, BaseGroup
from panda_cli import Config


class WebCli(BaseCommand): 
    """ Web server """ # automaticly add to web --help
    __cli_name__ = "web"

    config=Config(fields_name_to_flag=True)  # if True auto gen flag by field name host -> --host

    host: str = Option(
        "--host",
        default="127.0.0.1",
        description="Host to listen on",
    )

    port: int = Option(
        "--port",
        default=8000,
    )

    methods: list[str] # --methods GET --methods POST -> ['GET', 'POST']

    map: dict[str, str] # --map key=value --map key2=value2 -> {'key': 'value', 'key2': 'value2'}

    def __exec__(self) -> None:
        """ Automaticly runs when command is called """
    
        print(f"Host: {self.host}")
        print(f"Port: {self.port}")
        print(f"Methods: {self.methods}")
        print(f"Map: {self.map}")


class MainCli(BaseGroup):
    __cli_name__ = "main"


    web: WebCli


def main():
    MainCli.run()


if __name__ == "__main__":
    main()
```


## CLI
```bash
uv run -m src --help

        Options:
        --help  Show this message and exit.

        Commands:
        web  Web server
```

```bash
uv run tests/test.py web --help

        Web server

        Options:
        --host TEXT                 Host to listen on
        --port INTEGER
        --methods Iterable TEXT...  [required]
        --map TEXT=TEXT             [required]
        --help                      Show this message and exit.
```
