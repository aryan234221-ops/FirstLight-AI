"""Workflow orchestration for multi-agent planning flows."""

import asyncio
import logging
from uuid import uuid4

from app.engine.dispatcher import AgentDispatcher
from app.engine.core.task import Plan
from app.workflows.workflow_context import WorkflowContext
from app.workflows.workflow_planner import WorkflowPlanner


logger = logging.getLogger(__name__)

class WorkflowOrchestrator:
    """Coordinate multi-step planning workflows across registered agents."""

    def __init__(self, dispatcher: AgentDispatcher, planner: WorkflowPlanner | None = None) -> None:
        """Initialize the workflow orchestrator.

        Args:
            dispatcher: Dispatcher used to route workflow steps to agents.
            planner: Planner used to determine dynamic workflow participants.
        """
        self.__dispatcher: AgentDispatcher = dispatcher
        self.__planner: WorkflowPlanner = planner or WorkflowPlanner()

    def execute(
        self,
        goal: str,
        project_id: str | None = None,
        workflow_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> WorkflowContext:
        """Execute workflow in a synchronous context."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                self.execute_async(
                    goal=goal,
                    project_id=project_id,
                    workflow_id=workflow_id,
                    metadata=metadata,
                )
            )

        raise RuntimeError("execute() cannot be called from an active event loop; use execute_async()")

    async def execute_async(
        self,
        goal: str,
        project_id: str | None = None,
        workflow_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> WorkflowContext:
        """Execute a dynamically planned multi-agent workflow.

        Args:
            goal: Initial workflow goal.
            project_id: Optional project identifier linked to the workflow.
            workflow_id: Optional workflow identifier. Auto-generated when omitted.
            metadata: Optional workflow metadata.

        Returns:
            Final workflow context with ordered completed plans.

        Raises:
            ValueError: If the goal is empty or whitespace-only.
            Exception: Re-raises dispatcher or downstream execution failures.
        """
        normalized_goal = goal.strip() if isinstance(goal, str) else ""
        if not normalized_goal:
            raise ValueError("goal must be a non-empty string")

        planned_agents = self.__planner.plan(normalized_goal)
        if not planned_agents:
            raise ValueError("workflow plan must include at least one agent")

        if len(planned_agents) != len(set(planned_agents)):
            raise ValueError("workflow plan contains duplicate agent names")

        supported_agents = self.__planner.supported_agents()
        unknown_agents = [name for name in planned_agents if name not in supported_agents]
        if unknown_agents:
            raise ValueError(f"workflow plan contains unknown agents: {', '.join(unknown_agents)}")

        workflow_context = WorkflowContext(
            goal=normalized_goal,
            project_id=project_id,
            workflow_id=workflow_id or str(uuid4()),
            execution_order=planned_agents,
            metadata=dict(metadata or {}),
            _allowed_agents=supported_agents,
        )

        logger.info(
            "workflow_context_created",
            extra={
                "event": "workflow_context_created",
                "workflow_id": workflow_context.workflow_id,
                "step_count": len(planned_agents),
                "agent_names": planned_agents,
            },
        )

        logger.info(
            "workflow_plan_created",
            extra={
                "event": "workflow_plan_created",
                "step_count": len(planned_agents),
                "agent_names": planned_agents,
            },
        )

        dependencies = self.__build_dependency_map(planned_agents)
        execution_batches = self.__build_execution_batches(planned_agents, dependencies)

        try:
            completed_count = 0
            for batch in execution_batches:
                logger.info(
                    "workflow_parallel_started",
                    extra={
                        "event": "workflow_parallel_started",
                        "workflow_id": workflow_context.workflow_id,
                        "agent_names": batch,
                        "batch_size": len(batch),
                    },
                )

                task_map: dict[str, asyncio.Task[Plan]] = {}
                async with asyncio.TaskGroup() as task_group:
                    for agent_name in batch:
                        step_index = completed_count + batch.index(agent_name) + 1
                        logger.info(
                            "workflow_step_started",
                            extra={
                                "event": "workflow_step_started",
                                "step": step_index,
                                "agent_name": agent_name,
                                "workflow_id": workflow_context.workflow_id,
                            },
                        )
                        task_map[agent_name] = task_group.create_task(
                            self.__dispatch_async(agent_name, workflow_context)
                        )

                for agent_name in batch:
                    plan = task_map[agent_name].result()
                    await workflow_context.add_plan_async(
                        agent_name=agent_name,
                        plan=plan,
                        required_dependencies=dependencies.get(agent_name, set()),
                    )

                    logger.info(
                        "workflow_merge_completed",
                        extra={
                            "event": "workflow_merge_completed",
                            "workflow_id": workflow_context.workflow_id,
                            "agent_name": agent_name,
                            "completed_steps": workflow_context.completed_steps,
                        },
                    )

                    logger.info(
                        "workflow_context_updated",
                        extra={
                            "event": "workflow_context_updated",
                            "workflow_id": workflow_context.workflow_id,
                            "agent_name": agent_name,
                            "completed_steps": workflow_context.completed_steps,
                        },
                    )

                    completed_count += 1
                    logger.info(
                        "workflow_step_completed",
                        extra={
                            "event": "workflow_step_completed",
                            "step": completed_count,
                            "agent_name": agent_name,
                            "workflow_id": workflow_context.workflow_id,
                        },
                    )

                logger.info(
                    "workflow_parallel_completed",
                    extra={
                        "event": "workflow_parallel_completed",
                        "workflow_id": workflow_context.workflow_id,
                        "agent_names": batch,
                        "batch_size": len(batch),
                    },
                )
        except Exception as exc:
            logger.exception(
                "workflow_failed",
                extra={
                    "event": "workflow_failed",
                    "workflow_id": workflow_context.workflow_id,
                    "error_type": type(exc).__name__,
                },
            )
            raise

        logger.info(
            "workflow_context_completed",
            extra={
                "event": "workflow_context_completed",
                "workflow_id": workflow_context.workflow_id,
                "completed_steps": workflow_context.completed_steps,
            },
        )

        logger.info(
            "workflow_completed",
            extra={
                "event": "workflow_completed",
                "step_count": len(workflow_context.completed_agent_plans),
                "agent_names": workflow_context.completed_steps,
                "workflow_id": workflow_context.workflow_id,
            },
        )

        return workflow_context

    async def __dispatch_async(self, agent_name: str, workflow_context: WorkflowContext) -> Plan:
        """Dispatch an agent using structured workflow context."""
        # Yield once so sibling tasks can start before synchronous dispatch blocks.
        await asyncio.sleep(0)
        return self.__dispatcher.dispatch(
            agent_name=agent_name,
            goal=workflow_context.build_agent_goal(agent_name),
        )

    @staticmethod
    def __build_dependency_map(planned_agents: list[str]) -> dict[str, set[str]]:
        dependency_template: dict[str, set[str]] = {
            "ceo": set(),
            "architect": {"ceo"},
            "backend": {"architect"},
            "frontend": {"architect"},
            "database": {"backend"},
            "qa": {"database", "frontend", "backend", "architect"},
            "devops": {"qa", "database", "frontend", "backend", "architect"},
        }

        planned_set = set(planned_agents)
        dependencies: dict[str, set[str]] = {}
        for agent_name in planned_agents:
            dependencies[agent_name] = dependency_template.get(agent_name, set()) & planned_set
        return dependencies

    @staticmethod
    def __build_execution_batches(
        planned_agents: list[str], dependencies: dict[str, set[str]]
    ) -> list[list[str]]:
        remaining = set(planned_agents)
        completed: set[str] = set()
        batches: list[list[str]] = []

        while remaining:
            ready = [
                agent_name
                for agent_name in planned_agents
                if agent_name in remaining and dependencies.get(agent_name, set()) <= completed
            ]
            if not ready:
                unresolved = ", ".join(sorted(remaining))
                raise ValueError(f"workflow dependencies unresolved for: {unresolved}")

            batches.append(ready)
            for agent_name in ready:
                remaining.remove(agent_name)
                completed.add(agent_name)

        return batches
