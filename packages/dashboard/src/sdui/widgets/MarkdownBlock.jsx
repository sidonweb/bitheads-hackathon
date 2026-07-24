import FormattedMessage from '../../components/FormattedMessage.jsx';

export default function MarkdownBlock({ content }) {
  if (!content?.trim()) return null;
  return (
    <div className="sdui-markdown">
      <FormattedMessage text={content} />
    </div>
  );
}
