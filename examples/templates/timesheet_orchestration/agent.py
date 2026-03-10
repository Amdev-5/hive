"""Agent graph construction for Timesheet Orchestration Agent.

Graph: 6 nodes, 7 edges, 2 feedback loops, 3 HIL points.

    [intake] ──► [dispatch] ──► [collect] ──► [validate] ──► [report] ──► [deliver]
                    ▲               ▲              │             │
                    │               └── e4 ────────┘ (clarify)
                    └────────── e5 ────────────────┘ (missing)
"""

from pathlib import Path

from framework.graph import EdgeSpec, EdgeCondition, Goal, SuccessCriterion, Constraint
from framework.graph.edge import GraphSpec
from framework.graph.executor import ExecutionResult
from framework.graph.checkpoint_config import CheckpointConfig
from framework.llm import LiteLLMProvider
from framework.llm.mock import MockLLMProvider
from framework.runner.tool_registry import ToolRegistry
from framework.runtime.agent_runtime import AgentRuntime, create_agent_runtime
from framework.runtime.execution_stream import EntryPointSpec

from .config import default_config
from .nodes import (
    intake_node,
    dispatch_node,
    collect_node,
    validate_node,
    report_node,
    deliver_node,
)

# ─────────────────────────────────────────────────────────────
# Goal
# ─────────────────────────────────────────────────────────────
goal = Goal(
    id="timesheet-orchestration",
    name="Timesheet Orchestration Agent",
    description=(
        "Autonomously collect weekly timesheets from team members via Slack, "
        "send reminders via Telegram, validate and consolidate data, generate "
        "executive insights, and deliver a professional report via Email."
    ),
    success_criteria=[
        SuccessCriterion(
            id="collection-rate",
            description="Collect timesheets from >=90% of employees",
            metric="submission_rate",
            target=">=0.9",
            weight=0.25,
        ),
        SuccessCriterion(
            id="data-accuracy",
            description="All submitted hours pass arithmetic validation",
            metric="validation_pass_rate",
            target=">=0.95",
            weight=0.25,
        ),
        SuccessCriterion(
            id="report-quality",
            description=(
                "Executive report contains charts, per-person/project breakdowns, "
                "risk flags, and recommendations"
            ),
            metric="report_completeness",
            target=">=0.9",
            weight=0.3,
        ),
        SuccessCriterion(
            id="delivery-success",
            description="Report delivered to executive via email within 24h of deadline",
            metric="delivery_latency_hours",
            target="<=24",
            weight=0.2,
        ),
    ],
    constraints=[
        Constraint(
            id="max-3-hil",
            description=(
                "Maximum 3 human-in-loop points: intake setup, "
                "collection oversight, executive delivery"
            ),
            constraint_type="hard",
            category="workflow",
        ),
        Constraint(
            id="no-hallucinated-hours",
            description="Never fabricate timesheet data. Only use data from actual messages.",
            constraint_type="hard",
            category="accuracy",
        ),
        Constraint(
            id="privacy",
            description="Individual timesheet data not shared between employees.",
            constraint_type="hard",
            category="security",
        ),
        Constraint(
            id="idempotent-reminders",
            description="No duplicate reminders on restart. Check dispatch_log before sending.",
            constraint_type="hard",
            category="reliability",
        ),
        Constraint(
            id="arithmetic-validation",
            description="Per-task hours must sum to reported total. Flag discrepancies.",
            constraint_type="hard",
            category="accuracy",
        ),
    ],
)

# ─────────────────────────────────────────────────────────────
# Nodes
# ─────────────────────────────────────────────────────────────
nodes = [
    intake_node,
    dispatch_node,
    collect_node,
    validate_node,
    report_node,
    deliver_node,
]

