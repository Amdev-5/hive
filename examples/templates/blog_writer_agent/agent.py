"""Agent graph construction for Blog Writer Agent."""

from framework.graph import EdgeSpec, EdgeCondition, Goal, SuccessCriterion, Constraint
from framework.graph.edge import GraphSpec
from framework.graph.executor import ExecutionResult, GraphExecutor
from framework.runtime.event_bus import EventBus
from framework.runtime.core import Runtime
from framework.llm import LiteLLMProvider
from framework.runner.tool_registry import ToolRegistry

from .config import default_config, metadata
from .nodes import (
    intake_node,
    research_node,
    positioning_node,
    outline_review_node,
    write_draft_node,
    seo_optimize_node,
    quality_gate_node,
    publish_node,
)

# Goal definition
goal = Goal(
    id="business-blog-writer",
    name="Business Blog Writer",
    description=(
        "Create a business-focused blog post with strong positioning, "
        "credible sources, and clear SEO metadata — with human checkpoints."
    ),
    success_criteria=[
        SuccessCriterion(
            id="source-quality",
            description="Use multiple authoritative sources",
            metric="source_count",
            target=">=5",
            weight=0.2,
        ),
        SuccessCriterion(
            id="citation-coverage",
            description="All factual claims in the blog cite a source",
            metric="citation_coverage",
            target="100%",
            weight=0.2,
        ),
        SuccessCriterion(
            id="outline-approval",
            description="User approves thesis + outline before drafting",
            metric="user_approval",
            target="true",
            weight=0.2,
        ),
        SuccessCriterion(
            id="seo-basics",
            description="Blog includes title, meta description, and keywords",
            metric="seo_metadata_complete",
            target="true",
            weight=0.2,
        ),
        SuccessCriterion(
            id="cta-present",
            description="Clear business CTA included",
            metric="cta_present",
            target="true",
            weight=0.2,
        ),
    ],
    constraints=[
        Constraint(
            id="no-hallucination",
            description="Only include information found in sources",
            constraint_type="quality",
            category="accuracy",
        ),
        Constraint(
            id="source-attribution",
            description="Every claim must cite its source with numbered references",
            constraint_type="quality",
            category="accuracy",
        ),
        Constraint(
            id="human-checkpoints",
            description="User approves outline and final quality gate",
            constraint_type="functional",
            category="interaction",
        ),
    ],
)

# Node list
nodes = [
    intake_node,
    research_node,
    positioning_node,
    outline_review_node,
    write_draft_node,
    seo_optimize_node,
    quality_gate_node,
    publish_node,
]

# Edge definitions
edges = [
    EdgeSpec(
        id="intake-to-research",
        source="intake",
        target="research",
        condition=EdgeCondition.ON_SUCCESS,
        priority=1,
    ),
    EdgeSpec(
        id="research-to-positioning",
        source="research",
        target="positioning",
        condition=EdgeCondition.ON_SUCCESS,
        priority=1,
    ),
    EdgeSpec(
        id="positioning-to-outline-review",
        source="positioning",
        target="outline_review",
        condition=EdgeCondition.ON_SUCCESS,
        priority=1,
    ),
    EdgeSpec(
        id="outline-review-to-positioning",
        source="outline_review",
        target="positioning",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="str(needs_outline_changes).lower() == 'true'",
        priority=2,
    ),
    EdgeSpec(
        id="outline-review-to-draft",
        source="outline_review",
        target="write_draft",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="str(needs_outline_changes).lower() != 'true'",
        priority=1,
    ),
    EdgeSpec(
        id="draft-to-seo",
        source="write_draft",
        target="seo_optimize",
        condition=EdgeCondition.ON_SUCCESS,
        priority=1,
    ),
    EdgeSpec(
        id="seo-to-quality",
        source="seo_optimize",
        target="quality_gate",
        condition=EdgeCondition.ON_SUCCESS,
        priority=1,
    ),
    EdgeSpec(
        id="quality-to-draft",
        source="quality_gate",
        target="write_draft",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="str(needs_revision).lower() == 'true'",
        priority=2,
    ),
    EdgeSpec(
        id="quality-to-publish",
        source="quality_gate",
        target="publish",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="str(needs_revision).lower() != 'true'",
        priority=1,
    ),
]

# Graph configuration
entry_node = "intake"
entry_points = {"start": "intake"}
pause_nodes = []
terminal_nodes = ["publish"]


class BlogWriterAgent:
    """
    Blog Writer Agent — 8-node business writing pipeline with HITL gates.

    Flow: intake -> research -> positioning -> outline_review -> write_draft
                     -> seo_optimize -> quality_gate -> publish
                     ^                             |
                     +----------- outline loop     +---- revision loop
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
        self._executor: GraphExecutor | None = None
        self._graph: GraphSpec | None = None
        self._event_bus: EventBus | None = None
        self._tool_registry: ToolRegistry | None = None

    def _build_graph(self) -> GraphSpec:
        """Build the GraphSpec."""
        return GraphSpec(
            id="blog-writer-agent-graph",
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
                "max_iterations": 120,
                "max_tool_calls_per_turn": 20,
                "max_history_tokens": 32000,
            },
        )

    def _setup(self) -> GraphExecutor:
        """Set up the executor with all components."""
        from pathlib import Path

        storage_path = Path.home() / ".hive" / "agents" / "blog_writer_agent"
        storage_path.mkdir(parents=True, exist_ok=True)

        self._event_bus = EventBus()
        self._tool_registry = ToolRegistry()

        mcp_config_path = Path(__file__).parent / "mcp_servers.json"
        if mcp_config_path.exists():
            self._tool_registry.load_mcp_config(mcp_config_path)

        llm = LiteLLMProvider(
            model=self.config.model,
            api_key=self.config.api_key,
            api_base=self.config.api_base,
        )

        tool_executor = self._tool_registry.get_executor()
        tools = list(self._tool_registry.get_tools().values())

        self._graph = self._build_graph()
        runtime = Runtime(storage_path)

        self._executor = GraphExecutor(
            graph=self._graph,
            goal=self.goal,
            llm=llm,
            tools=tools,
            tool_executor=tool_executor,
            event_bus=self._event_bus,
            runtime=runtime,
        )

        return self._executor

    async def run(self, context: dict) -> ExecutionResult:
        """Execute the agent graph."""
        executor = self._setup()
        return await executor.execute(context)


# Default agent instance
_default_agent = BlogWriterAgent()


default_agent = _default_agent

