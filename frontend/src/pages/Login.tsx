import React, { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Eye, EyeOff, Brain, Mail, Lock } from "lucide-react";
import { PageLayout } from "@/components/layout/Layout";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { ROUTES } from "@/utils/constants";

export function Login() {
  const [searchParams] = useSearchParams();
  const redirect = searchParams.get("redirect") ?? ROUTES.DASHBOARD;

  const [email, setEmail] = useState("admin");
  const [password, setPassword] = useState("admin");
  const [showPassword, setShowPassword] = useState(false);

  const { loginMutation } = useAuth();
  const isLoading = loginMutation.isPending;
  const error = loginMutation.error;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) {
      return;
    }
    loginMutation.mutate({ email, password });
  }

  // Floating particles helper
  const particles = Array.from({ length: 15 }, (_, i) => ({
    id: i,
    size: Math.random() * 6 + 4,
    top: Math.random() * 100,
    left: Math.random() * 100,
    delay: Math.random() * 6,
    duration: Math.random() * 8 + 6,
  }));

  return (
    <PageLayout className="relative flex items-center justify-center min-h-screen bg-radial-glow overflow-hidden">
      {/* Floating Particles Background */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden z-0">
        {particles.map((p) => (
          <div
            key={p.id}
            className="absolute rounded-full bg-primary/10 animate-float"
            style={{
              width: `${p.size}px`,
              height: `${p.size}px`,
              top: `${p.top}%`,
              left: `${p.left}%`,
              animationDelay: `${p.delay}s`,
              animationDuration: `${p.duration}s`,
            }}
          />
        ))}
      </div>

      <div className="w-full max-w-md px-6 z-10 animate-fade-in">
        {/* Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mb-4 glow-sm border border-primary/20">
            <Brain className="w-7 h-7 text-primary" />
          </div>
          <h1 className="text-3xl font-headline font-bold gradient-text tracking-tight">
            Welcome back
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Sign in to your Thinkora account
          </p>
        </div>

        {/* Card */}
        <div className="glass-panel rounded-2xl p-8 sm:p-10 shadow-lg">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="bg-destructive/10 border border-destructive/20 text-destructive rounded-lg px-4 py-3 text-sm animate-fade-in">
                {error instanceof Error
                  ? error.message
                  : "Invalid email or password."}
              </div>
            )}

            <div className="space-y-2">
              <label
                htmlFor="login-email"
                className="text-sm font-medium text-on-surface-variant"
              >
                Email/UserName
              </label>
              <div className="input-glow rounded-lg">
                <Input
                  id="login-email"
                  type="text"
                  autoComplete="current"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  disabled={isLoading}
                  startIcon={<Mail className="w-4 h-4 text-muted-foreground" />}
                  className="bg-surface/50 border-outline/20 text-foreground"
                  minLength={1}
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label
                  htmlFor="login-password"
                  className="text-sm font-medium text-on-surface-variant"
                >
                  Password
                </label>
                <Link
                  to="#"
                  className="text-xs text-primary hover:underline hover:text-violet-primary"
                  onClick={(e) => e.preventDefault()}
                >
                  Forgot password?
                </Link>
              </div>
              <div className="input-glow rounded-lg">
                <Input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  disabled={isLoading}
                  startIcon={<Lock className="w-4 h-4 text-muted-foreground" />}
                  className="bg-surface/50 border-outline/20 text-foreground"
                  endIcon={
                    <button
                      type="button"
                      aria-label="Toggle password visibility"
                      onClick={() => setShowPassword((v) => !v)}
                      tabIndex={-1}
                      className="text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {showPassword ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                    </button>
                  }
                />
              </div>
            </div>

            <Button
              type="submit"
              id="login-submit"
              disabled={isLoading}
              className="w-full btn-glow bg-primary hover:bg-violet-primary text-primary-foreground font-semibold h-11 active:scale-[0.98] transition-all duration-150"
            >
              {isLoading && <Spinner className="w-4 h-4 mr-2" />}
              {isLoading ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          {/* Social Divider */}
          {/* <div className="relative flex items-center my-6">
            <div className="flex-grow border-t border-outline/25"></div>
            <span className="flex-shrink mx-4 text-[10px] tracking-wider font-semibold text-muted-foreground uppercase font-mono">
              or continue with
            </span>
            <div className="flex-grow border-t border-outline/25"></div>
          </div> */}

          {/* Social Buttons */}
          {/* <div className="grid grid-cols-2 gap-4">
            <Button
              type="button"
              variant="outline"
              className="border-outline/20 bg-surface/30 hover:bg-surface/60 text-foreground hover:text-white"
              onClick={() => alert("Social login demo")}
            >
              <svg
                className="w-4 h-4 mr-2"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M12.24 10.285V13.4h6.887C18.2 15.614 15.645 18 12.24 18c-3.86 0-7-3.14-7-7s3.14-7 7-7c1.706 0 3.277.61 4.5 1.625l2.437-2.437C17.312 1.696 14.933 1 12.24 1 6.583 1 2 5.583 2 11.24s4.583 10.24 10.24 10.24c5.795 0 10.254-4.074 10.254-10.24 0-.695-.08-1.355-.22-1.955H12.24z" />
              </svg>
              Google
            </Button>
            <Button
              type="button"
              variant="outline"
              className="border-outline/20 bg-surface/30 hover:bg-surface/60 text-foreground hover:text-white"
              onClick={() => alert("Social login demo")}
            >
              <svg
                className="w-4 h-4 mr-2"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
              </svg>
              GitHub
            </Button>
          </div> */}

          {/* Bottom text */}
          <p className="text-center text-sm text-muted-foreground mt-8">
            Don't have an account?{" "}
            <Link
              to={ROUTES.REGISTER}
              className="text-primary hover:underline hover:text-violet-primary font-semibold"
            >
              Create one
            </Link>
          </p>
        </div>
      </div>
    </PageLayout>
  );
}
