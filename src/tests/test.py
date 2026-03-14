from panda_cli import BaseCommand, Option, BaseGroup



class WebCli(BaseCommand):
    __cli_name__ = "web"

    host: str = Option(
        "--host",
        default="127.0.0.1",
        description="Host to listen on",
    )

    port: int = Option(
        "--port",
        default=8000,
    )

    value: dict[str, str]

    def __call__(self) -> None:
        print(f"Host: {self.host}")
        print(f"Port: {self.port}")
        print(f"Value: {self.value}")

class MainCli(BaseGroup):
    __cli_name__ = "main"


    web: WebCli


def main():
    cli = MainCli.run()


if __name__ == "__main__":
    main()
