"use client";

import React from "react";

interface SafeMarkdownProps {
  content: string;
  className?: string;
}

/**
 * Safe, lightweight Markdown renderer for AI Grama Sahayak.
 * Formats headings, bold, italic, inline code, bullet lists, numbered lists,
 * and converts links/URLs into safe external clickable links with target="_blank"
 * and rel="noopener noreferrer".
 *
 * STRICTLY PREVENTS ARBITRARY HTML EXECUTION:
 * Never uses dangerouslySetInnerHTML; produces typed React elements.
 */
export default function SafeMarkdown({ content, className = "markdown-body" }: SafeMarkdownProps) {
  if (!content) return null;

  // Split content into blocks by double newlines or paragraph boundaries
  const rawBlocks = content.split(/\n\s*\n/);

  return (
    <div className={className}>
      {rawBlocks.map((block, blockIdx) => {
        const trimmed = block.trim();
        if (!trimmed) return null;

        // Heading 3: ### Heading
        if (trimmed.startsWith("### ")) {
          return (
            <h4 key={blockIdx} className="md-h3">
              {renderInline(trimmed.slice(4))}
            </h4>
          );
        }

        // Heading 2: ## Heading
        if (trimmed.startsWith("## ")) {
          return (
            <h3 key={blockIdx} className="md-h2">
              {renderInline(trimmed.slice(3))}
            </h3>
          );
        }

        // Heading 1: # Heading
        if (trimmed.startsWith("# ")) {
          return (
            <h2 key={blockIdx} className="md-h1">
              {renderInline(trimmed.slice(2))}
            </h2>
          );
        }

        const lines = trimmed.split("\n");

        // Check if all lines are unordered list items (* or -)
        const isBulletList = lines.every((line) => /^\s*[-*•]\s+/.test(line));
        if (isBulletList) {
          return (
            <ul key={blockIdx} className="md-ul">
              {lines.map((line, lineIdx) => {
                const itemText = line.replace(/^\s*[-*•]\s+/, "");
                return (
                  <li key={lineIdx} className="md-li">
                    {renderInline(itemText)}
                  </li>
                );
              })}
            </ul>
          );
        }

        // Check if all lines are numbered list items (1. , 2. )
        const isNumberedList = lines.every((line) => /^\s*\d+[\.)]\s+/.test(line));
        if (isNumberedList) {
          return (
            <ol key={blockIdx} className="md-ol">
              {lines.map((line, lineIdx) => {
                const itemText = line.replace(/^\s*\d+[\.)]\s+/, "");
                return (
                  <li key={lineIdx} className="md-li">
                    {renderInline(itemText)}
                  </li>
                );
              })}
            </ol>
          );
        }

        // Normal paragraph with potential intra-block line breaks
        return (
          <p key={blockIdx} className="md-p">
            {lines.map((line, lineIdx) => (
              <React.Fragment key={lineIdx}>
                {lineIdx > 0 && <br />}
                {renderInline(line)}
              </React.Fragment>
            ))}
          </p>
        );
      })}
    </div>
  );
}

/**
 * Renders inline markdown tokens:
 * - Bold: **text** or __text__
 * - Italic: *text* or _text_
 * - Inline Code: `code`
 * - Markdown Links: [label](url)
 * - Standalone URLs: https://... or http://...
 */
function renderInline(text: string): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  let remaining = text;
  let keyCounter = 0;

  // Regex pattern matching inline elements
  // Group 1 & 2: Markdown link [label](url)
  // Group 3: Bold **text**
  // Group 4: Inline code `code`
  // Group 5: Raw URL http:// or https://
  const inlineRegex =
    /\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)|\*\*([^*]+)\*\*|`([^`]+)`|(https?:\/\/[^\s\)]+)/;

  while (remaining.length > 0) {
    const match = remaining.match(inlineRegex);
    if (!match || match.index === undefined) {
      nodes.push(remaining);
      break;
    }

    // Add plain text before match
    if (match.index > 0) {
      nodes.push(remaining.substring(0, match.index));
    }

    const [fullMatch, linkText, linkUrl, boldText, codeText, rawUrl] = match;

    if (linkText && linkUrl) {
      // Markdown link
      nodes.push(
        <a
          key={`link-${keyCounter++}`}
          href={sanitizeUrl(linkUrl)}
          target="_blank"
          rel="noopener noreferrer"
          className="md-link"
        >
          {linkText}
        </a>
      );
    } else if (boldText) {
      // Bold text
      nodes.push(
        <strong key={`bold-${keyCounter++}`} className="md-strong">
          {boldText}
        </strong>
      );
    } else if (codeText) {
      // Inline code
      nodes.push(
        <code key={`code-${keyCounter++}`} className="md-code">
          {codeText}
        </code>
      );
    } else if (rawUrl) {
      // Standalone URL
      nodes.push(
        <a
          key={`rawurl-${keyCounter++}`}
          href={sanitizeUrl(rawUrl)}
          target="_blank"
          rel="noopener noreferrer"
          className="md-link"
        >
          {truncateUrl(rawUrl)}
        </a>
      );
    } else {
      nodes.push(fullMatch);
    }

    remaining = remaining.substring(match.index + fullMatch.length);
  }

  return nodes;
}

/**
 * Sanitizes URLs to allow only safe http/https schemes.
 */
function sanitizeUrl(url: string): string {
  try {
    const parsed = new URL(url);
    if (parsed.protocol === "http:" || parsed.protocol === "https:") {
      return url;
    }
  } catch {
    // Ignore invalid URLs
  }
  return "#";
}

/**
 * Shortens long URLs for clean display in citizen chat.
 */
function truncateUrl(url: string): string {
  try {
    const parsed = new URL(url);
    const domain = parsed.hostname.replace(/^www\./, "");
    if (parsed.pathname.length > 15) {
      return `${domain}${parsed.pathname.slice(0, 15)}...`;
    }
    return `${domain}${parsed.pathname}`;
  } catch {
    return url.length > 35 ? `${url.slice(0, 32)}...` : url;
  }
}
