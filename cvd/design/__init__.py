"""Design assembly: turn a Config into a laid-out, checked Design."""

from .builder import build_design
from .checks import check_insert

__all__ = ["build_design", "check_insert"]
