# Task 02: FormattedMessage component

## Location

- `packages/dashboard/src/components/FormattedMessage.jsx` (new)

## Dependencies

- Task 01: `react-markdown`, `remark-gfm`, `rehype-sanitize`

## What to build

Reusable component that renders assistant markdown safely with custom element mappings for links and code.

## Design spec

### Props

```jsx
FormattedMessage({ text, className = 'assistant-text' })
```

- `text`: string (markdown source from agent reply)
- `className`: wrapper class (default matches current ChatPanel assistant bubble)

### Implementation skeleton

```jsx
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';

export default function FormattedMessage({ text, className = 'assistant-text' }) {
  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={{
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
          ),
          // optional: code/pre mappings for class hooks
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}
```

### Security

- **Only** `rehype-sanitize` — no `rehype-raw`.
- Default sanitize schema strips `<script>`, `onerror`, `javascript:` URLs.

### Supported elements

- Headings `h1`–`h3` (agent typically uses h3 or bold)
- `strong`, `em`
- `ul`, `ol`, `li`
- `code` (inline), `pre` > `code` (fenced blocks)
- `table`, `thead`, `tbody`, `tr`, `th`, `td` (via GFM)
- `a` — external links only styling

### Edge cases

- Empty string → render empty wrapper (no crash).
- Null/undefined text → treat as `''`.

## Done when

- [ ] Component renders `**bold**` as `<strong>`.
- [ ] Fenced code block renders `<pre><code>`.
- [ ] Links have `target="_blank"` and `rel="noopener noreferrer"`.
- [ ] Raw `<script>alert(1)</script>` in text does not execute (see task 05).
