/** An API call that did not succeed. Carries a human-readable message and,
 *  when present, the backend's machine-readable error code and field errors. */
export class ApiError extends Error {
  readonly status: number
  readonly code: string | undefined
  readonly fieldErrors: Record<string, string[]>

  constructor(
    message: string,
    status: number,
    code?: string,
    fieldErrors: Record<string, string[]> = {},
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.fieldErrors = fieldErrors
  }
}

type DrfError = Record<string, unknown> & {
  detail?: unknown
  code?: unknown
}

/**
 * Turn a DRF error body into an ApiError. DRF returns either `{detail, code}`
 * or a map of field -> [messages]; this normalises both so callers and forms
 * get a top-level message plus per-field messages.
 */
export function toApiError(body: unknown, status: number): ApiError {
  if (body && typeof body === 'object') {
    const data = body as DrfError
    const code = typeof data.code === 'string' ? data.code : undefined

    if (typeof data.detail === 'string') {
      return new ApiError(data.detail, status, code)
    }

    const fieldErrors: Record<string, string[]> = {}
    for (const [key, value] of Object.entries(data)) {
      if (key === 'code') continue
      if (Array.isArray(value)) {
        fieldErrors[key] = value.map(String)
      } else if (typeof value === 'string') {
        fieldErrors[key] = [value]
      }
    }
    const first = Object.values(fieldErrors)[0]?.[0]
    if (first) return new ApiError(first, status, code, fieldErrors)
  }

  return new ApiError(defaultMessage(status), status)
}

function defaultMessage(status: number): string {
  if (status === 0) return 'Could not reach the server. Check your connection.'
  if (status === 429) return 'Too many requests. Please wait a moment.'
  if (status >= 500)
    return 'Something went wrong on our end. Try again shortly.'
  if (status === 404) return 'Not found.'
  return 'Request failed.'
}

/**
 * Unwrap an openapi-fetch result, throwing an ApiError on failure.
 *
 * The generated schema only documents 200 responses, so openapi-fetch types
 * every result as success-only (its `error` field is `undefined` at the type
 * level). We therefore branch on the real `response.ok`, not on `error`, and
 * read the error body from `error` (populated at runtime whenever the response
 * is not ok).
 */
export function unwrap<T>(result: {
  data?: T
  error?: unknown
  response: Response
}): T {
  if (result.response.ok) {
    return result.data as T
  }
  throw toApiError(result.error, result.response.status)
}
