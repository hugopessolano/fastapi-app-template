export const API_BASE =
  process.env.NEXT_PUBLIC_SCAFFOLD_API_URL ?? "http://127.0.0.1:8001";

export type ScaffoldRequestInit = RequestInit & {
  projectId?: string | null;
};

export async function fetchJson(path: string, options?: ScaffoldRequestInit) {
  const { projectId, ...fetchOptions } = options ?? {};
  const headers = new Headers(fetchOptions.headers);
  headers.set("Content-Type", "application/json");
  if (projectId) {
    headers.set("X-Scaffold-Project", projectId);
  }
  const response = await fetch(`${API_BASE}${path}`, {
    headers,
    cache: "no-store",
    ...fetchOptions,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data?.detail ?? "Request failed");
  }
  return data;
}
