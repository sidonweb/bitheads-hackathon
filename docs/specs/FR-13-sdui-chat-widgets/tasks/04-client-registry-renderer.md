# Task 04: Client Registry & Renderer

## Location

- `packages/dashboard/src/sdui/registry.js` (NEW)
- `packages/dashboard/src/components/BlockRenderer.jsx` (NEW)
- `packages/dashboard/src/sdui/widgets/` (NEW)

## Registry pattern

```javascript
import MetricGrid from './widgets/MetricGrid.jsx';
import BarChart from './widgets/BarChart.jsx';
// ...

export const BLOCK_REGISTRY = {
  markdown: MarkdownBlock,
  metric_grid: MetricGrid,
  bar_chart: BarChart,
  funnel_chart: FunnelChart,
  table: DataTable,
  decision_card: DecisionCardBlock,
  alert: AlertBlock,
  actions: ActionsBlock,
};

export function renderBlock(block, handlers) {
  const Component = BLOCK_REGISTRY[block.type];
  if (!Component) return <UnknownBlock type={block.type} />;
  return <Component key={block.id} {...block} handlers={handlers} />;
}
```

## ChatPanel integration

Replace per-message rendering:

```
messages[].blocks?.length
  → <BlockRenderer blocks={m.blocks} handlers={…} />
  : <FormattedMessage text={m.text} />
```

Handlers passed down: `{ onApply, onRerunAnalyze, onOpenPreflight }`.

## Design spec (visual)

```
┌─────────────────────────────────────┐
│ Assistant                           │
│ ┌─────────────────────────────────┐ │
│ │ Executive summary bullets       │ │  decision_card / markdown
│ └─────────────────────────────────┘ │
│ ┌──────┐ ┌──────┐ ┌──────┐         │
│ │ p=   │ │ +14% │ │ n=   │         │  metric_grid
│ └──────┘ └──────┘ └──────┘         │
│ ┌─────────────────────────────────┐ │
│ │  ████ A  ██████ B               │ │  bar_chart
│ └─────────────────────────────────┘ │
│ [ Apply Scale ]                     │  actions
└─────────────────────────────────────┘
```

Use existing design tokens from `styles.css` / `index.css`.

## Done when

- [ ] Unknown block type shows muted fallback, no crash
- [ ] Blocks stack vertically with consistent spacing
- [ ] `npm run build` passes
