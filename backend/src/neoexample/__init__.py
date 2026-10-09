"""NeoExample API service."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("neoexample")
except PackageNotFoundError:  # pragma: no cover - running from a source tree
    __version__ = "0.0.0"

COMPONENT = "neoexample"
TITLE = "NeoExample"

__all__ = ["COMPONENT", "TITLE", "__version__"]
