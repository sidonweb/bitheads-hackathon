const TONE_CLASS = {
  info: 'sdui-alert-info',
  warning: 'sdui-alert-warning',
  error: 'sdui-alert-error',
};

export default function AlertBlock({ tone = 'info', message }) {
  if (!message) return null;
  return (
    <div className={`sdui-alert ${TONE_CLASS[tone] || TONE_CLASS.info}`} role="status">
      {message}
    </div>
  );
}
