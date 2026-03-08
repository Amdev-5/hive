"""Runtime configuration for Timesheet Orchestration Agent."""

from dataclasses import dataclass

from framework.config import RuntimeConfig

default_config = RuntimeConfig()


@dataclass
class AgentMetadata:
    name: str = "Timesheet Orchestration Agent"
    version: str = "1.0.0"
    description: str = (
        "Autonomously collect weekly timesheets from team members via Slack, "
        "send reminders via Telegram, validate and consolidate data with "
        "LLM-powered extraction, generate executive insights with anomaly "
        "detection, and deliver a professional HTML report with charts via Email."
    )
    intro_message: str = (
        "Hi! I'm your Timesheet Orchestration Agent. I'll help you set up "
        "automated weekly timesheet collection from your team. I'll send "
        "reminders, collect hours via Slack, validate the data, and generate "
        "an executive-ready report with charts and insights. Let's get started "
        "by setting up your team roster."
    )


metadata = AgentMetadata()