# ─────────────────────────────────────────────────────────────
# Edges (7 edges, 2 feedback loops)
# ─────────────────────────────────────────────────────────────
edges = [
    # Happy path: intake → dispatch → collect → validate → report → deliver
    EdgeSpec(
        id="e1-intake-to-dispatch",
        source="intake",
        target="dispatch-reminders",
        condition=EdgeCondition.ON_SUCCESS,
        priority=1,
    ),
    EdgeSpec(
        id="e2-dispatch-to-collect",
        source="dispatch-reminders",
        target="collect-timesheets",
        condition=EdgeCondition.ON_SUCCESS,
        priority=1,
    ),
    EdgeSpec(
        id="e3-collect-to-validate",
        source="collect-timesheets",
        target="validate-consolidate",
        condition=EdgeCondition.ON_SUCCESS,
        priority=1,
    ),
    # ── FEEDBACK LOOP 1: Clarification needed ──
    # If validation finds issues, send back to collect for clarification
    EdgeSpec(
        id="e4-validate-to-collect",
        source="validate-consolidate",
        target="collect-timesheets",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="str(validation_passed).lower() != 'true'",
        priority=2,
    ),
    # ── FEEDBACK LOOP 2: Missing submissions ──
    # If employees haven't responded, re-dispatch reminders
    EdgeSpec(
        id="e5-validate-to-dispatch",
        source="validate-consolidate",
        target="dispatch-reminders",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr=(
            "str(validation_passed).lower() == 'true' "
            "and missing_employees "
            "and len(missing_employees) > 0"
        ),
        priority=3,
    ),
    # Happy path continues: validation passed → generate report
    EdgeSpec(
        id="e6-validate-to-report",
        source="validate-consolidate",
        target="generate-report",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="str(validation_passed).lower() == 'true'",
        priority=1,
    ),
    # Report → deliver
    EdgeSpec(
        id="e7-report-to-deliver",
        source="generate-report",
        target="deliver-report",
        condition=EdgeCondition.ON_SUCCESS,
        priority=1,
    ),
]

# ─────────────────────────────────────────────────────────────
# Graph config
# ─────────────────────────────────────────────────────────────
entry_node = "intake"
entry_points = {
    "start": "intake",
    "weekly": "dispatch-reminders",
    "collect": "collect-timesheets",
}
pause_nodes = []
terminal_nodes = ["deliver-report"]
conversation_mode = "continuous"
identity_prompt = (
    "You are a timesheet orchestration agent. You help organizations "
    "collect, validate, and report on weekly timesheets autonomously. "
    "You are professional, concise, and data-driven."
)


