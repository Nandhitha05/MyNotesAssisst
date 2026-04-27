import React from "react";

export default function Message({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={"msg " + (isUser ? "user" : "ai")}>
      <div className="bubble">
        <div className="content">{renderContent(msg.content)}</div>

        {msg.sources && msg.sources.length > 0 && (
          <div className="sources">
            <span className="src-label">
              {msg.source_kind === "web" ? "Web sources" : "Sources"}
            </span>
            {msg.sources.map((s, i) => {
              if (s.kind === "web" && s.url) {
                return (
                  <a
                    key={i}
                    href={s.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="src-pill src-web"
                  >
                    🌐 {s.file}
                  </a>
                );
              }
              return (
                <span key={i} className="src-pill">
                  {s.file}
                  {s.page !== undefined && s.page !== "?" && s.page !== null
                    ? ` · p.${s.page}`
                    : ""}
                </span>
              );
            })}
          </div>
        )}

        {msg.mode && msg.mode !== "auto" && (
          <div className="mode-tag">mode: {msg.mode}</div>
        )}
      </div>
    </div>
  );
}

function escapeHtml(s) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function inline(line) {
  let s = escapeHtml(line);
  s = s.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
  s = s.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
  );
  // Bare URLs — leading lookbehind avoids re-wrapping ones already inside an href.
  s = s.replace(
    /(^|[^"=>])(https?:\/\/[^\s<)]+)/g,
    '$1<a href="$2" target="_blank" rel="noopener noreferrer">$2</a>'
  );
  return s;
}

function renderContent(text) {
  if (text == null) return null;
  if (typeof text !== "string") {
    try {
      text = JSON.stringify(text, null, 2);
    } catch {
      text = String(text);
    }
  }

  // Pull fenced code blocks out first so their bodies aren't reinterpreted as markdown.
  const blocks = [];
  const codeFence = /```([a-zA-Z0-9_+-]*)\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;
  while ((match = codeFence.exec(text)) !== null) {
    if (match.index > lastIndex) {
      blocks.push({ type: "text", content: text.slice(lastIndex, match.index) });
    }
    blocks.push({ type: "code", lang: match[1] || "", content: match[2] });
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) {
    blocks.push({ type: "text", content: text.slice(lastIndex) });
  }

  return blocks.map((b, bi) => {
    if (b.type === "code") {
      return (
        <pre key={bi} className="code-block">
          {b.lang && <div className="code-lang">{b.lang}</div>}
          <code>{b.content.replace(/\n$/, "")}</code>
        </pre>
      );
    }
    return renderTextBlock(b.content, bi);
  });
}

function renderTextBlock(text, blockKey) {
  const lines = text.split("\n");
  const elements = [];
  let tableBuf = null;

  const flushTable = () => {
    if (!tableBuf) return;
    const [headerLine, , ...rows] = tableBuf;
    const headers = headerLine
      .split("|")
      .map((c) => c.trim())
      .filter((c, i, a) => !(i === 0 && c === "") && !(i === a.length - 1 && c === ""));
    const rowCells = rows.map((r) =>
      r
        .split("|")
        .map((c) => c.trim())
        .filter((c, i, a) => !(i === 0 && c === "") && !(i === a.length - 1 && c === ""))
    );
    elements.push(
      <table key={`${blockKey}-tbl-${elements.length}`} className="md-table">
        <thead>
          <tr>
            {headers.map((h, i) => (
              <th key={i} dangerouslySetInnerHTML={{ __html: inline(h) }} />
            ))}
          </tr>
        </thead>
        <tbody>
          {rowCells.map((row, ri) => (
            <tr key={ri}>
              {row.map((c, ci) => (
                <td key={ci} dangerouslySetInnerHTML={{ __html: inline(c) }} />
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    );
    tableBuf = null;
  };

  lines.forEach((line, i) => {
    const isTableRow = /^\s*\|.*\|\s*$/.test(line);
    if (isTableRow) {
      tableBuf = tableBuf || [];
      tableBuf.push(line);
      return;
    }
    flushTable();

    const key = `${blockKey}-${i}`;
    if (line.startsWith("# ")) {
      elements.push(
        <h2 key={key} dangerouslySetInnerHTML={{ __html: inline(line.slice(2)) }} />
      );
      return;
    }
    if (line.startsWith("## ")) {
      elements.push(
        <h3 key={key} dangerouslySetInnerHTML={{ __html: inline(line.slice(3)) }} />
      );
      return;
    }
    if (line.startsWith("### ")) {
      elements.push(
        <h4 key={key} dangerouslySetInnerHTML={{ __html: inline(line.slice(4)) }} />
      );
      return;
    }
    if (/^\s*[-*]\s+/.test(line)) {
      elements.push(
        <div
          key={key}
          className="bullet"
          dangerouslySetInnerHTML={{
            __html: "• " + inline(line.replace(/^\s*[-*]\s+/, "")),
          }}
        />
      );
      return;
    }
    if (line.trim() === "") {
      elements.push(<br key={key} />);
      return;
    }
    elements.push(
      <div
        key={key}
        className="line"
        dangerouslySetInnerHTML={{ __html: inline(line) }}
      />
    );
  });
  flushTable();
  return <React.Fragment key={blockKey}>{elements}</React.Fragment>;
}
