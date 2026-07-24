"""Server-driven UI block schema, hinter, and builders."""

from .builders import build_blocks_for_plan, full_analysis_plan
from .hinter import hint_widgets
from .schema import SDUI_VERSION, WidgetPlan, block_to_dict

__all__ = [
    "SDUI_VERSION",
    "WidgetPlan",
    "block_to_dict",
    "build_blocks_for_plan",
    "full_analysis_plan",
    "hint_widgets",
]
