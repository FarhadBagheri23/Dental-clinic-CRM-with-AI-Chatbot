import { API_BASE } from "@/shared/config";

/** Thrown for any non-2xx response. `fields` maps a field name to its
 *  first validation message, so a form can show errors inline. */
export class ApiError extends Error {
  constructor(message, { status, fields = {} } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fields = fields;
  }
}

const GENERIC_ERROR = "ارتباط با سرور برقرار نشد. دوباره تلاش کنید.";

/** FastAPI returns 422 as {detail: [{loc: ["body","username"], msg: "..."}]}.
 *  Pydantic prefixes validator messages with "Value error, " — strip it. */
function parseValidationErrors(detail) {
  const fields = {};
  for (const item of detail) {
    const name = item.loc?.[item.loc.length - 1];
    if (name && !fields[name]) {
      fields[name] = String(item.msg).replace(/^Value error,\s*/, "");
    }
  }
  return fields;
}

export async function request(path, { method = "GET", body, signal } = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      signal,
      // The session is an httpOnly cookie; without this it is never sent.
      credentials: "include",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (cause) {
    if (cause.name === "AbortError") throw cause;
    throw new ApiError(GENERIC_ERROR, { status: 0 });
  }

  if (response.status === 204) return null;

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = payload?.detail;
    if (Array.isArray(detail)) {
      const fields = parseValidationErrors(detail);
      throw new ApiError(Object.values(fields)[0] ?? GENERIC_ERROR, {
        status: response.status,
        fields,
      });
    }
    throw new ApiError(
      typeof detail === "string" ? detail : GENERIC_ERROR,
      { status: response.status },
    );
  }

  return payload;
}

export const http = {
  get: (path, options) => request(path, { ...options, method: "GET" }),
  post: (path, body, options) => request(path, { ...options, method: "POST", body }),
};
