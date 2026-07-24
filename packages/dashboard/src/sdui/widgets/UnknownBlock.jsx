export default function UnknownBlock({ type }) {
  return (
    <div className="sdui-unknown" role="note">
      Unsupported widget: {type || 'unknown'}
    </div>
  );
}
