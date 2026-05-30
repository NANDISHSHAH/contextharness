"""ContextPack — universal AI context runtime."""

__version__ = "0.1.0"
__all__ = [
    "Project",
    "BuildStats",
    "AgentMemory",
    "SharedMemory",
    "WorkflowExtractor",
    "__version__",
]


def __getattr__(name: str):
    if name == "Project":
        from contextpack.core.project import Project

        return Project
    if name == "BuildStats":
        from contextpack.core.project import BuildStats

        return BuildStats
    if name == "AgentMemory":
        from contextpack.skills import AgentMemory

        return AgentMemory
    if name == "SharedMemory":
        from contextpack.skills import SharedMemory

        return SharedMemory
    if name == "WorkflowExtractor":
        from contextpack.workflows import WorkflowExtractor

        return WorkflowExtractor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
