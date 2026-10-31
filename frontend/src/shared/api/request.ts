export interface ApiErrorBody {
  code: string;
  message: string;
  details: unknown;
}

/** Ошибка бэкенда в едином формате `{ error: { code, message, details } }`. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: unknown;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.status = status;
    this.code = body.code;
    this.details = body.details;
  }
}

function parseError(status: number, payload: unknown): ApiError {
  if (payload && typeof payload === "object" && "error" in payload) {
    const error = (payload as { error: Partial<ApiErrorBody> }).error;
    return new ApiError(status, {
      code: error.code ?? "UNKNOWN",
      message: error.message ?? "Ошибка сервера",
      details: error.details ?? null,
    });
  }
  if (status === 404 || status === 405) {
    // Ответ не нашего формата: маршрута нет. Обычно на порту запущена старая версия бэкенда.
    return new ApiError(status, {
      code: "ROUTE_NOT_FOUND",
      message:
        "Бэкенд не знает этот запрос. Похоже, на порту 8000 запущена старая версия: остановите её " +
        "(в том числе Docker-контейнер) и запустите backend заново.",
      details: payload,
    });
  }
  if (status === 422 && payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    const fields = Array.isArray(detail)
      ? detail
          .map((item: { loc?: unknown[]; msg?: string }) =>
            `${(item.loc ?? []).filter((part) => part !== "body").join(".")}: ${item.msg ?? ""}`,
          )
          .join("; ")
      : String(detail);
    return new ApiError(status, {
      code: "VALIDATION_ERROR",
      message: `Сервер не принял данные: ${fields}`,
      details: detail,
    });
  }
  if (status >= 500) {
    return new ApiError(status, {
      code: "SERVER_UNAVAILABLE",
      message: "Бэкенд не отвечает. Проверьте, что он запущен: uv run python main.py в папке backend.",
      details: payload,
    });
  }
  return new ApiError(status, {
    code: "HTTP_ERROR",
    message: `Сервер ответил ${status}`,
    details: null,
  });
}

export async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...init.headers,
    },
  });

  if (response.status === 204) return undefined as T;

  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) throw parseError(response.status, payload);
  return payload as T;
}

export function jsonBody(data: unknown): RequestInit {
  return { method: "POST", body: JSON.stringify(data) };
}

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Неизвестная ошибка";
}
