export const MAX_ANALYSIS_POLL_ATTEMPTS = 5;

export function pollDelayMs(attempt: number): number {
  return Math.min(3000, 500 * attempt);
}

export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}