class TimesheetOrchestrationAgent:
    """
    Timesheet Orchestration Agent — 6-node pipeline with 2 feedback loops.

    Channels:
    - Slack: 2-way collection (send + read)
    - Telegram: 1-way push (reminders, escalation)
    - Email: 1-way push (executive report delivery)
    """

    def __init__(self, config=None):
        self.config = config or default_config
        self.goal = goal
        self.nodes = nodes
        self.edges = edges
        self.entry_node = entry_node
        self.entry_points = entry_points
        self.pause_nodes = pause_nodes
        self.terminal_nodes = terminal_nodes
        self._graph: GraphSpec | None = None
        self._agent_runtime: AgentRuntime | None = None
        self._tool_registry: ToolRegistry | None = None
        self._storage_path: Path | None = None

    def _build_graph(self) -> GraphSpec:
        """Build the GraphSpec."""
        return GraphSpec(
            id="timesheet-orchestration-graph",
            goal_id=self.goal.id,
            version="1.0.0",
            entry_node=self.entry_node,
            entry_points=self.entry_points,
            terminal_nodes=self.terminal_nodes,
            pause_nodes=self.pause_nodes,
            nodes=self.nodes,
            edges=self.edges,
            default_model=self.config.model,
            max_tokens=self.config.max_tokens,
            loop_config={
                "max_iterations": 100,
                "max_tool_calls_per_turn": 20,
                "max_history_tokens": 32000,
            },
            conversation_mode=conversation_mode,
            identity_prompt=identity_prompt,
        )

    def _setup(self, mock_mode=False) -> None:
        """Set up the agent runtime."""
        self._storage_path = (
            Path.home() / ".hive" / "agents" / "timesheet_orchestration"
        )
        self._storage_path.mkdir(parents=True, exist_ok=True)

        self._tool_registry = ToolRegistry()

        mcp_config_path = Path(__file__).parent / "mcp_servers.json"
        if mcp_config_path.exists():
            self._tool_registry.load_mcp_config(mcp_config_path)

        if mock_mode:
            llm = MockLLMProvider(model="timesheet-mock")
        else:
            llm = LiteLLMProvider(
                model=self.config.model,
                api_key=self.config.api_key,
                api_base=self.config.api_base,
                **self.config.extra_kwargs,
            )

        tool_executor = self._tool_registry.get_executor()
        tools = list(self._tool_registry.get_tools().values())

        self._graph = self._build_graph()

        checkpoint_config = CheckpointConfig(
            enabled=True,
            checkpoint_on_node_start=True,
            checkpoint_on_node_complete=True,
            checkpoint_max_age_days=30,
            async_checkpoint=True,
        )

        entry_point_specs = [
            EntryPointSpec(
                id="start",
                name="Full Setup & Run",
                entry_node="intake",
                trigger_type="manual",
                isolation_level="shared",
            ),
            EntryPointSpec(
                id="weekly",
                name="Weekly Reminder Trigger",
                entry_node="dispatch-reminders",
                trigger_type="cron",
                isolation_level="shared",
            ),
            EntryPointSpec(
                id="collect",
                name="Collect Submissions",
                entry_node="collect-timesheets",
                trigger_type="webhook",
                isolation_level="shared",
            ),
        ]

        self._agent_runtime = create_agent_runtime(
            graph=self._graph,
            goal=self.goal,
            storage_path=self._storage_path,
            entry_points=entry_point_specs,
            llm=llm,
            tools=tools,
            tool_executor=tool_executor,
            checkpoint_config=checkpoint_config,
        )

    async def start(self, mock_mode=False) -> None:
        """Set up and start the agent runtime."""
        if self._agent_runtime is None:
            self._setup(mock_mode=mock_mode)
        if not self._agent_runtime.is_running:
            await self._agent_runtime.start()

    async def stop(self) -> None:
        """Stop the agent runtime and clean up."""
        if self._agent_runtime and self._agent_runtime.is_running:
            await self._agent_runtime.stop()
        self._agent_runtime = None

    async def trigger_and_wait(
        self,
        entry_point: str = "start",
        input_data: dict | None = None,
        timeout: float | None = None,
        session_state: dict | None = None,
    ) -> ExecutionResult | None:
        """Execute the graph and wait for completion."""
        if self._agent_runtime is None:
            raise RuntimeError("Agent not started. Call start() first.")

        return await self._agent_runtime.trigger_and_wait(
            entry_point_id=entry_point,
            input_data=input_data or {},
            session_state=session_state,
        )

    async def run(
        self, context: dict, mock_mode=False, session_state=None
    ) -> ExecutionResult:
        """Run the agent (convenience method)."""
        await self.start(mock_mode=mock_mode)
        try:
            result = await self.trigger_and_wait(
                "start", context, session_state=session_state
            )
            return result or ExecutionResult(
                success=False, error="Execution timeout"
            )
        finally:
            await self.stop()

    def validate(self):
        """Validate agent structure."""
        errors = []
        warnings = []
        node_ids = {node.id for node in self.nodes}

        for edge in self.edges:
            if edge.source not in node_ids:
                errors.append(f"Edge {edge.id}: source '{edge.source}' not found")
            if edge.target not in node_ids:
                errors.append(f"Edge {edge.id}: target '{edge.target}' not found")

        if self.entry_node not in node_ids:
            errors.append(f"Entry node '{self.entry_node}' not found")

        # Check HIL count
        hil_nodes = [n for n in self.nodes if n.client_facing]
        if len(hil_nodes) > 3:
            warnings.append(
                f"More than 3 client-facing nodes ({len(hil_nodes)}). "
                f"Assignment requires max 3 HIL points."
            )

        # Check actual feedback loops have max_node_visits.
        # A conditional edge alone is not necessarily feedback.
        adjacency: dict[str, set[str]] = {}
        for edge in self.edges:
            adjacency.setdefault(edge.source, set()).add(edge.target)

        def _path_exists(start: str, target: str) -> bool:
            if start == target:
                return True
            seen = set()
            stack = [start]
            while stack:
                current = stack.pop()
                if current in seen:
                    continue
                seen.add(current)
                for nxt in adjacency.get(current, set()):
                    if nxt == target:
                        return True
                    if nxt not in seen:
                        stack.append(nxt)
            return False

        for node in self.nodes:
            incoming_conditionals = [
                e
                for e in self.edges
                if e.target == node.id and e.condition == EdgeCondition.CONDITIONAL
            ]
            has_feedback = any(_path_exists(node.id, e.source) for e in incoming_conditionals)
            if has_feedback and node.max_node_visits <= 1:
                warnings.append(
                    f"Node '{node.id}' has feedback edges but max_node_visits=1. "
                    f"Feedback loop will never execute."
                )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }


# Create default instance
default_agent = TimesheetOrchestrationAgent()
