import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize';
import { prepareAssistantMarkdown } from '../lib/prepareAssistantMarkdown.js';

const sanitizeSchema = {
  ...defaultSchema,
  attributes: {
    ...defaultSchema.attributes,
    code: [...(defaultSchema.attributes?.code || []), 'className'],
    span: [...(defaultSchema.attributes?.span || []), 'className'],
  },
  tagNames: [
    ...(defaultSchema.tagNames || []),
    'summary',
    'details',
  ],
};

export default function FormattedMessage({ text, className = 'assistant-text' }) {
  const content = prepareAssistantMarkdown(text);

  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[[rehypeSanitize, sanitizeSchema]]}
        components={{
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
          ),
          pre: ({ children }) => <pre className="md-pre">{children}</pre>,
          code: ({ className: codeClass, children, ...props }) => {
            const isBlock = Boolean(codeClass?.startsWith('language-'));
            if (!isBlock) {
              return <code className="md-inline-code" {...props}>{children}</code>;
            }
            const lang = codeClass.replace('language-', '');
            return (
              <code className={`md-code-block language-${lang}`} {...props}>
                {children}
              </code>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
