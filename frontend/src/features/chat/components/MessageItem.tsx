import React, {
  useState,
  useMemo,
  memo,
  useCallback,
  useRef,
  useEffect,
  Suspense,
} from "react";
import { Brain, Sparkles, Copy, Check, RefreshCw, Pencil } from "lucide-react";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import {
  oneDark,
  oneLight,
} from "react-syntax-highlighter/dist/esm/styles/prism";
import type { ChatMessage } from "@/types/api";
import { useAuthStore } from "@/store/authStore";
import { useSettingsStore } from "@/store/settingsStore";

// ─── Types ───────────────────────────────────────────────────────────────────

interface Citation {
  source_id: string;
  score: number;
  name?: string;
}

interface MessageItemProps {
  message: ChatMessage;
  isStreaming?: boolean;
  citations?: Citation[];
  onRegenerate?: () => void;
  suggestedQuestions?: string[];
  onQuestionClick?: (question: string) => void;
  onEdit?: (content: string) => void;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function getUserInitials(name: string | undefined): string {
  if (!name) return "U";
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return name.slice(0, 2).toUpperCase();
}

function useCopy(text: string, timeout = 2000) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), timeout);
  };
  return { copied, copy };
}

// ─── Callout config ───────────────────────────────────────────────────────────

interface CalloutConfig {
  emoji: string;
  label: string;
  cssClass: string;
  iconColor: string;
}

const CALLOUT_MAP: Record<string, CalloutConfig> = {
  "💡": {
    emoji: "💡",
    label: "Tip",
    cssClass: "callout-tip",
    iconColor: "#10b981",
  },
  "⚠️": {
    emoji: "⚠️",
    label: "Warning",
    cssClass: "callout-warning",
    iconColor: "#f59e0b",
  },
  "📝": {
    emoji: "📝",
    label: "Note",
    cssClass: "callout-note",
    iconColor: "#60a5fa",
  },
  "✅": {
    emoji: "✅",
    label: "Success",
    cssClass: "callout-tip",
    iconColor: "#10b981",
  },
  "❌": {
    emoji: "❌",
    label: "Error",
    cssClass: "callout-error",
    iconColor: "#f43f5e",
  },
  "🔥": {
    emoji: "🔥",
    label: "Hot",
    cssClass: "callout-warning",
    iconColor: "#f59e0b",
  },
  "💬": {
    emoji: "💬",
    label: "Note",
    cssClass: "callout-info",
    iconColor: "hsl(var(--primary))",
  },
};

function detectCallout(children: React.ReactNode): CalloutConfig | null {
  // Walk children to find the first text-like element
  const firstChild = React.Children.toArray(children)[0];
  let text = "";

  if (typeof firstChild === "string") {
    text = firstChild;
  } else if (React.isValidElement(firstChild)) {
    // Could be a <p> wrapping the content
    const pChildren = React.Children.toArray(
      (firstChild as React.ReactElement<any>).props.children,
    );
    const firstInP = pChildren[0];
    if (typeof firstInP === "string") {
      text = firstInP;
    } else if (React.isValidElement(firstInP)) {
      // Could be <strong> wrapping the emoji
      const strongChildren = React.Children.toArray(
        (firstInP as React.ReactElement<any>).props.children,
      );
      text = String(strongChildren[0] ?? "");
    }
  }

  for (const emoji of Object.keys(CALLOUT_MAP)) {
    if (text.includes(emoji)) return CALLOUT_MAP[emoji];
  }
  return null;
}

// ─── Mermaid Placeholder ──────────────────────────────────────────────────────

const MermaidBlock = memo(function MermaidBlock({ code }: { code: string }) {
  const { copied, copy } = useCopy(code);
  return (
    <div className="my-3 rounded-xl overflow-hidden border border-primary/15 shadow-lg bg-background">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-primary uppercase tracking-wider">
            ⬡ Diagram
          </span>
        </div>
        <button
          onClick={copy}
          className="flex items-center gap-1.5 text-[11px] font-mono text-muted-foreground hover:text-primary transition-colors active:scale-[0.98]"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-green-400" /> Copied!
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" /> Copy
            </>
          )}
        </button>
      </div>
      <pre className="text-[0.75rem] text-muted-foreground font-mono leading-relaxed p-4 whitespace-pre overflow-x-auto">
        {code}
      </pre>
      <div className="px-4 py-2 border-t border-border text-[10px] text-muted-foreground font-mono">
        Mermaid diagram — render with a Mermaid-compatible viewer
      </div>
    </div>
  );
});

