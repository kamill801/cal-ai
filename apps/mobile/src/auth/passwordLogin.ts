export interface PasswordAuthClient {
  auth: {
    signInWithPassword(input: { email: string; password: string }): PromiseLike<{ error: unknown }>;
  };
}

export async function signInWithPassword(client: PasswordAuthClient, email: string, password: string): Promise<void> {
  const normalizedEmail = email.trim();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail) || !password) {
    throw new Error("이메일과 비밀번호를 확인해 주세요.");
  }
  try {
    const { error } = await client.auth.signInWithPassword({ email: normalizedEmail, password });
    if (error) throw error;
  } catch {
    // Do not forward provider errors, which may contain request or account details.
    throw new Error("로그인하지 못했어요. 입력한 정보를 확인하고 다시 시도해 주세요.");
  }
}
