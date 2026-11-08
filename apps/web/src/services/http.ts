export class APIError extends Error {
  constructor(message: string, public code: string, public status: number) { super(message); }
}
/** One abort/deadline boundary; caller cancellation never becomes a visible timeout. */
export async function readJSON<T>(base: string, path: string, signal?: AbortSignal): Promise<T> {
  const timeout = AbortSignal.timeout(10000);
  try {
    const response = await fetch(`${base.replace(/\/$/, '')}${path}`, { signal: signal ? AbortSignal.any([signal, timeout]) : timeout });
    if (!response.ok) {
      let message = `API returned HTTP ${response.status}.`, code = 'HTTP_ERROR';
      try { const body = await response.json(); if (typeof body.error?.message === 'string') message = body.error.message; if (typeof body.error?.code === 'string') code = body.error.code; } catch { /* keep sanitized status */ }
      throw new APIError(message, code, response.status);
    }
    return await response.json() as T;
  } catch (error) {
    if (signal?.aborted) throw error;
    if (timeout.aborted) throw new APIError('The local API took too long to respond.', 'TIMEOUT', 0);
    throw error instanceof Error ? error : new Error('Unable to reach the local API.');
  }
}
