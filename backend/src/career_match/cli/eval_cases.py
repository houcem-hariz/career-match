"""Compare gold buckets to score_offer. No live LLM, no Postgres."""

from __future__ import annotations

import typer

from career_match.eval.annotated import evaluate_cases

app = typer.Typer(add_completion=False)


@app.command()
def main() -> None:
    results = evaluate_cases()
    failed = 0
    for item in results:
        mark = "ok" if item.ok else "FAIL"
        if not item.ok:
            failed += 1
        typer.echo(
            f"{mark:4} {item.case.case_id:36} "
            f"expected={item.case.expected_bucket.value:13} "
            f"got={item.predicted.value:13} "
            f"gaps={item.mandatory_gap_count} sen={item.seniority_gap:+d}  {item.title}"
        )
    typer.echo(f"{len(results)} cases, {len(results) - failed} ok, {failed} fail", err=True)
    if failed:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
