import React from "react";
import { Search, Bell, User, LogOut, Sun, Moon, Monitor } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ROUTES } from "@/utils/constants";
import { useAuthStore } from "@/store/authStore";
import { useSettingsStore } from "@/store/settingsStore";
import { env } from "@/config/env";

interface TopBarProps {
  /** Page title shown in the center/left */
  title?: string;
  /** Whether to show the global search bar */
  showSearch?: boolean;
  /** Extra actions rendered in the right slot */
  actions?: React.ReactNode;
  className?: string;
}

export function TopBar({
  title,
  showSearch = false,
  actions,
  className,
}: TopBarProps) {
  const { user, logout } = useAuthStore();
  const { theme, setTheme } = useSettingsStore();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate(ROUTES.LOGIN);
  }

  return (
    <header
      className={cn(
        "flex items-center gap-3 px-4 h-[60px] shrink-0 border-b border-border bg-card/70 backdrop-blur-sm",
        className,
      )}
    >
      {/* Title / Breadcrumb */}
      {title && (
        <h1 className="text-sm font-semibold text-foreground truncate">
          {title}
        </h1>
      )}

      {/* Search bar — grows to fill space */}
      {showSearch && (
        <div className="flex-1 max-w-sm mx-auto">
          <Input
            id="topbar-search"
            type="search"
            placeholder="Search notebooks, sources…"
            startIcon={<Search className="w-3.5 h-3.5" />}
            className="h-8 text-xs"
          />
        </div>
      )}

      {/* Right side spacer if no search */}
      {!showSearch && <div className="flex-1" />}

      {/* Right-side actions slot */}
      {actions}

      {/* Theme toggle - Inline segmented control */}
      <div className="flex items-center gap-0.5 p-0.5 bg-accent/50 rounded-lg border border-border">
        {[
          { value: 'light' as const, icon: Sun, label: 'Light' },
          { value: 'dark' as const, icon: Moon, label: 'Dark' },
          { value: 'system' as const, icon: Monitor, label: 'System' },
        ].map(({ value, icon: Icon, label }) => (
          <button
            key={value}
            onClick={() => setTheme(value)}
            title={label}
            className={cn(
              'flex items-center justify-center p-1.5 rounded-md transition-all duration-200',
              theme === value
                ? 'bg-background text-primary shadow-sm ring-1 ring-border/50'
                : 'text-muted-foreground hover:text-foreground hover:bg-background/50'
            )}
          >
            <Icon className="w-3.5 h-3.5" />
          </button>
        ))}
      </div>

      {/* Notification bell */}
      <Button
        variant="ghost"
        size="icon-sm"
        aria-label="Notifications"
        className="text-muted-foreground hover:text-foreground"
      >
        <Bell className="w-4 h-4" />
      </Button>

      {/* User menu */}
      {env.VITE_AUTH_ENABLED && (
        <div className="relative group">
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label={`User menu — ${user?.username ?? "Account"}`}
            className="text-muted-foreground hover:text-foreground"
          >
            <User className="w-4 h-4" />
          </Button>

          {/* Dropdown */}
          <div
            className={cn(
              "absolute right-0 top-full mt-1 w-48 glass rounded-xl border border-border",
              "opacity-0 pointer-events-none group-focus-within:opacity-100 group-focus-within:pointer-events-auto",
              "transition-all duration-200 z-50 shadow-xl py-1",
            )}
          >
            {user && (
              <div className="px-3 py-2 border-b border-border">
                <p className="text-xs font-medium text-foreground truncate">
                  {user.username}
                </p>
                <p className="text-[10px] text-muted-foreground truncate">
                  {user.email}
                </p>
              </div>
            )}
            {env.VITE_AUTH_ENABLED && (
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground
                         hover:text-destructive hover:bg-destructive/10 transition-colors duration-200"
              >
                <LogOut className="w-3.5 h-3.5" />
                Sign out
              </button>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
