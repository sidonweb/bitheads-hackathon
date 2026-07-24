import { useState } from 'react';

// Shows how the Copilot reasoned: the SQL it wrote + rule rationale.
// Turns the agent from a black box into a demo talking point.
export default function ReasoningExpander({ decision }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="expander">
      <button className="expander-toggle" onClick={() => setOpen((o) => !o)}>
        {open ? '▾' : '▸'} How the Copilot reasoned
      </button>
      {open && (
        <div className="expander-body">
          <div className="field-label">SQL the agent wrote</div>
          <pre className="sql">{decision.sql_used || '(not captured)'}</pre>
          <div className="field-label">Decision rule applied</div>
          <p className="muted">{decision.rule_rationale}</p>
        </div>
      )}
    </div>
  );
}
