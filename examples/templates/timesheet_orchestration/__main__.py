"""
CLI entry point for Timesheet Orchestration Agent.

Uses AgentRuntime for session management and TUI interaction.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

import click

from .agent import default_agent, TimesheetOrchestrationAgent


def setup_logging(verbose=False, debug=False):
    """Configure logging for execution visibility."""
    if debug:
        level, fmt = logging.DEBUG, "%(asctime)s %(name)s: %(message)s"
    elif verbose:
        level, fmt = logging.INFO, "%(message)s"
    else:
        level, fmt = logging.WARNING, "%(levelname)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, stream=sys.stderr)
    logging.getLogger("framework").setLevel(level)


def _load_local_env_if_present(env_file: str = ".env") -> None:
    """Load KEY=VALUE pairs from .env files into os.environ.

    Loads from the agent package directory first (highest priority), then CWD.
    Existing environment variables are not overwritten (setdefault).
    """
    candidates = [
        Path(__file__).parent / env_file,
        Path(env_file),
    ]
    for path in candidates:
        if not path.exists() or not path.is_file():
            continue
        try:
            for raw_line in path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line[len("export ") :].strip()
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if not key:
                    continue
                if len(value) >= 2 and (
                    (value.startswith('"') and value.endswith('"'))
                    or (value.startswith("'") and value.endswith("'"))
                ):
                    value = value[1:-1]
                os.environ.setdefault(key, value)
        except Exception as e:
            logging.getLogger(__name__).warning("Failed to load %s: %s", path, e)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Timesheet Orchestration Agent — autonomous weekly timesheet collection."""
    pass


@cli.command()
@click.option("--mock", is_flag=True, help="Run in mock mode")
@click.option("--quiet", "-q", is_flag=True, help="Only output result JSON")
@click.option("--verbose", "-v", is_flag=True, help="Show execution details")
@click.option("--debug", is_flag=True, help="Show debug logging")
def run(mock, quiet, verbose, debug):
    """Execute the full timesheet workflow (intake → report)."""
    _load_local_env_if_present()
    if not quiet:
        setup_logging(verbose=verbose, debug=debug)

    result = asyncio.run(default_agent.run({}, mock_mode=mock))

    output_data = {
        "success": result.success,
        "steps_executed": result.steps_executed,
        "output": result.output,
    }
    if result.error:
        output_data["error"] = result.error

    click.echo(json.dumps(output_data, indent=2, default=str))
    sys.exit(0 if result.success else 1)


@cli.command()
@click.option("--mock", is_flag=True, help="Run in mock mode")
@click.option("--verbose", "-v", is_flag=True, help="Show execution details")
@click.option("--debug", is_flag=True, help="Show debug logging")
def tui(mock, verbose, debug):
    """Launch the legacy TUI dashboard (deprecated; prefer `hive open`)."""
    _load_local_env_if_present()
    setup_logging(verbose=verbose, debug=debug)

    try:
        from framework.tui.app import AdenTUI
    except ImportError:
        click.echo(
            "TUI requires 'textual'. Install with: pip install textual"
        )
        sys.exit(1)

    from framework.llm import LiteLLMProvider
    from framework.runner.tool_registry import ToolRegistry
    from framework.runtime.agent_runtime import create_agent_runtime
    from framework.runtime.event_bus import EventBus
    from framework.runtime.execution_stream import EntryPointSpec

    async def run_with_tui():
        agent = TimesheetOrchestrationAgent()
        agent._event_bus = EventBus()
        agent._tool_registry = ToolRegistry()

        storage_path = Path.home() / ".hive" / "agents" / "timesheet_orchestration"
        storage_path.mkdir(parents=True, exist_ok=True)

        mcp_config_path = Path(__file__).parent / "mcp_servers.json"
        if mcp_config_path.exists():
            agent._tool_registry.load_mcp_config(mcp_config_path)

        llm = None
        if not mock:
            llm = LiteLLMProvider(
                model=agent.config.model,
                api_key=agent.config.api_key,
                api_base=agent.config.api_base,
            )

        tools = list(agent._tool_registry.get_tools().values())
        tool_executor = agent._tool_registry.get_executor()
        graph = agent._build_graph()

        runtime = create_agent_runtime(
            graph=graph,
            goal=agent.goal,
            storage_path=storage_path,
            entry_points=[
                EntryPointSpec(
                    id="start",
                    name="Full Setup & Run",
                    entry_node="intake",
                    trigger_type="manual",
                    isolation_level="isolated",
                ),
                EntryPointSpec(
                    id="weekly",
                    name="Weekly Trigger",
                    entry_node="dispatch-reminders",
                    trigger_type="cron",
                    isolation_level="shared",
                ),
            ],
            llm=llm,
            tools=tools,
            tool_executor=tool_executor,
        )

        await runtime.start()

        try:
            app = AdenTUI(runtime)
            await app.run_async()
        finally:
            await runtime.stop()

    asyncio.run(run_with_tui())


@cli.command()
@click.option("--json", "output_json", is_flag=True)
def info(output_json):
    """Show agent information."""
    data = {
        "name": "Timesheet Orchestration Agent",
        "version": "1.0.0",
        "nodes": [n.id for n in default_agent.nodes],
        "edges": [e.id for e in default_agent.edges],
        "client_facing_nodes": [
            n.id for n in default_agent.nodes if n.client_facing
        ],
        "entry_points": default_agent.entry_points,
        "terminal_nodes": default_agent.terminal_nodes,
        "feedback_loops": [
            "e4: validate → collect (clarification)",
            "e5: validate → dispatch (missing submissions)",
        ],
    }
    if output_json:
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Agent: {data['name']} v{data['version']}")
        click.echo(f"Nodes: {', '.join(data['nodes'])}")
        click.echo(f"HIL Points: {', '.join(data['client_facing_nodes'])}")
        click.echo(f"Feedback Loops: {len(data['feedback_loops'])}")
        for loop in data["feedback_loops"]:
            click.echo(f"  - {loop}")


@cli.command()
def validate():
    """Validate agent structure."""
    result = default_agent.validate()
    if result["valid"]:
        click.echo("Agent structure is valid.")
        for w in result.get("warnings", []):
            click.echo(f"  WARNING: {w}")
    else:
        click.echo("Agent has errors:")
        for e in result["errors"]:
            click.echo(f"  ERROR: {e}")
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    cli()
