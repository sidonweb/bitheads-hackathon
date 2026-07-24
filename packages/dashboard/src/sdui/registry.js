import AlertBlock from './widgets/AlertBlock.jsx';
import ActionsBlock from './widgets/ActionsBlock.jsx';
import BarChartBlock from './widgets/BarChartBlock.jsx';
import DecisionCardBlock from './widgets/DecisionCardBlock.jsx';
import FunnelChartBlock from './widgets/FunnelChartBlock.jsx';
import MarkdownBlock from './widgets/MarkdownBlock.jsx';
import MetricGridBlock from './widgets/MetricGridBlock.jsx';
import TableBlock from './widgets/TableBlock.jsx';
import UnknownBlock from './widgets/UnknownBlock.jsx';

export const BLOCK_REGISTRY = {
  markdown: MarkdownBlock,
  metric_grid: MetricGridBlock,
  bar_chart: BarChartBlock,
  funnel_chart: FunnelChartBlock,
  table: TableBlock,
  decision_card: DecisionCardBlock,
  alert: AlertBlock,
  actions: ActionsBlock,
};

export { UnknownBlock };
