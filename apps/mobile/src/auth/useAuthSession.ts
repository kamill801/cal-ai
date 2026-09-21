import type { Session, SupabaseClient } from "@supabase/supabase-js";
import { makeRedirectUri } from "expo-auth-session";
import * as WebBrowser from "expo-web-browser";
import { useEffect, useMemo, useState } from "react";
import { AppState, Platform } from "react-native";
import { createSupabaseAuthClient, isSupabaseAuthEnabled } from "./supabase";

WebBrowser.maybeCompleteAuthSession();

export interface AuthSessionState {
  enabled: boolean;
  configured: boolean;
  ready: boolean;
  loading: boolean;
  session?: Session;
  error?: string;
  signInWithKakao(): Promise<void>;
  signOut(): Promise<boolean>;
}

export function useAuthSession(): AuthSessionState {
  const enabled = isSupabaseAuthEnabled();
  const client = useMemo(() => createSupabaseAuthClient(), []);
  const [session, setSession] = useState<Session | undefined>();
  const [ready, setReady] = useState(!enabled);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();

  useEffect(() => {
    if (!client) {
      setReady(true);
      return;
    }
    let mounted = true;
    void client.auth.getSession().then(({ data }) => {
      if (mounted) {
        setSession(data.session ?? undefined);
        setReady(true);
      }
    }).catch(() => {
      if (mounted) {
        setError("로그인 상태를 불러오지 못했어요. 다시 로그인해 주세요.");
        setReady(true);
      }
    });
    const { data } = client.auth.onAuthStateChange((_event, nextSession) => {
      if (mounted) {
        setSession(nextSession ?? undefined);
        setReady(true);
      }
    });
    return () => {
      mounted = false;
      data.subscription.unsubscribe();
    };
  }, [client]);

  useEffect(() => {
    if (!client) {
      return;
    }
    const updateRefreshState = (state: string) => {
      if (state === "active") {
        client.auth.startAutoRefresh();
        return;
      }
      client.auth.stopAutoRefresh();
    };
    updateRefreshState(AppState.currentState);
    const subscription = AppState.addEventListener("change", updateRefreshState);
    return () => {
      subscription.remove();
      client.auth.stopAutoRefresh();
    };
  }, [client]);

  return {
    enabled,
    configured: !enabled || Boolean(client),
    ready,
    loading,
    session,
    error,
    async signInWithKakao() {
      if (!client) {
        setError("카카오 로그인 환경 설정이 아직 완료되지 않았어요.");
        return;
      }
      setLoading(true);
      setError(undefined);
      try {
        await openKakaoLogin(client);
      } catch {
        setError("카카오 로그인을 완료하지 못했어요. 잠시 후 다시 시도해 주세요.");
      } finally {
        setLoading(false);
      }
    },
    async signOut() {
      if (!client) {
        return true;
      }
      setLoading(true);
      setError(undefined);
      try {
        const { error: signOutError } = await client.auth.signOut();
        if (signOutError) {
          throw signOutError;
        }
        return true;
      } catch {
        setError("로그아웃하지 못했어요. 다시 시도해 주세요.");
        return false;
      } finally {
        setLoading(false);
      }
    }
  };
}

async function openKakaoLogin(client: SupabaseClient): Promise<void> {
  const redirectTo = makeRedirectUri({ scheme: "trustfirstnutrition", path: "auth/callback" });
  if (Platform.OS === "web") {
    const { error } = await client.auth.signInWithOAuth({
      provider: "kakao",
      options: { redirectTo }
    });
    if (error) {
      throw error;
    }
    return;
  }

  const { data, error } = await client.auth.signInWithOAuth({
    provider: "kakao",
    options: { redirectTo, skipBrowserRedirect: true }
  });
  if (error || !data.url) {
    throw error ?? new Error("kakao_authorization_url_missing");
  }
  const result = await WebBrowser.openAuthSessionAsync(data.url, redirectTo);
  if (result.type !== "success") {
    if (result.type === "cancel" || result.type === "dismiss") {
      return;
    }
    throw new Error("kakao_authorization_failed");
  }
  const code = new URL(result.url).searchParams.get("code");
  if (!code) {
    throw new Error("kakao_authorization_code_missing");
  }
  const { error: exchangeError } = await client.auth.exchangeCodeForSession(code);
  if (exchangeError) {
    throw exchangeError;
  }
}
