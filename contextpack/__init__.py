"""ContextPack — universal AI context runtime."""

__version__ = "0.1.0"
__all__ = ["Project", "BuildStats", "__version__"]


def __getattr__(name: str):
    if name == "Project":
        from contextpack.core.project import Project

        return Project
    if name == "BuildStats":
        from contextpack.core.project import BuildStats

        return BuildStats
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
