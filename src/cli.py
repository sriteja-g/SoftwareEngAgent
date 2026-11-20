import json
import click

from src.orchestration.orchestrator import SoftwareEngineeringAgent


@click.group()
def cli():
    """Autonomous Software Engineering Agent."""


@cli.command()
@click.argument("file_path")
def analyze(file_path):
    click.echo(json.dumps(SoftwareEngineeringAgent().process_request(f"Analyze {file_path}", file_path), indent=2))


@cli.command()
@click.argument("file_path")
@click.option("--description", "-d", default="Fix all issues")
def fix(file_path, description):
    result = SoftwareEngineeringAgent().process_request(f"Fix issues: {description}", file_path)
    final = result["results"][-1]
    click.echo("Fix generated successfully" if final.get("success") else "Fix failed")
    click.echo(final.get("diff", final.get("error", "")))


@cli.command()
@click.argument("file_path")
def test(file_path):
    result = SoftwareEngineeringAgent().process_request(f"Generate tests for {file_path}", file_path)
    click.echo(f"Generated {result['results'][0]['tests_generated']} test run(s)")


if __name__ == "__main__":
    cli()
