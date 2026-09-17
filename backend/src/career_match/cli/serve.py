"""HTTP API for the matching pipeline. Same cards as run_pipeline."""

from __future__ import annotations

import typer
import uvicorn

from career_match.api.app import create_live_app

app = typer.Typer(add_completion=False)


@app.command()
def main(
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8000, min=1, max=65535),
) -> None:
    try:
        api = create_live_app()
    except Exception as exc:
        typer.echo(
            "Postgres is unreachable. From the project root run: docker compose up -d",
            err=True,
        )
        typer.echo(f"({exc.__class__.__name__})", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"# career-match API on http://{host}:{port}", err=True)
    uvicorn.run(api, host=host, port=port, log_level="info")


if __name__ == "__main__":
    app()
