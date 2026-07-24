"""SDUI block schema v1 — discriminated union, no optional JSON blobs."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SDUI_VERSION = "1.0"

BlockType = Literal[
    "markdown",
    "metric_grid",
    "bar_chart",
    "funnel_chart",
    "table",
    "decision_card",
    "alert",
    "actions",
]

ALLOWED_ACTION_IDS = frozenset(
    {"apply_scale", "apply_rollback", "rerun_analyze", "open_preflight"}
)

DATA_VIZ_TYPES = frozenset({"bar_chart", "funnel_chart", "table"})
DECISION_TYPES = frozenset({"metric_grid", "decision_card", "actions"})


class BlockBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str
    id: str
    version: str = SDUI_VERSION


class MarkdownBlock(BlockBase):
    type: Literal["markdown"] = "markdown"
    content: str


class MetricItem(BaseModel):
    label: str
    value: str
    tone: Literal["positive", "negative", "neutral"] = "neutral"


class MetricGridBlock(BlockBase):
    type: Literal["metric_grid"] = "metric_grid"
    columns: int = Field(ge=1, le=4)
    metrics: list[MetricItem] = Field(min_length=1, max_length=4)


class ChartSeries(BaseModel):
    name: str
    value: float = Field(ge=0)


class VariantSeries(BaseModel):
    name: str
    values: list[float] = Field(min_length=1, max_length=50)


class BarChartBlock(BlockBase):
    type: Literal["bar_chart"] = "bar_chart"
    title: str
    y_label: str = Field(alias="yLabel")
    mode: Literal["simple", "grouped"] = "simple"
    series: list[ChartSeries] = Field(default_factory=list, max_length=50)
    categories: list[str] = Field(default_factory=list, max_length=50)
    grouped_series: list[VariantSeries] = Field(
        default_factory=list, alias="groupedSeries", max_length=4
    )

    @model_validator(mode="after")
    def validate_mode(self) -> BarChartBlock:
        if self.mode == "simple" and not self.series:
            raise ValueError("simple bar chart requires series")
        if self.mode == "grouped":
            if not self.categories or not self.grouped_series:
                raise ValueError("grouped bar chart requires categories and groupedSeries")
            width = len(self.categories)
            for vs in self.grouped_series:
                if len(vs.values) != width:
                    raise ValueError("grouped series values must match categories length")
        return self


class FunnelStep(BaseModel):
    label: str
    count: int = Field(ge=0)


class FunnelChartBlock(BlockBase):
    type: Literal["funnel_chart"] = "funnel_chart"
    title: str
    steps: list[FunnelStep] = Field(min_length=1, max_length=50)


class TableBlock(BlockBase):
    type: Literal["table"] = "table"
    title: str
    columns: list[str] = Field(min_length=1)
    rows: list[list[Any]] = Field(max_length=50)

    @model_validator(mode="after")
    def rows_match_columns(self) -> TableBlock:
        width = len(self.columns)
        for row in self.rows:
            if len(row) != width:
                raise ValueError("each row must match column count")
        return self


class DecisionCardBlock(BlockBase):
    type: Literal["decision_card"] = "decision_card"
    decision: dict[str, Any]
    bullets: list[str] = Field(max_length=5)


class AlertBlock(BlockBase):
    type: Literal["alert"] = "alert"
    tone: Literal["info", "warning", "error"] = "info"
    message: str


class ActionButton(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    action_id: str = Field(alias="actionId")
    label: str
    variant: Literal["primary", "secondary", "destructive"] = "secondary"
    disabled: bool = False

    @field_validator("action_id")
    @classmethod
    def allowed_action(cls, value: str) -> str:
        if value not in ALLOWED_ACTION_IDS:
            raise ValueError(f"actionId not allowed: {value}")
        return value


class ActionsBlock(BlockBase):
    type: Literal["actions"] = "actions"
    buttons: list[ActionButton] = Field(min_length=1, max_length=4)


BlockUnion = Annotated[
    MarkdownBlock
    | MetricGridBlock
    | BarChartBlock
    | FunnelChartBlock
    | TableBlock
    | DecisionCardBlock
    | AlertBlock
    | ActionsBlock,
    Field(discriminator="type"),
]


class WidgetPlan(BaseModel):
    should_render: bool = False
    block_types: list[BlockType] = Field(default_factory=list, max_length=8)
    rationale: str = ""


def block_to_dict(block: BlockUnion) -> dict[str, Any]:
    return block.model_dump(mode="json", by_alias=True, exclude_none=True)
