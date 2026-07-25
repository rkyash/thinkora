import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  Home,
  Settings,
  Plus,
  ChevronLeft,
  BookOpen,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { ROUTES } from "@/utils/constants";
import { useNotebookStore } from "@/store/notebookStore";
import type { Notebook, Workspace } from "@/types/api";
import { useSettings } from "@/hooks/useSettings";
import { SettingKey } from "@/api/settings";

interface SidebarProps {
  workspaces?: Workspace[];
  notebooks?: Notebook[];
  activeWorkspaceId?: string | null;
  isLoadingNotebooks?: boolean;
  onCreateNotebook?: () => void;
  onSelectWorkspace?: (id: string) => void;
}

export function Sidebar({
  workspaces = [],
  notebooks = [],
  activeWorkspaceId,
  isLoadingNotebooks = false,
  onCreateNotebook,
  onSelectWorkspace,
}: SidebarProps) {
  const navigate = useNavigate();
  const { sidebarOpen, toggleSidebar } = useNotebookStore();

  const { data: settingsData } = useSettings();
  const activeProvider =
    settingsData?.settings.find((s) => s.key === SettingKey.ACTIVE_PROVIDER)
      ?.value || "openai";

  const providerIcons: Record<string, string> = {
    ollama: "🦙",
    openai: "🤖",
    anthropic: "🧠",
    gemini: "✨",
    groq: "⚡",
    mistral: "💫",
    openrouter: "🔀",
    openai_proxy: "🔄",
  };
  const providerIcon = providerIcons[activeProvider] || "🤖";
  const providerNameMap: Record<string, string> = {
    ollama: "Ollama",
    openai: "OpenAI",
    anthropic: "Anthropic",
    gemini: "Gemini",
    groq: "Groq",
    mistral: "Mistral",
    openrouter: "OpenRouter",
    openai_proxy: "Custom",
  };
  const providerName = providerNameMap[activeProvider] || activeProvider;

  return (
    <aside
      className={cn(
        "flex flex-col h-full bg-card border-r border-border transition-all duration-300",
        sidebarOpen ? "w-64" : "w-14",
      )}
      aria-label="Main navigation"
    >
      {/* Logo + collapse toggle */}
      <div
        className={cn(
          "flex items-center gap-2.5 px-3 h-[60px] shrink-0 border-b border-border relative",
          !sidebarOpen && "justify-center px-2",
        )}
      >
        <NavLink
          to={ROUTES.DASHBOARD}
          title="Thinkora - Dashboard"
          className={cn(
            "flex items-center gap-1 min-w-0 flex-1 group focus:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-lg",
            !sidebarOpen && "justify-center flex-initial",
          )}
        >
          <div className="flex items-center justify-center w-9 h-8 rounded-lg shrink-0 transition-transform duration-50 group-hover:scale-105">
            <img
              src="/thinkora_logo_icon.png"
              alt="Thinkora Icon"
              className="w-9 h-8 object-contain drop-shadow-sm"
            />
          </div>
          {sidebarOpen && (
            <div className="flex flex-col items-start justify-center min-w-0 flex-1 py-0.5 transition-opacity duration-50">
              <div className="flex items-center">
                <img
                  src="/thinkora_logo_text_light.png"
                  alt="Thinkora Logo"
                  className="h-6 w-auto object-contain object-left dark:hidden"
                />
                <img
                  src="/thinkora_logo_text_dark.png"
                  alt="Thinkora Logo"
                  className="h-6 w-auto object-contain object-left hidden dark:block"
                />
              </div>
              <span className="text-[7.2px] font-extrabold tracking-[0.06em] text-muted-foreground/90 uppercase leading-none mt-1 select-none gradient-text truncate block">
                READ • UNDERSTAND • THINK BETTER
              </span>
            </div>
          )}
        </NavLink>

        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          onClick={toggleSidebar}
          aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
          className={cn(
            "shrink-0 text-muted-foreground hover:text-foreground transition-all duration-200",
            sidebarOpen
              ? "ml-auto"
              : "absolute -right-3 top-1/2 -translate-y-1/2 z-20 w-6 h-6 rounded-full border border-border bg-card shadow-md hover:bg-accent flex items-center justify-center p-0",
          )}
        >
          <ChevronLeft
            className={cn(
              "w-4 h-4 transition-transform duration-300",
              !sidebarOpen && "rotate-180 w-3.5 h-3.5",
            )}
          />
        </Button>
      </div>

      {/* Nav links */}
      <nav
        className="flex flex-col gap-1 px-2 py-3"
        aria-label="Primary navigation"
      >
        <SidebarLink
          to={ROUTES.DASHBOARD}
          icon={<Home className="w-4 h-4" />}
          label="Home"
          collapsed={!sidebarOpen}
        />
        <SidebarLink
          to={ROUTES.SETTINGS}
          icon={<Settings className="w-4 h-4" />}
          label="Settings"
          collapsed={!sidebarOpen}
        />
      </nav>

      <div className="border-t border-border" />

      {/* Workspaces */}
      {workspaces.length > 0 &&
        (sidebarOpen ? (
          <div className="px-3 py-2">
            <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Workspaces
            </p>
            <div className="space-y-0.5">
              {workspaces.map((ws) => (
                <button
                  key={ws.id}
                  onClick={() => onSelectWorkspace?.(ws.id)}
                  className={cn(
                    "w-full text-left px-2.5 py-1.5 rounded-lg text-sm transition-colors duration-200 truncate",
                    activeWorkspaceId === ws.id
                      ? "bg-accent text-foreground font-medium"
                      : "text-muted-foreground hover:bg-accent hover:text-foreground",
                  )}
                >
                  {ws.name}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-1.5 py-3 border-b border-border">
            {workspaces.map((ws) => {
              const isActive = activeWorkspaceId === ws.id;
              return (
                <button
                  key={ws.id}
                  onClick={() => onSelectWorkspace?.(ws.id)}
                  title={`Workspace: ${ws.name}`}
                  className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold uppercase transition-all duration-200 active:scale-[0.98] shrink-0 border",
                    isActive
                      ? "bg-primary text-primary-foreground border-primary shadow-lg shadow-primary/25"
                      : "bg-background hover:bg-accent text-muted-foreground hover:text-foreground border-border",
                  )}
                >
                  {ws.name.charAt(0)}
                </button>
              );
            })}
          </div>
        ))}

      {/* Notebooks */}
      <div className="flex-1 overflow-y-auto">
        {sidebarOpen && (
          <div className="px-3 py-2">
            <div className="flex items-center justify-between mb-2">
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                Notebooks
              </p>
              {activeWorkspaceId && (
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={onCreateNotebook}
                  aria-label="Create notebook"
                  className="text-muted-foreground hover:text-foreground -mr-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                </Button>
              )}
            </div>

            {isLoadingNotebooks ? (
              <div className="flex items-center gap-2 py-2 px-1 text-muted-foreground">
                <Loader2 className="w-3 h-3 animate-spin" />
                <span className="text-xs">Loading…</span>
              </div>
            ) : notebooks.length === 0 ? (
              <p className="text-xs text-muted-foreground px-1 py-1">
                No notebooks yet
              </p>
            ) : (
              <div className="space-y-0.5">
                {notebooks.map((nb) => (
                  <button
                    key={nb.id}
                    onClick={() => navigate(ROUTES.notebook(nb.id))}
                    className="w-full text-left px-2.5 py-1.5 rounded-lg text-sm
                               text-muted-foreground hover:bg-accent hover:text-foreground
                               transition-colors duration-200 flex items-center gap-2 group"
                  >
                    <span className="text-base">{nb.emoji}</span>
                    <span className="truncate">{nb.name}</span>
                    <BookOpen className="w-3 h-3 ml-auto opacity-0 group-hover:opacity-50 shrink-0" />
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Collapsed state: show notebook dots */}
        {!sidebarOpen && notebooks.length > 0 && (
          <div className="flex flex-col items-center gap-1 py-2">
            {notebooks.slice(0, 6).map((nb) => (
              <button
                key={nb.id}
                onClick={() => navigate(ROUTES.notebook(nb.id))}
                title={nb.name}
                className="w-8 h-8 rounded-lg flex items-center justify-center text-base
                           hover:bg-accent transition-colors duration-200"
              >
                {nb.emoji}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Active AI Provider Badge */}
      <div className="mt-auto border-t border-border p-3">
        {sidebarOpen ? (
          <div
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-background border border-border overflow-hidden"
            title={`Active AI: ${providerName}`}
          >
            <span className="text-lg shrink-0">{providerIcon}</span>
            <div className="min-w-0 flex-1">
              <p className="text-[9px] font-semibold text-muted-foreground uppercase tracking-wider leading-none">
                Active AI
              </p>
              <p className="text-xs font-medium text-foreground truncate">
                {providerName}
              </p>
            </div>
            <div className="w-1.5 h-1.5 rounded-full bg-terminal-green shadow-[0_0_5px_rgba(16,185,129,0.5)] shrink-0" />
          </div>
        ) : (
          <div
            className="flex justify-center"
            title={`Active AI: ${providerName}`}
          >
            <div className="relative w-8 h-8 rounded-lg bg-background border border-border flex items-center justify-center">
              <span className="text-base">{providerIcon}</span>
              <div className="absolute top-0 right-0 w-1.5 h-1.5 rounded-full bg-terminal-green shadow-[0_0_5px_rgba(16,185,129,0.5)] translate-x-1/3 -translate-y-1/3" />
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}

// ─── Helper: nav link ─────────────────────────────────────────────────────────

function SidebarLink({
  to,
  icon,
  label,
  collapsed,
}: {
  to: string;
  icon: React.ReactNode;
  label: string;
  collapsed: boolean;
}) {
  return (
    <NavLink
      to={to}
      end
      title={collapsed ? label : undefined}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm transition-colors duration-200",
          isActive
            ? "bg-accent text-foreground font-medium"
            : "text-muted-foreground hover:bg-accent hover:text-foreground",
          collapsed && "justify-center px-0",
        )
      }
    >
      {icon}
      {!collapsed && <span>{label}</span>}
    </NavLink>
  );
}
