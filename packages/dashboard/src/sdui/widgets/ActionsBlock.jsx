const VARIANT_CLASS = {
  primary: 'btn-primary',
  secondary: 'btn-secondary',
  destructive: 'btn-danger-outline',
};

export default function ActionsBlock({ buttons = [], handlers = {} }) {
  if (!buttons.length) return null;
  const onAction = handlers.onAction || (() => {});

  return (
    <div className="sdui-actions">
      {buttons.map((btn) => (
        <button
          key={btn.actionId}
          type="button"
          className={`btn sdui-action-btn ${VARIANT_CLASS[btn.variant] || VARIANT_CLASS.secondary}`}
          disabled={btn.disabled}
          onClick={() => onAction(btn.actionId)}
        >
          {btn.label}
        </button>
      ))}
    </div>
  );
}
