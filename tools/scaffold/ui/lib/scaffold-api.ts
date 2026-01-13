export const API_BASE =
  process.env.NEXT_PUBLIC_SCAFFOLD_API_URL ?? "http://127.0.0.1:8001";

export async function fetchJson(path: string, options?: RequestInit) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data?.detail ?? "Request failed");
  }
  return data;
}
