export function ownerScope(authEnabled: boolean, userId?: string): string {
  return authEnabled ? (userId ? `user:${userId}` : "signed-out") : "local";
}

export function ownerStorageKey(base: string, scope: string): string {
  return scope === "local" ? base : `${base}/${encodeURIComponent(scope)}`;
}
