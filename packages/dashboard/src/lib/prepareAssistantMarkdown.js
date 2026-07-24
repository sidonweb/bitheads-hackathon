/**
 * Wrap raw SQL in the assistant reply with fenced ```sql blocks so react-markdown
 * renders them like ChatGPT/Claude code blocks instead of plain pre-wrapped text.
 */

const SQL_STATEMENT =
  /SELECT[\s\S]*?\bFROM\b[\s\S]*?(?:;(?=\s|$)|(?=\n\n)|$)/gi;

const SQL_LINE_RUN =
  /(?:^|\n)((?:[ \t]*(?:SELECT|WITH)\b[\s\S]*?)(?:;(?=\s|$)|$))/gim;

const SQL_FRAGMENT_BODY =
  /(?:^|\n)((?:variant_id|WITH)[\s\S]*?(?:universal_events|GROUP\s+BY)[\s\S]*?(?:;(?=\s|$)|$))/gim;

export function stripLeakedSql(text) {
  if (!text?.trim()) return text ?? '';
  let out = text;
  // Glued prose after SQL: GROUP BY variant_idIt seems...
  out = out.replace(/variant_id[\s\S]*?GROUP\s+BY\s+variant_id(?=[A-Za-z])/gi, '');
  out = out.replace(
    /variant_id[\s\S]*?(?:universal_events|GROUP\s+BY)[\s\S]*?(?:;|\n\n|$)/gi,
    '',
  );
  out = out.replace(
    /(?:^|\s)(?:variant_id|universal_events)[\s\S]*?(?=It |The |There |However|I |We )/gi,
    ' ',
  );
  out = out.replace(/SELECT[\s\S]*?;/gi, '');
  out = out.replace(/\n{3,}/g, '\n\n');
  return out.trimStart();
}

export function prepareAssistantMarkdown(text) {
  if (!text?.trim()) return text ?? '';
  const cleaned = stripLeakedSql(text);
  if (cleaned.includes('```')) return cleaned;

  let result = cleaned;

  result = result.replace(SQL_FRAGMENT_BODY, (full, sql) => {
    const trimmed = sql.trim().replace(/\s*;+\s*$/, ';');
    if (trimmed.length < 24) return full;
    return `\n\n\`\`\`sql\n${trimmed}\n\`\`\`\n`;
  });

  result = result.replace(SQL_STATEMENT, (match) => {
    const sql = match.trim().replace(/\s*;+\s*$/, ';');
    if (sql.length < 24 || !/\bFROM\b/i.test(sql)) return match;
    return `\n\n\`\`\`sql\n${sql}\n\`\`\`\n`;
  });

  // Catch SELECT blocks that start on their own line but weren't matched above
  result = result.replace(SQL_LINE_RUN, (full, sql) => {
    if (full.includes('```')) return full;
    const trimmed = sql.trim().replace(/\s*;+\s*$/, ';');
    if (trimmed.length < 24 || !/\bFROM\b/i.test(trimmed)) return full;
    return `\n\n\`\`\`sql\n${trimmed}\n\`\`\`\n`;
  });

  return result;
}
