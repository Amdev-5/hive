"""
CLI entry point for Blog Writer Agent.

Uses AgentRuntime for multi-entrypoint support with HITL pause/resume.
"""

import asyncio
import json
import logging
import sys
import click

from .agent import default_agent, BlogWriterAgent


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


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Blog Writer Agent - Business blog pipeline with HITL checkpoints."""
    pass


@cli.command()
@click.option("--topic", "-t", type=str, required=True, help="Blog topic")
@click.option("--quiet", "-q", is_flag=True, help="Only output result JSON")
@click.option("--verbose", "-v", is_flag=True, help="Show execution details")
@click.option("--debug", is_flag=True, help="Show debug logging")
def run(topic, quiet, verbose, debug):
    """Execute blog writing on a topic."""
    if not quiet:
        setup_logging(verbose=verbose, debug=debug)

    context = {"topic": topic}

    result = asyncio.run(default_agent.run(context))

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
@click.option("--verbose", "-v", is_flag=True, help="Show execution details")
@click.option("--debug", is_flag=True, help="Show debug logging")
def tui(verbose, debug):
    """Launch the TUI dashboard for interactive writing."""
    setup_logging(verbose=verbose, debug=debug)

    try:
        from framework.tui.app import AdenTUI
    except ImportError:
        click.echo(
            "TUI requires the 'textual' package. Install with: pip install textual"
        )
        sys.exit(1)

    from pathlib import Path

    from framework.llm import LiteLLMProvider
    from framework.runner.tool_registry import ToolRegistry
    from framework.runtime.agent_runtime import create_agent_runtime
    from framework.runtime.execution_stream import EntryPointSpec

    async def run_with_tui():
        agent = BlogWriterAgent()

        # Build graph and tools
        agent._tool_registry = ToolRegistry()

        storage_path = Path.home() / ".hive" / "agents" / "blog_writer_agent"
        storage_path.mkdir(parents=True, exist_ok=True)

        mcp_config_path = Path(__file__).parent / "mcp_servers.json"
        if mcp_config_path.exists():
            agent._tool_registry.load_mcp_config(mcp_config_path)

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
                    name="Start Blog Writer",
                    entry_node="intake",
                    trigger_type="manual",
                    isolation_level="isolated",
                ),
            ],
            tools=tools,
            tool_executor=tool_executor,
            llm=llm,
        )

        await runtime.start()

        try:
            tui_app = AdenTUI(runtime=runtime)
            await tui_app.run_async()
        finally:
            await runtime.stop()

    asyncio.run(run_with_tui())


if __name__ == "__main__":
    cli()
