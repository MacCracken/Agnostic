"""Compatibility helpers for CrewAI tooling."""

try:
    from crewai.tools import BaseTool  # type: ignore
except Exception:  # pragma: no cover - fallback for older CrewAI builds
    class BaseTool:  # type: ignore
        name: str = ""
        description: str = ""

        def _run(self, *args, **kwargs):
            raise NotImplementedError("BaseTool._run must be implemented")
