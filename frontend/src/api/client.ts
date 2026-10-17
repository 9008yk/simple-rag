export type HealthResponse = {
  status: string;
};

export type Document = {
  id: string;
  filename: string;
  status: string;
  chunk_count: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

function getErrorMessage(payload: unknown, fallback: string): string {
  if (typeof payload !== "object" || payload === null || !("detail" in payload)) {
    return fallback;
  }

  const detail = (payload as { detail: unknown }).detail;
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === "object" && item !== null && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }
        return "";
      })
      .filter(Boolean);

    if (messages.length > 0) {
      return messages.join("; ");
    }
  }

  return fallback;
}

async function requestError(response: Response, fallback: string): Promise<string> {
  const payload = await response.json().catch(() => null);
  return getErrorMessage(payload, fallback);
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch("/health");

  if (!response.ok) {
    throw new Error(await requestError(response, "后端连接失败。"));
  }

  return response.json();
}

export async function listDocuments(): Promise<Document[]> {
  const response = await fetch("/api/documents");

  if (!response.ok) {
    throw new Error(await requestError(response, "文档列表加载失败。"));
  }

  return response.json();
}

export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/documents", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await requestError(response, "文档上传失败。"));
  }

  return response.json();
}
