"""Foundation smoke test for FirstLight AI Studio.

This script verifies that the core application context and shared services
initialize correctly.
"""

from app.core.application import ApplicationContext


def main() -> int:
    """Run the foundation initialization smoke test.

    Returns:
        Exit code ``0`` when initialization succeeds, otherwise ``1``.
    """
    print("=== FirstLight AI Studio Foundation Smoke Test ===")

    try:
        context = ApplicationContext()

        prompt_manager = context.prompt_manager
        print(f"[OK] PromptManager: {type(prompt_manager).__name__}")

        provider = context.provider
        print(f"[OK] Provider: {type(provider).__name__}")

        ai_engine = context.ai_engine
        print(f"[OK] AIEngine: {type(ai_engine).__name__}")

        planning_service = context.planning_service
        print(f"[OK] PlanningService: {type(planning_service).__name__}")

        print("=== Summary: Foundation initialization succeeded ===")
        return 0
    except Exception as exc:
        print(f"[ERROR] Foundation initialization failed: {type(exc).__name__}: {exc}")
        print("=== Summary: Foundation initialization failed ===")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