// ─── Code Block ──────────────────────────────────────────────────────────────

const CodeBlock = memo(function CodeBlock({
  className,
  children,
}: {
  className?: string;
  children?: React.ReactNode;
}) {
  const theme = useSettingsStore((s) => s.theme);
  const isDark =
    theme === "dark" ||
    (theme === "system" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches);

  const match = /language-(\w+)/.exec(className || "");
  const lang = match ? match[1] : "text";
  let code = String(children).replace(/\n$/, "");

  // Auto-format JSON
  if (lang === "json") {
    try {
      const parsed = JSON.parse(code);
      code = JSON.stringify(parsed, null, 2);
    } catch (e) {
      // Keep original code if it's not valid JSON yet
    }
  }

  const { copied, copy } = useCopy(code);

  // Render Mermaid diagrams as a styled placeholder
  if (lang === "mermaid") {
    return <MermaidBlock code={code} />;
  }

  return (
    <div className="my-3 rounded-xl overflow-hidden border border-border shadow-lg">
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-background border-b border-border">
        <div className="flex items-center gap-2">
          {/* Traffic-light dots */}
          <span className="w-2.5 h-2.5 rounded-full bg-terminal-red" />
          <span className="w-2.5 h-2.5 rounded-full bg-terminal-yellow" />
          <span className="w-2.5 h-2.5 rounded-full bg-terminal-green" />
          <span className="ml-2 text-[11px] font-mono text-muted-foreground select-none">
            {lang}
          </span>
        </div>
        <button
          onClick={copy}
          className="flex items-center gap-1.5 text-[11px] font-mono text-muted-foreground hover:text-primary transition-colors active:scale-[0.98]"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-green-400" /> Copied!
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" /> Copy
            </>
          )}
        </button>
      </div>
      {/* Code body */}
      <SyntaxHighlighter
        style={(isDark ? oneDark : oneLight) as any}
        language={lang}
        PreTag="div"
        codeTagProps={{
          style: { backgroundColor: "transparent", border: "none" },
        }}
        showLineNumbers={code.split("\n").length > 4}
        wrapLongLines={false}
        lineProps={{
          style: {
            border: "none",
            borderBottom: "none",
            background: "transparent",
            boxShadow: "none",
          },
        }}
        customStyle={{
          margin: 0,
          borderRadius: 0,
          fontSize: "0.78rem",
          lineHeight: "1.65",
          background: "transparent",
          padding: "1rem 1.25rem",
          border: "none",
        }}
        lineNumberStyle={{
          color: "hsl(var(--muted-foreground))",
          minWidth: "2.2em",
          paddingRight: "1em",
          userSelect: "none",
          borderRight: "none",
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
});

// ─── Checkbox List Item ───────────────────────────────────────────────────────

function CheckboxListItem({ children }: { children: React.ReactNode }) {
  // remark-gfm injects an <input type="checkbox"> as the first child of task list items.
  // We strip it and render a styled custom checkbox instead.
  let isChecked = false;
  const processedChildren = React.Children.map(children, (child) => {
    if (
      React.isValidElement(child) &&
      (child as React.ReactElement<any>).type === "input"
    ) {
      isChecked = !!(child as React.ReactElement<any>).props.checked;
      return null; // remove the raw <input>; we'll render our own
    }
    return child;
  });

  return (
    <li className="flex items-start gap-2 leading-[1.7] pl-0 list-none">
      <span
        className={cn(
          "mt-[0.28em] w-4 h-4 shrink-0 rounded border flex items-center justify-center transition-colors",
          isChecked
            ? "bg-primary border-primary"
            : "border-border bg-transparent",
        )}
      >
        {isChecked && (
          <svg
            viewBox="0 0 10 8"
            className="w-2.5 h-2.5 fill-none stroke-background stroke-[1.8]"
          >
            <path
              d="M1 4l2.5 2.5L9 1"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
      </span>
      <span
        className={cn(
          "flex-1",
          isChecked && "line-through text-muted-foreground",
        )}
      >
        {processedChildren}
      </span>
    </li>
  );
}

// ─── Markdown Components ──────────────────────────────────────────────────────

function useMarkdownComponents(): React.ComponentProps<
  typeof ReactMarkdown
>["components"] {
  return useMemo(
    () => ({
      // Code: inline vs block
      code({ className, children, ...props }: any) {
        const isBlock = !!className;
        if (!isBlock) {
          // Inline code
          return (
            <code
              className="font-mono text-[0.82em] bg-primary/10 text-primary border border-primary/20 px-[0.4em] py-[0.12em] rounded-[0.3em] whitespace-nowrap"
              {...props}
            >
              {children}
            </code>
          );
        }
        return <CodeBlock className={className}>{children}</CodeBlock>;
      },

      // Pre: wraps code blocks — let CodeBlock handle styling
      pre({ children }) {
        return <>{children}</>;
      },

      // Paragraphs
      p({ children }) {
        return (
          <p className="mb-[0.75em] last:mb-0 leading-[1.75]">{children}</p>
        );
      },

      // Headings
      h1: ({ children }) => (
        <h1 className="text-[1.35em] font-semibold text-foreground font-headline mt-[1.1em] mb-[0.4em] first:mt-0">
          {children}
        </h1>
      ),
      h2: ({ children }) => (
        <h2 className="text-[1.18em] font-semibold text-foreground font-headline mt-[1.1em] mb-[0.4em] pb-[0.25em] border-b border-border first:mt-0">
          {children}
        </h2>
      ),
      h3: ({ children }) => (
        <h3 className="text-[1.05em] font-semibold text-foreground font-headline mt-[1.1em] mb-[0.4em] first:mt-0">
          {children}
        </h3>
      ),
      h4: ({ children }) => (
        <h4 className="text-[0.95em] font-semibold text-foreground font-headline mt-[1em] mb-[0.3em] first:mt-0">
          {children}
        </h4>
      ),

      // Lists — with checkbox support
      ul: ({ children }) => (
        <ul className="pl-[1.4em] my-[0.5em] mb-[0.75em] space-y-[0.2em] marker:text-primary list-disc">
          {children}
        </ul>
      ),
      ol: ({ children }) => (
        <ol className="list-decimal pl-[1.4em] my-[0.5em] mb-[0.75em] space-y-[0.2em] marker:text-primary">
          {children}
        </ol>
      ),
      li({ children, ...props }: any) {
        // Detect GFM task list items via a child input[type=checkbox]
        const isTask =
          (props.className ?? "").includes("task-list-item") ||
          React.Children.toArray(children).some(
            (c) =>
              React.isValidElement(c) &&
              (c as React.ReactElement<any>).type === "input",
          );
        if (isTask) return <CheckboxListItem>{children}</CheckboxListItem>;
        return <li className="leading-[1.7] pl-[0.2em]">{children}</li>;
      },

      // Blockquote — with callout detection
      blockquote: ({ children }) => {
        const callout = detectCallout(children);
        if (callout) {
          return (
            <div
              className={cn(
                "my-[0.75em] px-[0.9em] py-[0.7em] rounded-[0.5rem] not-italic",
                callout.cssClass,
              )}
            >
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-[1em]">{callout.emoji}</span>
                <span
                  className="text-[0.72em] font-semibold uppercase tracking-wider font-mono"
                  style={{ color: callout.iconColor }}
                >
                  {callout.label}
                </span>
              </div>
              <div className="text-[0.9em] leading-[1.7] text-foreground/80">
                {children}
              </div>
            </div>
          );
        }
        // Default blockquote
        return (
          <blockquote className="border-l-[3px] border-primary bg-primary/5 italic text-muted-foreground my-[0.75em] px-[0.9em] py-[0.6em] rounded-r-[0.4rem]">
            {children}
          </blockquote>
        );
      },

      // Table — overflow-scrollable with sticky header
      table: ({ children }) => (
        <div className="my-[0.75em] overflow-x-auto rounded-lg border border-border">
          <table className="w-full border-collapse text-[0.82em]">
            {children}
          </table>
        </div>
      ),
      thead: ({ children }) => (
        <thead className="bg-primary/10 sticky top-0 z-10">{children}</thead>
      ),
      th: ({ children }) => (
        <th className="text-left font-semibold text-primary px-[0.9em] py-[0.55em] border-b border-border whitespace-nowrap">
          {children}
        </th>
      ),
      td: ({ children }) => (
        <td className="px-[0.9em] py-[0.45em] border-b border-border align-top last:border-b-0">
          {children}
        </td>
      ),
      tr: ({ children }) => (
        <tr className="hover:bg-foreground/5 transition-colors">{children}</tr>
      ),

      // HR
      hr: () => <hr className="border-none border-t border-border my-[1em]" />,

      // Links
      a: ({ href, children }) => (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary underline underline-offset-[2px] decoration-primary/40 hover:text-primary/80 hover:decoration-primary/80 transition-colors"
        >
          {children}
        </a>
      ),

      // Strong / em / del
      strong: ({ children }) => (
        <strong className="font-semibold text-foreground">{children}</strong>
      ),
      em: ({ children }) => (
        <em className="italic text-foreground/80">{children}</em>
      ),
      del: ({ children }) => (
        <del className="line-through text-muted-foreground">{children}</del>
      ),
    }),
    [],
  );
}

// ─── Throttled content for streaming ──────────────────────────────────────────

/**
 * During streaming, LLM tokens arrive many times per second. Re-parsing the
 * full content through ReactMarkdown + remark-gfm on every single token causes
 * noticeable jank. This hook throttles the content updates so the markdown
 * renderer only re-parses at ~12 fps (every 80ms), which feels real-time but
 * avoids excessive work.
 */
function useDeferredContent(content: string, isStreaming: boolean): string {
  const [deferred, setDeferred] = useState(content);
  const lastUpdate = useRef(0);
  const rafId = useRef<number>(0);

  useEffect(() => {
    if (!isStreaming) {
      // When streaming stops, immediately show the final content
      setDeferred(content);
      return;
    }

    const now = performance.now();
    const elapsed = now - lastUpdate.current;

    if (elapsed >= 80) {
      // Enough time has passed — update immediately
      lastUpdate.current = now;
      setDeferred(content);
    } else {
      // Schedule an update after the remaining time
      cancelAnimationFrame(rafId.current);
      rafId.current = requestAnimationFrame(() => {
        lastUpdate.current = performance.now();
        setDeferred(content);
      });
    }

    return () => cancelAnimationFrame(rafId.current);
  }, [content, isStreaming]);

  return deferred;
}

// ─── Streaming Cursor ─────────────────────────────────────────────────────────

function StreamingCursor() {
  return (
    <span
      className="inline-flex gap-0.5 ml-1 select-none items-end pb-0.5"
      aria-label="Generating..."
    >
      <span
        className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce"
        style={{ animationDelay: "0ms" }}
      />
      <span
        className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce"
        style={{ animationDelay: "160ms" }}
      />
      <span
        className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce"
        style={{ animationDelay: "320ms" }}
      />
    </span>
  );
}

// ─── Follow-up Chips ──────────────────────────────────────────────────────────

interface FollowUpChipsProps {
  questions: string[];
  onQuestionClick: (q: string) => void;
}

function FollowUpChips({ questions, onQuestionClick }: FollowUpChipsProps) {
  if (!questions.length) return null;
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      <span className="text-[10px] text-muted-foreground font-mono self-center mr-1 shrink-0">
        Follow-up:
      </span>
      {questions.map((q, i) => (
        <button
          key={i}
          onClick={() => onQuestionClick(q)}
          className="text-[11px] px-3 py-1.5 rounded-full border border-primary/20 bg-primary/5 text-primary hover:bg-primary/15 hover:border-primary/40 transition-all hover:-translate-y-px active:scale-[0.98] max-w-[260px] truncate"
          title={q}
        >
          {q}
        </button>
      ))}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export const MessageItem = memo(function MessageItem({
  message,
  isStreaming,
  citations,
  onRegenerate,
  suggestedQuestions,
  onQuestionClick,
  onEdit,
}: MessageItemProps) {
  const user = useAuthStore((s) => s.user);
  const isUser = message.role === "user";
  const { copied, copy } = useCopy(message.content);
  const markdownComponents = useMarkdownComponents();
  const deferredContent = useDeferredContent(message.content, !!isStreaming);

  const handleQuestionClick = useCallback(
    (q: string) => onQuestionClick?.(q),
    [onQuestionClick],
  );

  return (
    <div
      className={cn(
        "flex gap-3 items-start animate-fade-in group",
        isUser
          ? "ml-auto flex-row-reverse max-w-[80%]"
          : "mr-auto max-w-[90%] w-full",
      )}
    >
      {/* ── Avatar ── */}
      <div
        className={cn(
          "w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-xs font-bold shadow-sm mt-0.5",
          isUser
            ? "bg-primary/10 text-primary border border-primary/20"
            : "from-primary/30 to-primary/10 text-primary border border-primary/25",
        )}
      >
        {isUser ? (
          getUserInitials(user?.username)
        ) : (
          // <Brain className="w-4 h-4" />
          <img
            src="/thinkora_logo_icon.png"
            alt="Thinkora Icon"
            className="w-7 h-7 object-contain drop-shadow-sm"
          />
        )}
      </div>

      {/* ── Content column ── */}
      <div
        className={cn(
          "flex flex-col gap-1.5",
          isUser ? "items-end" : "items-start w-full",
        )}
      >
        {/* ── Bubble ── */}
        <div
          className={cn(
            "relative text-foreground shadow-sm",
            isUser
              ? "bg-primary/10 border border-primary/20 rounded-2xl rounded-tr-sm px-4 py-3"
              : "bg-card border border-border rounded-2xl rounded-tl-sm px-5 py-4 w-full backdrop-blur-sm",
          )}
        >
          {isUser ? (
            // User message: plain pre-wrap text
            <p className="text-sm leading-relaxed whitespace-pre-wrap break-words text-foreground">
              {message.content}
            </p>
          ) : isStreaming ? (
            // AI message during streaming: render markdown in real-time so users
            // see formatted headings, bold, lists, code blocks, etc. as content arrives.
            // Wrapped in Suspense for react-markdown v10 compatibility. The fallback
            // shows raw text, but only flashes briefly on the very first chunk.
            <div className="prose-chat">
              {message.content ? (
                <Suspense
                  fallback={
                    <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                      {message.content}
                    </p>
                  }
                >
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={markdownComponents}
                  >
                    {deferredContent}
                  </ReactMarkdown>
                </Suspense>
              ) : (
                <p className="text-sm leading-relaxed">{"\u200b"}</p>
              )}
              <StreamingCursor />
            </div>
          ) : (
            // AI message finalized: full markdown rendering.
            // Wrapped in Suspense because react-markdown v10 uses React 19's use() hook
            // which suspends on first render. The fallback shows plain text while parsing.
            <div className="prose-chat">
              <Suspense
                fallback={
                  <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                    {message.content}
                  </p>
                }
              >
                <ReactMarkdown
                  key={message.id}
                  remarkPlugins={[remarkGfm]}
                  components={markdownComponents}
                >
                  {message.content}
                </ReactMarkdown>
              </Suspense>
            </div>
          )}
        </div>

        {/* ── User message action row (edit) ── */}
        {isUser && !isStreaming && message.content && onEdit && (
          <div className="flex items-center gap-2 mr-1 opacity-0 group-hover:opacity-100 transition-opacity justify-end">
            <button
              onClick={() => onEdit(message.content)}
              className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
              title="Edit message"
            >
              <Pencil className="w-3 h-3" />
              <span>Edit</span>
            </button>
          </div>
        )}

        {/* ── Action row (copy, regenerate) ── */}
        {!isUser && !isStreaming && message.content && (
          <div className="flex items-center gap-2 ml-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={copy}
              className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-3 h-3 text-green-400" />
                  <span className="text-green-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  <span>Copy</span>
                </>
              )}
            </button>

            {onRegenerate && (
              <button
                onClick={onRegenerate}
                className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
                title="Regenerate response"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Regenerate</span>
              </button>
            )}
          </div>
        )}

        {/* ── Follow-up chips ── */}
        {!isUser &&
          !isStreaming &&
          suggestedQuestions &&
          suggestedQuestions.length > 0 &&
          onQuestionClick && (
            <FollowUpChips
              questions={suggestedQuestions}
              onQuestionClick={handleQuestionClick}
            />
          )}

        {/* ── Citations ── */}
        {citations && citations.length > 0 && (
          <div className="flex flex-wrap gap-1.5 items-center mt-0.5">
            <span className="text-[10px] text-muted-foreground font-mono">
              Sources:
            </span>
            {citations.map((c, i) => (
              <span
                key={`${i}-${c.source_id}`}
                title={`Score: ${c.score.toFixed(3)}`}
                className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-md bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 transition-colors cursor-help"
              >
                <Sparkles className="w-2.5 h-2.5 shrink-0" />
                {c.name
                  ? c.name.length > 30
                    ? c.name.slice(0, 28) + "…"
                    : c.name
                  : `Source ${i + 1}`}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
});
