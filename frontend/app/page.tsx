"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ReactNode, useEffect, useMemo, useState } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

type Mode = "hybrid" | "corpus_only";

type SearchSource = {
  case_name: string;
  citation: string;
  court: string;
  year: number;
  summary: string;
  relevance_score: number;
  url: string;
};

type SearchResponse = {
  answer: string;
  sources: SearchSource[];
  mode: Mode;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  sources?: SearchSource[];
};

const samplePrompts = [
  "Summarize Miranda v. Arizona using the IRAC format.",
  "How have courts applied the strict scrutiny test in affirmative action cases?",
  "Explain the current limits of qualified immunity for police officers.",
  "Compare the holdings of Roe v. Wade and Dobbs v. Jackson Women’s Health Organization.",
];

const researchPillars = [
  { label: "Corpus depth", value: "Landmark SCOTUS + seeded library" },
  { label: "Web recall", value: "Legal web search + authority filters" },
  { label: "LLM reasoning", value: "IRAC + citation-first prompting" },
];

const modeOptions: { value: Mode; label: string; description: string }[] = [
  {
    value: "hybrid",
    label: "Hybrid evidence",
    description: "Corpus + web when confidence dips",
  },
  {
    value: "corpus_only",
    label: "Corpus only",
    description: "Faster answers from indexed matter",
  },
];

const formatTimestamp = (date: Date) =>
  new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
  }).format(date);

const resolveSourceUrl = (url: string) => {
  if (!url) return "#";
  if (url.startsWith("http")) return url;
  return `${API_BASE_URL}${url.startsWith("/") ? url : `/${url}`}`;
};

const HeroIcon = () => (
  <svg
    viewBox="0 0 24 24"
    aria-hidden="true"
    className="h-5 w-5 text-indigo-300"
  >
    <path
      d="M12 2 14.8 8.4 22 9.2 16.8 13.8 18.1 21 12 17.7 5.9 21 7.2 13.8 2 9.2 9.2 8.4 12 2Z"
      fill="currentColor"
    />
  </svg>
);

const SearchIcon = () => (
  <svg
    viewBox="0 0 24 24"
    aria-hidden="true"
    className="h-5 w-5 text-slate-300"
  >
    <path
      d="M11 3a8 8 0 1 1 0 16c-1.8 0-3.4-.6-4.8-1.6l-3.1 3a1 1 0 0 1-1.4-1.4l3-3.1A8 8 0 0 1 11 3Zm0 2a6 6 0 1 0 0 12 6 6 0 0 0 0-12Z"
      fill="currentColor"
    />
  </svg>
);

const ShieldIcon = () => (
  <svg
    viewBox="0 0 24 24"
    aria-hidden="true"
    className="h-5 w-5 text-emerald-300"
  >
    <path
      d="M12 3 4 6v5c0 5 3.4 9.7 8 11 4.6-1.3 8-6 8-11V6l-8-3Zm0 2.2 6 2.2v3.6c0 4-2.6 7.6-6 8.8-3.4-1.2-6-4.8-6-8.8V7.4l6-2.2Zm0 3.8a3 3 0 0 0-3 3c0 2 3 5 3 5s3-3 3-5a3 3 0 0 0-3-3Z"
      fill="currentColor"
    />
  </svg>
);

const markdownComponents = {
  h1: ({ children }: { children?: ReactNode }) => (
    <h2 className="text-2xl font-semibold text-white">{children}</h2>
  ),
  h2: ({ children }: { children?: ReactNode }) => (
    <h3 className="text-xl font-semibold text-white">{children}</h3>
  ),
  h3: ({ children }: { children?: ReactNode }) => (
    <h4 className="text-lg font-semibold text-white">{children}</h4>
  ),
  p: ({ children }: { children?: ReactNode }) => (
    <p className="text-base text-slate-100">{children}</p>
  ),
  strong: ({ children }: { children?: ReactNode }) => (
    <strong className="font-semibold text-white">{children}</strong>
  ),
  em: ({ children }: { children?: ReactNode }) => (
    <em className="text-slate-200">{children}</em>
  ),
  ul: ({ children }: { children?: ReactNode }) => (
    <ul className="ml-6 list-disc space-y-1 text-base text-slate-100">
      {children}
    </ul>
  ),
  ol: ({ children }: { children?: ReactNode }) => (
    <ol className="ml-6 list-decimal space-y-1 text-base text-slate-100">
      {children}
    </ol>
  ),
  li: ({ children }: { children?: ReactNode }) => (
    <li className="text-base text-slate-100">{children}</li>
  ),
  blockquote: ({ children }: { children?: ReactNode }) => (
    <blockquote className="border-l-2 border-indigo-400/60 pl-4 text-slate-200">
      {children}
    </blockquote>
  ),
  code: ({ children }: { children?: ReactNode }) => (
    <code className="rounded-md bg-slate-800 px-1.5 py-0.5 text-sm text-amber-200">
      {children}
    </code>
  ),
  a: ({ href, children }: { href?: string; children?: ReactNode }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="text-indigo-300 underline decoration-dotted underline-offset-4 hover:text-indigo-200"
    >
      {children}
    </a>
  ),
};

