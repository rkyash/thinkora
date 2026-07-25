import React, { useState, useEffect } from "react";
import {
  Brain,
  Cpu,
  Palette,
  Lock,
  Eye,
  EyeOff,
  CheckCircle2,
  XCircle,
  Loader2,
  RefreshCcw,
  Save,
  Trash2,
  Server,
  ChevronDown,
  Sun,
  Moon,
  Monitor,
} from "lucide-react";
import { Layout } from "@/components/layout/Layout";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { cn } from "@/lib/utils";
import {
  useSettings,
  useBulkUpdateSettings,
  useTestProvider,
  useFetchModels,
} from "@/hooks/useSettings";
import { SettingKey } from "@/api/settings";
import { useSettingsStore } from "@/store/settingsStore";

// ─── Per-provider curated model catalogues ────────────────────────────────────

const PROVIDER_MODELS: Record<string, { label: string; value: string }[]> = {
  openai: [
    { label: "GPT-4o (Latest)", value: "openai/gpt-4o" },
    { label: "GPT-4o Mini", value: "openai/gpt-4o-mini" },
    { label: "GPT-4 Turbo", value: "openai/gpt-4-turbo" },
    { label: "GPT-3.5 Turbo", value: "openai/gpt-3.5-turbo" },
    { label: "o1 Preview", value: "openai/o1-preview" },
    { label: "o1 Mini", value: "openai/o1-mini" },
    { label: "o3 Mini", value: "openai/o3-mini" },
  ],
  anthropic: [
    {
      label: "Claude 3.5 Sonnet",
      value: "anthropic/claude-3-5-sonnet-20241022",
    },
    { label: "Claude 3.5 Haiku", value: "anthropic/claude-3-5-haiku-20241022" },
    { label: "Claude 3 Opus", value: "anthropic/claude-3-opus-20240229" },
    { label: "Claude 3 Sonnet", value: "anthropic/claude-3-sonnet-20240229" },
    { label: "Claude 3 Haiku", value: "anthropic/claude-3-haiku-20240307" },
  ],
  gemini: [
    { label: "Gemini 2.0 Flash", value: "gemini/gemini-2.0-flash" },
    { label: "Gemini 2.0 Flash Lite", value: "gemini/gemini-2.0-flash-lite" },
    { label: "Gemini 1.5 Pro", value: "gemini/gemini-1.5-pro-latest" },
    { label: "Gemini 1.5 Flash", value: "gemini/gemini-1.5-flash-latest" },
    { label: "Gemini 1.5 Flash 8B", value: "gemini/gemini-1.5-flash-8b" },
  ],
  groq: [
    {
      label: "Llama 3.3 70B (Versatile)",
      value: "groq/llama-3.3-70b-versatile",
    },
    { label: "Llama 3.1 70B", value: "groq/llama-3.1-70b-versatile" },
    { label: "Llama 3.1 8B Instant", value: "groq/llama-3.1-8b-instant" },
    { label: "Mixtral 8x7B", value: "groq/mixtral-8x7b-32768" },
    { label: "Gemma 2 9B", value: "groq/gemma2-9b-it" },
  ],
  mistral: [
    { label: "Mistral Large Latest", value: "mistral/mistral-large-latest" },
    { label: "Mistral Small Latest", value: "mistral/mistral-small-latest" },
    { label: "Codestral Latest", value: "mistral/codestral-latest" },
    { label: "Pixtral 12B", value: "mistral/pixtral-12b-2409" },
    { label: "Mistral 7B Instruct", value: "mistral/open-mistral-7b" },
  ],
  openrouter: [
    { label: "GPT-4o (via OpenRouter)", value: "openrouter/openai/gpt-4o" },
    {
      label: "Claude 3.5 Sonnet (via OpenRouter)",
      value: "openrouter/anthropic/claude-3.5-sonnet",
    },
    {
      label: "Gemini Flash 1.5 (via OpenRouter)",
      value: "openrouter/google/gemini-flash-1.5",
    },
    {
      label: "Llama 3.1 70B (via OpenRouter)",
      value: "openrouter/meta-llama/llama-3.1-70b-instruct",
    },
    {
      label: "Qwen 2.5 72B (via OpenRouter)",
      value: "openrouter/qwen/qwen-2.5-72b-instruct",
    },
  ],
  ollama: [{ label: "Custom model…", value: "__custom__" }],
  openai_proxy: [{ label: "Custom model…", value: "__custom__" }],
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

const MASK = "••••••••";

function isMasked(val: string | null | undefined): boolean {
  return val === MASK || val === "••••••••";
}

const PROVIDER_ICONS: Record<string, string> = {
  ollama: "🦙",
  openai: "🤖",
  anthropic: "🧠",
  gemini: "✨",
  groq: "⚡",
  mistral: "💫",
  openrouter: "🔀",
  openai_proxy: "🔄",
};

// ─── ModelSelector sub-component ─────────────────────────────────────────────

interface ModelSelectorProps {
  providerId: string;
  modelSettingKey: string;
  value: string;
  onChange: (key: string, value: string) => void;
  fetchedModels?: string[];
  onFetchModels?: () => void;
  isFetchingModels?: boolean;
  className?: string;
}

function ModelSelector({
  providerId,
  modelSettingKey,
  value,
  onChange,
  fetchedModels = [],
  onFetchModels,
  isFetchingModels,
  className,
}: ModelSelectorProps) {
  const baseModels = PROVIDER_MODELS[providerId] ?? [];
  const fetchedOptions = fetchedModels.map((m) => {
    const prefix =
      providerId === "openai_proxy"
        ? "openai/"
        : providerId === "ollama"
          ? "ollama/"
          : `${providerId}/`;
    return { label: m, value: `${prefix}${m}` };
  });

  const allModels = [...baseModels, ...fetchedOptions].reduce(
    (acc, curr) => {
      if (!acc.some((m) => m.value === curr.value)) acc.push(curr);
      return acc;
    },
    [] as typeof baseModels,
  );

  const hasCustom = allModels.some((m) => m.value === "__custom__");

  // Determine if current value is one of the known options or a custom one
  const isKnownOption = allModels.some(
    (m) => m.value === value && m.value !== "__custom__",
  );
  const isCustom = Boolean(value && !isKnownOption);
  const [showCustomInput, setShowCustomInput] = useState(isCustom);
  const [customVal, setCustomVal] = useState(isCustom ? value : "");

  function handleSelectChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const v = e.target.value;
    if (v === "__custom__") {
      setShowCustomInput(true);
      // don't call onChange yet — wait for custom input
    } else {
      setShowCustomInput(false);
      onChange(modelSettingKey, v);
    }
  }

  function handleCustomChange(e: React.ChangeEvent<HTMLInputElement>) {
    const v = e.target.value;
    setCustomVal(v);
    onChange(modelSettingKey, v);
  }

  const selectValue = showCustomInput ? "__custom__" : value || "";

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-center justify-between">
        <label className="text-[10px] font-semibold text-muted-foreground uppercase font-mono tracking-wider flex items-center gap-1">
          <Cpu className="w-3 h-3" />
          Model
        </label>
        {onFetchModels && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onFetchModels}
            disabled={isFetchingModels}
            className="h-5 text-[10px] px-2 text-muted-foreground hover:text-foreground"
          >
            {isFetchingModels ? (
              <Loader2 className="w-3 h-3 animate-spin mr-1" />
            ) : (
              <RefreshCcw className="w-3 h-3 mr-1" />
            )}
            Fetch Models
          </Button>
        )}
      </div>
      <div className="relative">
        <select
          value={selectValue}
          onChange={handleSelectChange}
          className="w-full text-xs rounded-lg bg-background border border-outline-variant px-2.5 py-1.5 pr-7 text-foreground focus:ring-1 focus:ring-primary focus:outline-none transition-all appearance-none cursor-pointer"
        >
          <option value="">— use global default —</option>
          {allModels
            .filter((m) => m.value !== "__custom__")
            .map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          {hasCustom && (
            <option value="__custom__">Custom model string…</option>
          )}
        </select>
        <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-muted-foreground pointer-events-none" />
      </div>
      {showCustomInput && (
        <Input
          value={customVal}
          onChange={handleCustomChange}
          placeholder={`e.g. ollama/llama3.2:latest`}
          className="text-xs bg-surface/50 border-outline/20 text-foreground h-7"
          autoFocus
        />
      )}
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export function Settings() {
  const { data, isLoading, isError, refetch } = useSettings();
  const bulkUpdate = useBulkUpdateSettings();
  const testProvider = useTestProvider();
  const fetchModelsHook = useFetchModels();
  const { setTheme } = useSettingsStore();

  const [localSettings, setLocalSettings] = useState<Record<string, string>>(
    {},
  );
  const [dirty, setDirty] = useState<Set<string>>(new Set());
  const [visibleKeys, setVisibleKeys] = useState<Record<string, boolean>>({});
  const [testResults, setTestResults] = useState<
    Record<string, { success: boolean; message: string }>
  >({});
  const [testingId, setTestingId] = useState<string | null>(null);
  const [fetchedModels, setFetchedModels] = useState<Record<string, string[]>>(
    {},
  );
  const [fetchingId, setFetchingId] = useState<string | null>(null);

  // Sync loaded settings into local state
  useEffect(() => {
    if (!data) return;
    const initial: Record<string, string> = {};
    for (const s of data.settings) {
      if (!(s.key in localSettings)) {
        initial[s.key] = isMasked(s.value) ? "" : (s.value ?? "");
      }
    }
    // Also seed per-provider model selections from ProviderInfo.selected_model
    for (const p of data.providers) {
      if (
        p.model_setting &&
        p.selected_model &&
        !(p.model_setting in localSettings)
      ) {
        initial[p.model_setting] = p.selected_model;
      }
      if (
        p.base_url_setting &&
        p.selected_base_url &&
        !(p.base_url_setting in localSettings)
      ) {
        initial[p.base_url_setting] = p.selected_base_url;
      }
    }
    setLocalSettings((prev) => ({ ...initial, ...prev }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const settingsMap = React.useMemo(() => {
    const m: Record<string, string | null> = {};
    for (const s of data?.settings ?? []) m[s.key] = s.value;
    return m;
  }, [data]);

  function handleChange(key: string, value: string) {
    setLocalSettings((prev) => ({ ...prev, [key]: value }));
    setDirty((prev) => new Set(prev).add(key));
  }

  function toggleVisible(key: string) {
    setVisibleKeys((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  async function handleSave() {
    if (dirty.size === 0) return;
    const updates: Record<string, string> = {};
    for (const key of dirty) {
      const val = localSettings[key] ?? "";
      if (val !== "" || !isMasked(settingsMap[key])) {
        updates[key] = val;
      }
    }
    await bulkUpdate.mutateAsync(updates);
    setDirty(new Set());
  }

  async function handleTestProvider(providerId: string) {
    setTestingId(providerId);
    setTestResults((prev) => ({
      ...prev,
      [providerId]: { success: false, message: "" },
    }));
    try {
      const result = await testProvider.mutateAsync(providerId);
      setTestResults((prev) => ({
        ...prev,
        [providerId]: { success: result.success, message: result.message },
      }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Connection failed";
      setTestResults((prev) => ({
        ...prev,
        [providerId]: { success: false, message: msg },
      }));
    } finally {
      setTestingId(null);
    }
  }

  async function handleFetchModels(providerId: string) {
    setFetchingId(providerId);
    try {
      const models = await fetchModelsHook.mutateAsync(providerId);
      setFetchedModels((prev) => ({ ...prev, [providerId]: models }));
    } catch (err: unknown) {
      console.error("Failed to fetch models:", err);
    } finally {
      setFetchingId(null);
    }
  }

  // ─── Appearance values ───────────────────────────────────────────────────────
  const theme = localSettings[SettingKey.THEME] || "dark";
  const fontSize = localSettings[SettingKey.FONT_SIZE] || "md";
  const compactMode = localSettings[SettingKey.COMPACT_MODE] === "true";

  // ─── Loading / Error ─────────────────────────────────────────────────────────

  if (isLoading) {
    return (
      <Layout title="Settings">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-6 h-6 animate-spin text-primary" />
          <span className="ml-3 text-muted-foreground">Loading settings…</span>
        </div>
      </Layout>
    );
  }

  if (isError) {
    return (
      <Layout title="Settings">
        <div className="flex flex-col items-center justify-center h-64 gap-4">
          <XCircle className="w-8 h-8 text-destructive" />
          <p className="text-muted-foreground">Failed to load settings.</p>
          <Button variant="outline" onClick={() => refetch()} className="gap-2">
            <RefreshCcw className="w-4 h-4" /> Retry
          </Button>
        </div>
      </Layout>
    );
  }

  const providers = data?.providers ?? [];

  return (
    <Layout title="Settings">
      <div className="max-w-3xl mx-auto px-6 py-8 space-y-6 animate-fade-in">
        {/* Header */}
        <div className="mb-2">
          <h1 className="text-3xl font-headline font-bold text-foreground">
            Workspace Settings
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Configure AI providers, select models, and adjust appearance.
          </p>
        </div>

        {/* ─── Section 0: Active Provider ────────────────────────────────────────── */}
        <section className="glass-panel rounded-xl p-6 space-y-5 border border-primary/20 bg-primary/5">
          <div className="flex items-center gap-3 border-b border-outline/10 pb-3">
            <Brain className="w-5 h-5 text-primary" />
            <h2 className="font-headline font-semibold text-foreground text-base">
              Active AI Provider
            </h2>
            <span className="text-xs text-muted-foreground ml-auto">
              Select which AI powers your workspace
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {providers.map((p) => {
              const isActive =
                localSettings[SettingKey.ACTIVE_PROVIDER] === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => handleChange(SettingKey.ACTIVE_PROVIDER, p.id)}
                  className={cn(
                    "flex flex-col items-center justify-center p-4 rounded-xl border transition-all text-center gap-2",
                    isActive
                      ? "border-primary bg-primary/10 shadow-[0_0_15px_rgba(var(--primary),0.2)]"
                      : "border-border bg-card hover:bg-accent hover:border-outline/30",
                  )}
                >
                  <span className="text-3xl mb-1">
                    {PROVIDER_ICONS[p.id] ?? "🤖"}
                  </span>
                  <span
                    className={cn(
                      "font-headline font-bold text-sm",
                      isActive ? "text-primary" : "text-foreground",
                    )}
                  >
                    {p.name}
                  </span>
                  <div className="flex items-center gap-1.5 mt-1">
                    <span
                      className={cn(
                        "w-2 h-2 rounded-full",
                        p.is_configured
                          ? "bg-terminal-green"
                          : "bg-terminal-red",
                      )}
                    />
                    <span className="text-[10px] text-muted-foreground font-mono">
                      {p.is_configured ? "Ready" : "Missing Key"}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {/* ─── Section 1: AI Provider Configurations ───────────────────────────── */}
        <section className="glass-panel rounded-xl p-6 space-y-5">
          <div className="flex items-center gap-3 border-b border-outline/10 pb-3">
            <Server className="w-5 h-5 text-primary" />
            <h2 className="font-headline font-semibold text-foreground text-base">
              Provider Configurations
            </h2>
            <span className="text-xs text-muted-foreground ml-auto">
              Configure API keys and select the model to use per provider
            </span>
          </div>

          <div className="space-y-4">
            {providers.map((p) => {
              const keySettingKey = p.key_setting ?? "";
              const currentKeyVal = localSettings[keySettingKey] ?? "";
              const isVisible = !!visibleKeys[p.id];
              const testResult = testResults[p.id];
              const isTesting = testingId === p.id;

              return (
                <div
                  key={p.id}
                  className={cn(
                    "glass rounded-xl border transition-all overflow-hidden",
                    p.is_configured
                      ? "border-terminal-green/20 bg-terminal-green/5"
                      : "border-border bg-card",
                  )}
                >
                  {/* Top row: name / badge / API key / test */}
                  <div className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    {/* Provider info */}
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      <span className="text-2xl leading-none mt-0.5 shrink-0">
                        {PROVIDER_ICONS[p.id] ?? "🤖"}
                      </span>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-headline font-bold text-sm text-foreground">
                            {p.name}
                          </span>
                          <span
                            className={cn(
                              "text-[9px] font-mono font-bold px-2 py-0.5 rounded-full border",
                              p.is_configured
                                ? "bg-terminal-green/10 border-terminal-green/20 text-terminal-green"
                                : "bg-muted border-border text-muted-foreground",
                            )}
                          >
                            {p.is_configured ? "configured" : "unconfigured"}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-0.5 leading-snug">
                          {p.description}
                        </p>
                      </div>
                    </div>

                    {/* API key / URL + test */}
                    <div className="flex items-center gap-2 shrink-0 flex-wrap">
                      {p.key_setting && (
                        <div className="input-glow rounded-lg">
                          <Input
                            type={isVisible ? "text" : "password"}
                            value={currentKeyVal}
                            onChange={(e) =>
                              handleChange(keySettingKey, e.target.value)
                            }
                            placeholder={
                              isMasked(settingsMap[keySettingKey])
                                ? "Already set — type to replace"
                                : "Enter API key"
                            }
                            startIcon={
                              <Lock className="w-3.5 h-3.5 text-muted-foreground" />
                            }
                            className="w-44 text-xs bg-background border-border text-foreground h-8"
                            endIcon={
                              <button
                                type="button"
                                onClick={() => toggleVisible(p.id)}
                                className="text-muted-foreground hover:text-foreground"
                              >
                                {isVisible ? (
                                  <EyeOff className="w-3.5 h-3.5" />
                                ) : (
                                  <Eye className="w-3.5 h-3.5" />
                                )}
                              </button>
                            }
                          />
                        </div>
                      )}

                      {p.base_url_setting && (
                        <div className="input-glow rounded-lg">
                          <Input
                            value={localSettings[p.base_url_setting] ?? ""}
                            onChange={(e) =>
                              handleChange(p.base_url_setting!, e.target.value)
                            }
                            placeholder={
                              p.id === "ollama"
                                ? "http://localhost:11434"
                                : "https://api.example.com/v1"
                            }
                            startIcon={
                              <Server className="w-3.5 h-3.5 text-muted-foreground" />
                            }
                            className="w-44 text-xs bg-background border-border text-foreground h-8"
                          />
                        </div>
                      )}

                      <Button
                        variant="outline"
                        onClick={() => handleTestProvider(p.id)}
                        disabled={isTesting}
                        className="border-border bg-background hover:bg-accent text-foreground text-[10px] px-3 h-8 gap-1 shrink-0"
                      >
                        {isTesting ? (
                          <>
                            <Loader2 className="w-3 h-3 animate-spin" />
                            Testing…
                          </>
                        ) : (
                          "Test"
                        )}
                      </Button>
                    </div>
                  </div>

                  {/* Model selector row */}
                  {p.model_setting && (
                    <div className="px-4 pb-4 border-t border-border pt-3 bg-muted/20">
                      <ModelSelector
                        providerId={p.id}
                        modelSettingKey={p.model_setting}
                        value={localSettings[p.model_setting] ?? ""}
                        onChange={handleChange}
                        fetchedModels={fetchedModels[p.id]}
                        onFetchModels={
                          p.supports_fetch_models
                            ? () => handleFetchModels(p.id)
                            : undefined
                        }
                        isFetchingModels={fetchingId === p.id}
                      />
                      {localSettings[p.model_setting] && (
                        <p className="text-[10px] text-muted-foreground mt-1.5 font-mono">
                          LiteLLM string:{" "}
                          <span className="text-primary/70">
                            {localSettings[p.model_setting]}
                          </span>
                        </p>
                      )}
                    </div>
                  )}

                  {/* Test result banner */}
                  {testResult && !isTesting && (
                    <div
                      className={cn(
                        "mx-4 mb-4 flex items-start gap-2 rounded-lg px-3 py-2 text-xs",
                        testResult.success
                          ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                          : "border-destructive/20 bg-destructive/10 text-destructive",
                      )}
                    >
                      {testResult.success ? (
                        <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                      ) : (
                        <XCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                      )}
                      <span className="leading-snug">{testResult.message}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* ─── Section 3: Appearance ───────────────────────────────────────────── */}
        <section className="glass-panel rounded-xl p-6 space-y-5">
          <div className="flex items-center gap-3 border-b border-outline/10 pb-3">
            <Palette className="w-5 h-5 text-primary" />
            <h2 className="font-headline font-semibold text-foreground text-base">
              Appearance
            </h2>
          </div>

          <div className="space-y-5 divide-y divide-outline/10">
            {/* Theme */}
            <div className="flex flex-col gap-3 py-2">
              <div>
                <span className="text-sm font-semibold text-foreground font-headline">
                  Theme Mode
                </span>
                <p className="text-xs text-muted-foreground">
                  Adjust interface color tone.
                </p>
              </div>
              <div className="flex gap-2">
                {[
                  { value: "light" as const, icon: Sun, label: "Light" },
                  { value: "dark" as const, icon: Moon, label: "Dark" },
                  { value: "system" as const, icon: Monitor, label: "System" },
                ].map(({ value, icon: Icon, label }) => (
                  <button
                    key={value}
                    onClick={() => {
                      handleChange(SettingKey.THEME, value);
                      setTheme(value as any);
                    }}
                    className={cn(
                      "flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg",
                      "border transition-all duration-200",
                      theme === value
                        ? "bg-primary/10 border-primary text-primary"
                        : "bg-card border-border text-muted-foreground hover:bg-accent",
                    )}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="text-sm font-medium">{label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Font Size */}
            <div className="flex items-center justify-between pt-4 pb-2">
              <div>
                <span className="text-sm font-semibold text-foreground font-headline">
                  Font Size
                </span>
                <p className="text-xs text-muted-foreground">
                  Modify text readability scale.
                </p>
              </div>
              <div className="flex gap-1 bg-muted/50 p-1 rounded-xl border border-border text-xs font-medium">
                {(["sm", "md", "lg"] as const).map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => handleChange(SettingKey.FONT_SIZE, opt)}
                    className={cn(
                      "px-3 py-1.5 rounded-lg uppercase transition-colors",
                      fontSize === opt
                        ? "bg-primary/20 text-primary font-bold"
                        : "text-muted-foreground hover:text-foreground",
                    )}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </div>

            {/* Compact Mode */}
            <div className="flex items-center justify-between pt-4 pb-2">
              <div>
                <span className="text-sm font-semibold text-foreground font-headline">
                  Compact Layout
                </span>
                <p className="text-xs text-muted-foreground">
                  Reduce paddings and list density.
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={compactMode}
                onClick={() =>
                  handleChange(
                    SettingKey.COMPACT_MODE,
                    compactMode ? "false" : "true",
                  )
                }
                className={cn(
                  "relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background",
                  compactMode
                    ? "bg-primary"
                    : "bg-surface/70 border border-outline/30",
                )}
              >
                <span
                  className={cn(
                    "inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform",
                    compactMode ? "translate-x-4" : "translate-x-1",
                  )}
                />
              </button>
            </div>
          </div>
        </section>

        {/* ─── Save / Reset Bar ─────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center gap-2">
            {dirty.size > 0 && (
              <span className="text-xs text-terminal-yellow font-mono">
                {dirty.size} unsaved change{dirty.size > 1 ? "s" : ""}
              </span>
            )}
            {bulkUpdate.isSuccess && dirty.size === 0 && (
              <span className="flex items-center gap-1 text-xs text-terminal-green">
                <CheckCircle2 className="w-3.5 h-3.5" /> Saved
              </span>
            )}
            {bulkUpdate.isError && (
              <span className="flex items-center gap-1 text-xs text-terminal-red">
                <XCircle className="w-3.5 h-3.5" /> Save failed
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            {dirty.size > 0 && (
              <Button
                variant="outline"
                onClick={() => {
                  setDirty(new Set());
                  setLocalSettings({});
                  refetch();
                }}
                className="gap-1.5 border-outline/20 text-muted-foreground hover:text-foreground"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Discard
              </Button>
            )}

            <Button
              onClick={handleSave}
              disabled={dirty.size === 0 || bulkUpdate.isPending}
              className="btn-glow bg-primary hover:bg-violet-primary text-primary-foreground font-semibold px-6 h-10 shadow-sm gap-2 active:scale-[0.98] transition-all duration-150"
            >
              {bulkUpdate.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Saving…
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Save Configuration
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </Layout>
  );
}
