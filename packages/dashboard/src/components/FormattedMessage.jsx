import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';
import { prepareAssistantMarkdown } from '../lib/prepareAssistantMarkdown.js';

export default function FormattedMessage({ text, className = 'assistant-text' }) {
  const content = prepareAssistantMarkdown(text);

  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={{
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
          ),
          pre: ({ children }) => <pre className="md-pre">{children}</pre>,
          code: ({ inline, className: codeClass, children, ...props }) => {
            if (inline) {
              return <code className="md-inline-code" {...props}>{children}</code>;
            }
            const lang = codeClass?.replace('language-', '') || 'text';
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
