"""
Timesheet Orchestration Agent - Autonomous weekly timesheet collection & reporting.

Collects timesheets from team members via Slack, sends reminders via Telegram,
validates data, generates executive reports with charts, and delivers via Email.
Multi-channel, restart-safe, max 3 human-in-loop points.
"""

from .agent import TimesheetOrchestrationAgent, default_agent, goal, nodes, edges
from .config import default_config, metadata

__version__ = "1.0.0"

__all__ = [
    "TimesheetOrchestrationAgent",
    "default_agent",
    "goal",
    "nodes",
    "edges",
    "default_config",
    "metadata",
]
