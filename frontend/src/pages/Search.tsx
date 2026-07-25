import React, { useState, useDeferredValue } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search as SearchIcon,
  FileText,
  Globe,
  Play,
  StickyNote,
  Layers,
  ArrowRight,
  History,
  Sparkles,
  Loader2,
} from "lucide-react";
import { Layout } from "@/components/layout/Layout";
import { Input } from "@/components/ui/Input";
import { cn } from "@/lib/utils";
import { useSearch } from "@/hooks/useSearch";

interface SearchResult {
  id: string;
  title: string;
  snippet: string;
  type: "pdf" | "url" | "Play" | "note" | "flashcard";
  notebookName: string;
  notebookId: string;
  relevance: number; // Percent
  timestamp: string;
}

export function Search() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState<
    "all" | "pdf" | "url" | "Play" | "note" | "flashcard"
  >("all");

  // Deferred query for debouncing (React 18+)
  const deferredQuery = useDeferredValue(query);
  const { data: searchData, isFetching } = useSearch(deferredQuery);

  // Build results from API or fallback to mocks when no query
  const apiResults: SearchResult[] = (searchData?.results ?? []).map((r, idx) => ({
    id: r.chunk_id,
    title: r.source_name || `Result ${idx + 1}`,
    snippet: r.content.slice(0, 200),
    type: "pdf" as const,
    notebookName: r.notebook_id,
    notebookId: r.notebook_id,
    relevance: Math.round(r.score * 100),
    timestamp: `Score: ${r.score.toFixed(3)}`,
  }));

  const useApiResults = deferredQuery.trim().length >= 2;

  const recentSearches = [
    "Attention Mechanism scaling factor",
    "Positional encoding sine waves",
    "Ollama models local execution",
  ];

  const popularTopics = [
    "Transformer",
    "Multi-Head Attention",
    "BPE Vocabulary",
    "Deep Learning",
  ];

  const allResults: SearchResult[] = [
    {
      id: "r1",
      title: "Attention is All You Need - Page 4",
      snippet:
        "We describe Scaled Dot-Product Attention. The input consists of queries and keys of dimension d_k, and values of dimension d_v.",
      type: "pdf",
      notebookName: "📚 ML Research",
      notebookId: "demo-1",
      relevance: 98,
      timestamp: "Updated 10m ago",
    },
    {
      id: "r2",
      title: "Attention Mechanism Key takeaways (Note)",
      snippet:
        "The primary innovation of the Transformer is the self-attention mechanism. Unlike recurrent models, it processes all input positions simultaneously.",
      type: "note",
      notebookName: "📚 ML Research",
      notebookId: "demo-1",
      relevance: 92,
      timestamp: "Updated 15m ago",
    },
    {
      id: "r3",
      title: "Sine/Cosine frequency formulas (Flashcard)",
      snippet:
        "Question: What type of positional encoding is used in the original Transformer? Answer: Sine and cosine functions of different frequencies...",
      type: "flashcard",
      notebookName: "📚 ML Research",
      notebookId: "demo-1",
      relevance: 85,
      timestamp: "Generated 1h ago",
    },
    {
      id: "r4",
      title: "Ollama Setup Tutorial video",
      snippet:
        "Transcribed video outline: Downloading llama3 model, exposing inference host URL localport:11434, configuring frontend api bindings.",
      type: "Play",
      notebookName: "💻 System Design",
      notebookId: "demo-3",
      relevance: 78,
      timestamp: "Uploaded 3h ago",
    },
    {
      id: "r5",
      title: "Cellular replication overview (Note)",
      snippet:
        "Ribosome structures translate messenger RNA (mRNA) into polypeptide chains. This synthesis represents the core pathway of genetic transcription.",
      type: "note",
      notebookName: "🧬 Biology Notes",
      notebookId: "demo-2",
      relevance: 74,
      timestamp: "Updated 2d ago",
    },
    {
      id: "r6",
      title: "https://react.dev/reference/react-19",
      snippet:
        "React 19 Server Components reference documentation, actions form state transitions, useActionState, useOptimistic, and API enhancements.",
      type: "url",
      notebookName: "💻 System Design",
      notebookId: "demo-3",
      relevance: 62,
      timestamp: "Updated 3d ago",
    },
  ];

  // Filter & match logic (mock fallback when no real query)
  const filteredResults = useApiResults
    ? apiResults
    : allResults.filter((r) => {
        const matchesQuery =
          r.title.toLowerCase().includes(query.toLowerCase()) ||
          r.snippet.toLowerCase().includes(query.toLowerCase()) ||
          r.notebookName.toLowerCase().includes(query.toLowerCase());
        if (!matchesQuery) return false;
        if (activeFilter === "all") return true;
        return r.type === activeFilter;
  });

  // Group filtered results by notebook name
  const groupedResults: Record<string, SearchResult[]> = {};
  filteredResults.forEach((res) => {
    if (!groupedResults[res.notebookName]) {
      groupedResults[res.notebookName] = [];
    }
    groupedResults[res.notebookName].push(res);
  });

  const getResultIcon = (type: SearchResult["type"]) => {
    switch (type) {
      case "pdf":
        return <FileText className="w-4 h-4 text-primary" />;
      case "url":
        return <Globe className="w-4 h-4 text-secondary" />;
      case "Play":
        return <Play className="w-4 h-4 text-terminal-red" />;
      case "note":
        return <StickyNote className="w-4 h-4 text-terminal-green" />;
      case "flashcard":
        return <Layers className="w-4 h-4 text-terminal-yellow" />;
    }
  };

  const filters = [
    { id: "all", label: "All Results" },
    { id: "pdf", label: "PDFs" },
    { id: "url", label: "Websites" },
    { id: "Play", label: "Videos" },
    { id: "note", label: "Notes" },
    { id: "flashcard", label: "Flashcards" },
  ] as const;

  return (
    <Layout title="Search" showSearch={false}>
      <div className="max-w-4xl mx-auto px-6 py-8 space-y-6 animate-fade-in">
        {/* Search header container */}
        <div className="glass-panel p-6 rounded-xl space-y-4 border-primary/10 shadow-md">
          <div className="input-glow rounded-xl">
            <Input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search across all notebooks, uploaded PDFs, notes, and study tools..."
              startIcon={
                <SearchIcon className="w-5 h-5 text-muted-foreground" />
              }
              className="w-full text-base bg-surface/50 border-outline/25 text-foreground h-12 pl-11 pr-4"
            />
          </div>

          {/* Filters chips */}
          <div className="flex gap-2 flex-wrap pt-1 select-none">
            {filters.map((f) => (
              <button
                key={f.id}
                onClick={() => setActiveFilter(f.id)}
                className={cn(
                  "text-xs font-semibold px-3.5 py-1.5 rounded-full transition-all border",
                  activeFilter === f.id
                    ? "bg-primary text-primary-foreground border-primary shadow-sm"
                    : "glass text-muted-foreground border-outline/10 hover:border-outline/25 hover:text-foreground",
                )}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {query ? (
          /* Results View */
          <div className="space-y-6">
            {Object.keys(groupedResults).length > 0 ? (
              Object.entries(groupedResults).map(([notebookName, items]) => (
                <div key={notebookName} className="space-y-3">
                  <h3 className="text-[10px] font-mono font-semibold text-muted-foreground uppercase tracking-widest pl-1">
                    Notebook: {notebookName}
                  </h3>

                  <div className="space-y-3">
                    {items.map((res) => (
                      <div
                        key={res.id}
                        onClick={() => navigate(`/notebook/${res.notebookId}`)}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            navigate(`/notebook/${res.notebookId}`);
                          }
                        }}
                        className="glass-panel rounded-xl p-4.5 hover:border-primary/20 hover:glow-sm hover:-translate-y-0.5 transition-all duration-200 cursor-pointer flex gap-4 items-start relative group"
                      >
                        {/* Icon circle */}
                        <div className="w-9 h-9 rounded-xl bg-surface/40 flex items-center justify-center border border-outline/10 shrink-0 mt-0.5">
                          {getResultIcon(res.type)}
                        </div>

                        {/* Title and snippet info */}
                        <div className="flex-1 min-w-0 space-y-1 pr-14">
                          <h4 className="font-headline font-bold text-sm text-foreground group-hover:text-primary transition-colors truncate">
                            {res.title}
                          </h4>
                          <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                            {res.snippet}
                          </p>

                          {/* Relevance bar */}
                          <div className="pt-2 flex items-center gap-2">
                            <span className="text-[9px] font-mono text-muted-foreground uppercase">
                              Relevance
                            </span>
                            <div className="w-24 h-1 bg-surface-container rounded-full overflow-hidden shrink-0">
                              <div
                                className="h-full bg-primary"
                                style={{ width: `${res.relevance}%` }}
                              />
                            </div>
                            <span className="text-[9px] font-mono text-primary font-bold">
                              {res.relevance}%
                            </span>
                          </div>
                        </div>

                        {/* Footer details */}
                        <div className="absolute right-4 top-4.5 text-[9px] text-muted-foreground font-mono text-right flex flex-col items-end gap-1.5">
                          <span>{res.timestamp}</span>
                          <ArrowRight className="w-3.5 h-3.5 text-primary opacity-0 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            ) : (
              <div className="glass-panel p-10 rounded-xl text-center text-muted-foreground space-y-2">
                <p className="text-sm">
                  No results match your search query: "{query}"
                </p>
                <p className="text-xs">
                  Try selecting a different filter chip or searching for a
                  different keyword.
                </p>
              </div>
            )}
          </div>
        ) : (
          /* Empty State View: Recents & Popular */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
            {/* Recents list */}
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase font-mono tracking-wider flex items-center gap-1.5 pl-1">
                <History className="w-4 h-4 text-outline/60" /> Recent Searches
              </h3>
              <div className="glass-panel p-4 rounded-xl space-y-1 shadow-sm">
                {recentSearches.map((s, idx) => (
                  <button
                    key={idx}
                    onClick={() => setQuery(s)}
                    className="w-full text-left py-2 px-2.5 rounded-lg text-xs text-on-surface-variant hover:text-foreground hover:bg-surface/40 transition-colors truncate block font-medium"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Popular tags grid */}
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase font-mono tracking-wider flex items-center gap-1.5 pl-1">
                <Sparkles className="w-4 h-4 text-primary" /> Popular Topics
              </h3>
              <div className="glass-panel p-4 rounded-xl flex gap-2 flex-wrap shadow-sm">
                {popularTopics.map((topic, idx) => (
                  <button
                    key={idx}
                    onClick={() => setQuery(topic)}
                    className="text-xs font-medium px-3.5 py-1.5 rounded-xl border border-outline/10 bg-surface/30 hover:bg-surface/60 text-foreground transition-all"
                  >
                    {topic}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