export default function Home() {
  const [mode, setMode] = useState<Mode>("hybrid");
  const [inputValue, setInputValue] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Ali's Legal Assistant is online. Ask me for holdings, historic reasoning, or synthesize opposing arguments—every answer is grounded in cited authority.",
      timestamp: formatTimestamp(new Date()),
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [sources, setSources] = useState<SearchSource[]>([]);
  const [apiStatus, setApiStatus] = useState<"checking" | "online" | "offline">(
    "checking",
  );

  useEffect(() => {
    let mounted = true;
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/health`, {
          cache: "no-store",
        });
        if (!mounted) return;
        setApiStatus(res.ok ? "online" : "offline");
      } catch {
        if (mounted) {
          setApiStatus("offline");
        }
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 20000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const averageScore = useMemo(() => {
    if (!sources.length) return null;
    const avg =
      sources.reduce((acc, item) => acc + (item.relevance_score ?? 0), 0) /
      sources.length;
    return Math.round(avg * 100);
  }, [sources]);

  const latestCourts = useMemo(
    () =>
      sources
        .map((source) => source.court)
        .filter((value, index, list) => value && list.indexOf(value) === index)
        .slice(0, 3),
    [sources],
  );

  const sendQuery = async (rawQuery: string) => {
    const trimmed = rawQuery.trim();
    if (!trimmed || isLoading) return;

    const timestamp = new Date();
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: trimmed,
      timestamp: formatTimestamp(timestamp),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setErrorMessage(null);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/search/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: trimmed,
          mode,
          limit: 6,
        }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail || "Search failed. Try again shortly.");
      }

      const data: SearchResponse = await response.json();

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: data.answer,
        timestamp: formatTimestamp(new Date()),
        sources: data.sources,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setSources(data.sources || []);
    } catch (error) {
      const fallbackMessage: Message = {
        id: `assistant-error-${Date.now()}`,
        role: "assistant",
        content:
          error instanceof Error
            ? error.message
            : "Something went wrong while contacting the research API.",
        timestamp: formatTimestamp(new Date()),
      };
      setMessages((prev) => [...prev, fallbackMessage]);
      setErrorMessage("Could not reach the backend. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    sendQuery(inputValue);
  };

  const statusLabel =
    apiStatus === "online"
      ? "Backend online"
      : apiStatus === "offline"
        ? "Backend unreachable"
        : "Checking status";

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-8 text-white sm:px-6 lg:px-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <header className="rounded-3xl border border-white/10 bg-slate-900/60 p-6 shadow-[0_0_60px_rgba(59,130,246,0.15)] backdrop-blur">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-4">
              <div className="rounded-2xl bg-indigo-500/20 p-3">
                <HeroIcon />
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-300">
                  Legal Assistant
                </p>
                <h1 className="mt-1 text-2xl font-semibold leading-tight text-white sm:text-3xl">
                  Ali's Legal Assistant
                </h1>
                <p className="mt-2 text-sm text-slate-400">
                  Hybrid RAG assistant for briefs, motions, and oral argument
                  prep. Grounded reasoning with transparent citations.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div
                className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium ${
                  apiStatus === "online"
                    ? "bg-emerald-500/10 text-emerald-200"
                    : apiStatus === "offline"
                      ? "bg-rose-500/10 text-rose-200"
                      : "bg-slate-500/10 text-slate-300"
                }`}
              >
                <span className="relative flex h-2 w-2">
                  <span
                    className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${
                      apiStatus === "online"
                        ? "bg-emerald-400 animate-ping"
                        : apiStatus === "offline"
                          ? "bg-rose-400"
                          : "bg-slate-400 animate-pulse"
                    }`}
                  />
                  <span
                    className={`relative inline-flex h-2 w-2 rounded-full ${
                      apiStatus === "online"
                        ? "bg-emerald-300"
                        : apiStatus === "offline"
                          ? "bg-rose-300"
                          : "bg-slate-300"
                    }`}
                  />
                </span>
                {statusLabel}
              </div>
            </div>
          </div>
          <div className="mt-6 grid gap-3 text-sm text-slate-300 sm:grid-cols-2 lg:grid-cols-3">
            {researchPillars.map((item) => (
              <div
                key={item.label}
                className="rounded-2xl border border-white/5 bg-white/5 px-4 py-3"
              >
                <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                  {item.label}
                </p>
                <p className="mt-1 font-medium text-white">{item.value}</p>
              </div>
            ))}
          </div>
        </header>

        <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(280px,1fr)]">
          <section className="flex flex-col rounded-3xl border border-white/10 bg-slate-900/70 shadow-2xl shadow-indigo-500/5 backdrop-blur">
            <div className="border-b border-white/5 p-6">
              <div className="flex flex-wrap items-center gap-3">
                {modeOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setMode(option.value)}
                    className={`rounded-2xl border px-4 py-3 text-left transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-500 ${
                      mode === option.value
                        ? "border-indigo-400 bg-indigo-500/10 text-white"
                        : "border-white/10 bg-white/5 text-slate-300 hover:border-white/30 hover:text-white"
                    }`}
                  >
                    <p className="text-sm font-semibold">{option.label}</p>
                    <p className="text-xs text-slate-400">
                      {option.description}
                    </p>
                  </button>
                ))}
              </div>
              <div className="mt-5 grid gap-3 md:grid-cols-2">
                {samplePrompts.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    disabled={isLoading}
                    onClick={() => sendQuery(prompt)}
                    className="rounded-2xl border border-white/5 bg-white/5 p-3 text-left text-sm text-slate-300 transition hover:border-white/20 hover:bg-white/10 hover:text-white disabled:opacity-60"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex-1 space-y-6 overflow-y-auto p-6">
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              {isLoading && (
                <div className="flex gap-3">
                  <div className="h-10 w-10 rounded-full bg-indigo-500/20" />
                  <div className="flex-1 rounded-3xl border border-white/5 bg-white/5 p-5">
                    <div className="space-y-3">
                      <div className="h-3 w-2/3 animate-pulse rounded bg-white/10" />
                      <div className="h-3 w-5/6 animate-pulse rounded bg-white/10" />
                      <div className="h-3 w-1/2 animate-pulse rounded bg-white/10" />
                    </div>
                  </div>
                </div>
              )}
              {!isLoading && messages.length === 1 && (
                <div className="rounded-3xl border border-dashed border-white/10 bg-white/5 p-6 text-sm text-slate-400">
                  Ask something specific—Ali's Legal Assistant excels at IRAC summaries,
                  comparing precedent, validating citations, and crafting
                  cross-motions grounded in binding authority.
                </div>
              )}
            </div>

            <form
              onSubmit={handleSubmit}
              className="border-t border-white/5 p-4 sm:p-6"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <div className="relative flex-1">
                  <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2">
                    <SearchIcon />
                  </span>
                  <input
                    className="w-full rounded-2xl border border-white/10 bg-white/5 py-4 pl-12 pr-4 text-base text-white placeholder:text-slate-500 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-400/40"
                    placeholder="Pose a fact pattern, cite precedent, or ask for a synthesis…"
                    value={inputValue}
                    onChange={(event) => setInputValue(event.target.value)}
                    disabled={isLoading}
                  />
                </div>
                <button
                  type="submit"
                  disabled={!inputValue.trim() || isLoading}
                  className="inline-flex items-center justify-center rounded-2xl bg-indigo-500 px-6 py-4 text-base font-semibold text-white shadow shadow-indigo-500/30 transition hover:bg-indigo-400 disabled:opacity-60"
                >
                  {isLoading ? "Researching…" : "Send"}
                </button>
              </div>
              <p className="mt-2 text-xs text-slate-500">
                Responses cite FastAPI backend sources. Always verify before
                filing.
              </p>
              {errorMessage && (
                <p className="mt-2 text-sm text-rose-300">{errorMessage}</p>
              )}
            </form>
          </section>

          <aside className="space-y-6">
            <div className="rounded-3xl border border-white/10 bg-slate-900/60 p-6">
              <div className="flex items-center gap-2 text-sm font-semibold text-white">
                <ShieldIcon />
                Citation telemetry
              </div>
              <div className="mt-4 space-y-4 text-sm text-slate-300">
                <div className="rounded-2xl border border-white/5 bg-white/5 px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                    Avg confidence
                  </p>
                  <p className="mt-2 text-3xl font-semibold text-white">
                    {averageScore ? `${averageScore}%` : "—"}
                  </p>
                </div>
                <div className="rounded-2xl border border-white/5 bg-white/5 px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                    Courts referenced
                  </p>
                  <p className="mt-1 text-base text-white">
                    {latestCourts.length
                      ? latestCourts.join(" · ")
                      : "Awaiting query"}
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-slate-900/60 p-6">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-white">
                  Active authorities
                </p>
                <span className="text-xs text-slate-400">
                  {sources.length ? `${sources.length} cited` : "—"}
                </span>
              </div>
              <div className="mt-4 space-y-4">
                {sources.length === 0 && (
                  <p className="text-sm text-slate-400">
                    Run a query to see cited precedent with pin-ready summaries.
                  </p>
                )}
                {sources.map((source, index) => (
                  <a
                    key={`${source.case_name}-${index}`}
                    href={resolveSourceUrl(source.url)}
                    target="_blank"
                    rel="noreferrer"
                    className="group block rounded-2xl border border-white/5 bg-white/5 p-4 transition hover:border-indigo-400/60 hover:bg-white/10"
                  >
                    <p className="text-xs uppercase tracking-[0.3em] text-indigo-300">
                      Case {index + 1}
                    </p>
                    <p className="mt-2 text-base font-semibold text-white">
                      {source.case_name}
                    </p>
                    <p className="text-sm text-slate-400">{source.citation}</p>
                    <p
                      className="mt-2 text-sm text-slate-300"
                      style={{
                        display: "-webkit-box",
                        WebkitLineClamp: 3,
                        WebkitBoxOrient: "vertical",
                        overflow: "hidden",
                      }}
                    >
                      {source.summary || "Summary not available"}
                    </p>
                    <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                      <span>{source.court}</span>
                      <span>Score {(source.relevance_score || 0).toFixed(2)}</span>
                    </div>
                  </a>
                ))}
              </div>
            </div>

            <div className="rounded-3xl border border-dashed border-white/10 bg-slate-900/40 p-6 text-sm text-slate-400">
              <p className="text-base font-semibold text-white">
                Workflow tips
              </p>
              <ul className="mt-3 space-y-2">
                <li>• Specify the jurisdiction and procedural posture.</li>
                <li>• Ask Ali's Legal Assistant to contrast holdings with modern authority.</li>
                <li>• Provide draft arguments for citation validation.</li>
              </ul>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isAssistant = message.role === "assistant";
  const paragraphs = message.content
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);

  return (
    <div
      className={`flex gap-4 ${isAssistant ? "flex-row" : "flex-row-reverse"}`}
    >
      <div
        className={`flex h-10 w-10 items-center justify-center rounded-full text-sm font-semibold ${
          isAssistant
            ? "bg-indigo-500/20 text-indigo-200"
            : "bg-white text-slate-900"
        }`}
      >
        {isAssistant ? "A" : "You"}
      </div>
      <div className="flex-1">
        <div
          className={`rounded-3xl border p-5 text-sm leading-7 ${
            isAssistant
              ? "border-white/10 bg-white/5"
              : "border-indigo-500/30 bg-indigo-500/10"
          }`}
        >
          <div className="text-xs uppercase tracking-[0.4em] text-slate-500">
            {isAssistant ? "Assistant" : "Researcher"}
          </div>
          <div className="mt-2 space-y-3 text-base text-slate-100">
            {isAssistant ? (
              <div className="space-y-3">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={markdownComponents}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            ) : paragraphs.length > 0 ? (
              paragraphs.map((paragraph, index) => (
                <p key={`${message.id}-${index}`}>{paragraph}</p>
              ))
            ) : (
              message.content
            )}
          </div>
          <p className="mt-4 text-xs text-slate-500">{message.timestamp}</p>
        </div>
        {isAssistant && message.sources && message.sources.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-3">
            {message.sources.map((source, index) => (
              <span
                key={`${message.id}-source-${index}`}
                className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200"
              >
                <span className="text-[10px] uppercase tracking-[0.3em] text-slate-500">
                  #{index + 1}
                </span>
                {source.case_name}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
