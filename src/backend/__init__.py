"""ResumeMate Backend Package

Use lazy imports to avoid circular import problems when submodules import
other modules in the same package during package initialization.
"""

__version__ = "0.1.0"

# Do not eagerly import submodules here to avoid circular imports.
# Provide lazy accessors so external code can do:
#   from backend import ResumeMateProcessor
import importlib

__all__ = ["ResumeMateProcessor"]


def __getattr__(name: str):
    """Lazily import attributes from submodules on first access.

    This avoids importing `processor` during package initialization which
    can cause circular imports with modules under `backend.agents`.
    """
    if name == "ResumeMateProcessor":
        module = importlib.import_module(".processor", __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


def __dir__():
    return sorted(list(globals().keys()) + __all__)
