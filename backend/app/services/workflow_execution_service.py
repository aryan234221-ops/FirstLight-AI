from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone

from app.engine.core.task import Plan
from app.engine.dispatcher import AgentDispatcher
from app.repositories.sql_repositories import ActivityRepository, WorkflowRepository
from app.workflows.workflow_planner import WorkflowPlanner


logger = logging.getLogger(__name__)


class WorkflowExecutionService:
    def __init__(
        self,
        planner: WorkflowPlanner,
        dispatcher: AgentDispatcher,
        workflow_repository: WorkflowRepository,
        activity_repository: ActivityRepository,
    ) -> None:
        self._planner = planner
        self._dispatcher = dispatcher
        self._workflow_repository = workflow_repository
        self._activity_repository = activity_repository

    def create_run_with_ceo_gate(self, project_id: str, goal: str, requested_by: str | None) -> tuple[str, Plan]:
        run = self._workflow_repository.create_run(project_id=project_id, goal=goal, requested_by=requested_by)
        self._workflow_repository.add_approval_gate(run.id, gate_name="CEO_PLAN")

        start = time.perf_counter()
        ceo_plan = self._dispatcher.dispatch("ceo", goal)
        latency = int((time.perf_counter() - start) * 1000)
        self._workflow_repository.add_agent_output(
            run_id=run.id,
            agent_name="ceo",
            goal=ceo_plan.goal,
            tasks=[{"title": task.title, "description": task.description} for task in ceo_plan.tasks],
            latency_ms=latency,
        )
        self._workflow_repository.add_event(
            run.id,
            event_type="approval_required",
            status="pending",
            message="CEO plan generated and waiting for review approval",
            agent_name="ceo",
            progress=10,
        )
        self._activity_repository.log(
            event_type="workflow.approval_required",
            message="Workflow awaiting CEO plan approval",
            project_id=project_id,
            user_id=requested_by,
        )
        return run.id, ceo_plan

    async def continue_run(self, run_id: str, edited_goal: str | None = None) -> None:
        run = self._workflow_repository.get_run(run_id)
        if run is None:
            raise ValueError("Workflow run not found")

        goal = edited_goal.strip() if isinstance(edited_goal, str) and edited_goal.strip() else run.goal
        run.goal = goal
        run.status = "running"
        run.approval_state = "approved"
        run.started_at = datetime.now(timezone.utc)
        run.error_message = None
        self._workflow_repository.update_run(run)

        outputs = self._workflow_repository.list_outputs(run.id)
        completed_agents = {output.agent_name for output in outputs}

        planned = self._planner.plan(goal)
        remaining = [agent for agent in planned if agent not in completed_agents]
        total_steps = max(len(planned), 1)

        self._workflow_repository.add_event(
            run.id,
            event_type="execution_started",
            status="running",
            message="Workflow execution started",
            progress=int((len(completed_agents) / total_steps) * 100),
        )

        started = time.perf_counter()
        try:
            for index, agent_name in enumerate(remaining, start=len(completed_agents) + 1):
                run.current_agent = agent_name
                self._workflow_repository.update_run(run)
                self._workflow_repository.add_event(
                    run.id,
                    event_type="agent_started",
                    status="running",
                    message=f"Running {agent_name}",
                    agent_name=agent_name,
                    progress=int(((index - 1) / total_steps) * 100),
                )

                await asyncio.sleep(0)
                local_start = time.perf_counter()
                plan = self._dispatcher.dispatch(agent_name, goal)
                latency = int((time.perf_counter() - local_start) * 1000)
                self._workflow_repository.add_agent_output(
                    run_id=run.id,
                    agent_name=agent_name,
                    goal=plan.goal,
                    tasks=[{"title": task.title, "description": task.description} for task in plan.tasks],
                    latency_ms=latency,
                )

                self._workflow_repository.add_event(
                    run.id,
                    event_type="agent_completed",
                    status="completed",
                    message=f"Completed {agent_name}",
                    agent_name=agent_name,
                    progress=int((index / total_steps) * 100),
                    payload={"task_count": len(plan.tasks)},
                )

            run.current_agent = None
            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc)
            run.duration_ms = int((time.perf_counter() - started) * 1000)
            self._workflow_repository.update_run(run)
            self._workflow_repository.add_event(
                run.id,
                event_type="execution_completed",
                status="completed",
                message="Workflow execution completed",
                progress=100,
            )
            self._workflow_repository.add_execution_history(
                project_id=run.project_id,
                execution_type="workflow",
                status="completed",
                input_payload={"goal": run.goal},
                output_payload={
                    "agent_sequence": [output.agent_name for output in self._workflow_repository.list_outputs(run.id)],
                },
                duration_ms=run.duration_ms,
            )
            self._activity_repository.log(
                event_type="workflow.completed",
                message="Workflow run completed",
                project_id=run.project_id,
                status="completed",
            )
        except Exception as exc:
            run.current_agent = None
            run.status = "failed"
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            run.duration_ms = int((time.perf_counter() - started) * 1000)
            self._workflow_repository.update_run(run)
            self._workflow_repository.add_event(
                run.id,
                event_type="execution_failed",
                status="failed",
                message=str(exc),
                progress=100,
            )
            self._workflow_repository.add_execution_history(
                project_id=run.project_id,
                execution_type="workflow",
                status="failed",
                input_payload={"goal": run.goal},
                output_payload={},
                duration_ms=run.duration_ms,
                error_message=str(exc),
            )
            self._activity_repository.log(
                event_type="workflow.failed",
                message="Workflow run failed",
                project_id=run.project_id,
                status="failed",
                payload={"error": str(exc)},
            )
            logger.exception("workflow_execution_failed", extra={"event": "workflow_execution_failed", "workflow_id": run.id})
            raise

    def read_run_detail(self, run_id: str) -> dict[str, object]:
        run = self._workflow_repository.get_run(run_id)
        if run is None:
            raise ValueError("Workflow run not found")

        outputs = self._workflow_repository.list_outputs(run_id)
        events = self._workflow_repository.list_events(run_id)
        return {
            "run": run,
            "outputs": outputs,
            "events": events,
        }

    def export_run(self, run_id: str) -> dict[str, object]:
        detail = self.read_run_detail(run_id)
        run = detail["run"]
        outputs = detail["outputs"]
        events = detail["events"]
        return {
            "run": {
                "id": run.id,
                "project_id": run.project_id,
                "goal": run.goal,
                "status": run.status,
                "approval_state": run.approval_state,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "duration_ms": run.duration_ms,
                "error_message": run.error_message,
            },
            "outputs": [
                {
                    "agent_name": output.agent_name,
                    "goal": output.goal,
                    "tasks": json.loads(output.tasks_json),
                    "status": output.status,
                    "latency_ms": output.latency_ms,
                    "token_usage": output.token_usage,
                    "cost": float(output.cost),
                    "error_message": output.error_message,
                }
                for output in outputs
            ],
            "events": [
                {
                    "event_type": event.event_type,
                    "agent_name": event.agent_name,
                    "status": event.status,
                    "message": event.message,
                    "progress": event.progress,
                    "payload": json.loads(event.payload_json),
                    "created_at": event.created_at.isoformat(),
                }
                for event in events
            ],
        }
