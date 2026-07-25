/**
 * Minimal cleanup of assistant markdown before rendering.
 * The backend already strips leaked SQL from streamed tokens, so this layer
 * only handles edge cases that slip through (e.g. fallback non-streaming path).
 */

const FULL_SQL_BLOCK = /^[ \t]*SELECT\b[\s\S]*?\bFROM\b[\s\S]*?;[ \t]*$/gm;

export function stripLeakedSql(text) {
  if (!text?.trim()) return text ?? '';
  let out = text;
  out = out.replace(FULL_SQL_BLOCK, '');
  out = out.replace(/\n{3,}/g, '\n\n');
  return out.trimStart();
}

export function prepareAssistantMarkdown(text) {
  if (!text?.trim()) return text ?? '';
  return stripLeakedSql(text);
}
