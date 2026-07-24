import Decision from '../../components/Decision.jsx';

export default function DecisionCardBlock({
  decision,
  bullets = [],
  handlers = {},
}) {
  if (!decision) return null;

  return (
    <div className="sdui-decision-card">
      <Decision
        decision={decision}
        onApply={handlers.onApply}
        applyState={handlers.applyState}
        applyError={handlers.applyError}
        trafficSplit={handlers.trafficSplit}
        experimentStatus={handlers.experimentStatus}
        summaryBullets={bullets}
      />
    </div>
  );
}
