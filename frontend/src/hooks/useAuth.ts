import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import * as authApi from "@/api/auth";
import { useAuthStore } from "@/store/authStore";
import { meKeys } from "@/utils/queryKeys";
import { ROUTES } from "@/utils/constants";

/**
 * useAuth — comprehensive auth hook.
 *
 * Provides:
 * - `user`        current user from Zustand store
 * - `isAuthed`    true if JWT present
 * - `loginMutation`    trigger login
 * - `registerMutation` trigger registration
 * - `logoutMutation`   trigger logout + redirect
 * - `meQuery`     TanStack Query for /auth/me (refetches on mount when authed)
 */
export function useAuth() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const {
    user,
    accessToken,
    login: storeLogin,
    logout: storeLogout,
    setUser,
  } = useAuthStore();

  const isAuthed = Boolean(accessToken);

  // ─── Fetch current user ──────────────────────────────────────────────────
  const meQuery = useQuery({
    queryKey: meKeys.all,
    queryFn: async () => {
      const res = await authApi.getMe();
      if (res.data) setUser(res.data);
      return res.data;
    },
    enabled: isAuthed,
    staleTime: 5 * 60 * 1000,
  });

  // ─── Login ───────────────────────────────────────────────────────────────
  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: async (res) => {
      const resp = res.data;
      // Fetch user profile immediately after login
      // const meRes = await authApi.getMe()
      storeLogin(resp.user, {
        access_token: resp.tokens.access_token,
        refresh_token: resp.tokens.refresh_token,
      });
      await queryClient.invalidateQueries({ queryKey: meKeys.all });
      navigate(ROUTES.DASHBOARD);
    },
  });

  // ─── Register ────────────────────────────────────────────────────────────
  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: async (res) => {
      // After register, log user in automatically
      // (backend creates account — user must then login or backend returns tokens)
      void res;
      navigate(ROUTES.LOGIN);
    },
  });

  // ─── Logout ──────────────────────────────────────────────────────────────
  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSettled: () => {
      storeLogout();
      queryClient.clear();
      navigate(ROUTES.LOGIN);
    },
  });

  return {
    user: user ?? meQuery.data,
    isAuthed,
    isLoadingMe: meQuery.isLoading,
    loginMutation,
    registerMutation,
    logoutMutation,
  };
}
