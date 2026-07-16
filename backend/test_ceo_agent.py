"""CEOAgent smoke test for FirstLight AI Studio.

This script validates CEOAgent dependency wiring and can optionally run a live
plan generation call.
"""

from __future__ import annotations

import argparse

from app.core.application import ApplicationContext
from app.engine.agents.ceo_agent import CEOAgent
from app.engine.parser import ResponseParser


def main() -> int:
    """Run the CEO agent smoke test.

    Returns:
        Exit code ``0`` when the smoke test succeeds, otherwise ``1``.
    """
    parser = argparse.ArgumentParser(description="Run CEOAgent smoke test")
    parser.add_argument(
        "--run-plan",
        action="store_true",
        help="Execute a live plan generation call",
    )
    args = parser.parse_args()

    print("=== FirstLight AI Studio CEOAgent Smoke Test ===")

    try:
        context = ApplicationContext()
        planning_service = context.planning_service
        response_parser = ResponseParser()
        ceo_agent = CEOAgent(
            planning_service=planning_service,
            response_parser=response_parser,
        )

        print(f"[OK] ApplicationContext: {type(context).__name__}")
        print(f"[OK] PlanningService: {type(planning_service).__name__}")
        print(f"[OK] ResponseParser: {type(response_parser).__name__}")
        print(f"[OK] CEOAgent: {type(ceo_agent).__name__}")

        if args.run_plan:
            plan = ceo_agent.plan("Build a 30-day launch plan for FirstLight AI Studio")
            print(f"[OK] Plan parsed: {type(plan).__name__}")
            print(f"[OK] Task count: {len(plan.tasks)}")
        else:
            print("[INFO] Live plan run skipped. Use --run-plan to execute generation.")

        print("=== Summary: CEOAgent smoke test succeeded ===")
        return 0
    except Exception as exc:
        print(f"[ERROR] CEOAgent smoke test failed: {type(exc).__name__}: {exc}")
        print("=== Summary: CEOAgent smoke test failed ===")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
