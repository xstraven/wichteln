export type ParticipantPayload = {
  name: string;
};

export type IllegalPairPayload = {
  giver: string;
  receiver: string;
};

export type CreateGroupPayload = {
  identifier: string;
  participants: ParticipantPayload[];
  illegalPairs: IllegalPairPayload[];
  description?: string;
};

export type GroupCreateResponse = {
  identifier: string;
  participantCount: number;
  illegalPairCount: number;
};

export type RevealResponse = {
  identifier: string;
  participantName: string;
  recipientName: string;
};

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(
  /\/$/,
  "",
) || "";

const defaultHeaders: HeadersInit = {
  "Content-Type": "application/json",
};

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { ...defaultHeaders, ...(init.headers ?? {}) },
  });

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const payload = isJson ? await response.json() : null;

  if (!response.ok) {
    const detail =
      payload?.detail ??
      payload?.message ??
      `Unexpected error (${response.status}) while contacting the elves.`;
    throw new ApiError(detail, response.status);
  }

  return payload as T;
}

export async function createGroup(payload: CreateGroupPayload): Promise<GroupCreateResponse> {
  return request<GroupCreateResponse>("/api/groups", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function revealMatch(
  identifier: string,
  name: string,
): Promise<RevealResponse> {
  return request<RevealResponse>(`/api/groups/${encodeURIComponent(identifier)}/reveal`, {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export async function fetchIdentifier(): Promise<string> {
  const response = await request<{ identifier: string }>("/api/identifier", {
    method: "GET",
  });
  return response.identifier;
}

export { ApiError };
