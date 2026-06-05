# {{API_NAME}} API — v{{VERSION}}

- **Base URL:** `{{BASE_URL}}`
- **Status:** {{STATUS}}
- **Last updated:** {{DATE}}

## Overview

{{OVERVIEW}}

What the API does, who it's for, and at a high level how to use it.

## Authentication

{{AUTHENTICATION}}

```bash
curl -H "Authorization: Bearer $TOKEN" https://api.example.com/v1/resource
```

## Error Model

{{ERROR_MODEL}}

All errors return a consistent JSON shape:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "The 'name' field is required",
    "details": { "field": "name" }
  }
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request — invalid input |
| 401 | Unauthorized — missing or invalid token |
| 403 | Forbidden — token valid but lacks permission |
| 404 | Not found |
| 429 | Rate limited |
| 5xx | Server error |

## Rate Limiting

{{RATE_LIMITING}}

- **Limit:** {{LIMIT}} requests per {{WINDOW}}
- **Headers:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- **Retry:** Exponential backoff when you receive 429

## Versioning

{{VERSIONING}}

- API is versioned via URL path (`/v1/...`, `/v2/...`)
- Breaking changes require a new major version
- Old versions supported for 12 months after deprecation

## Endpoints

### `{{METHOD_1}} {{ENDPOINT_1}}`

{{ENDPOINT_1_DESC}}

**Request:**

```json
{
  "field": "value"
}
```

**Response (200):**

```json
{
  "id": "abc",
  "field": "value"
}
```

### `{{METHOD_2}} {{ENDPOINT_2}}`

{{ENDPOINT_2_DESC}}

## Schemas

{{SCHEMAS}}

### `Resource`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier |
| `name` | string | Yes | Display name |
| `created_at` | string (ISO 8601) | Yes | Creation timestamp |

## Examples

### curl

```bash
curl -X POST https://api.example.com/v1/resources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Resource"}'
```

### Python

```python
import requests
response = requests.post(
    "https://api.example.com/v1/resources",
    headers={"Authorization": f"Bearer {token}"},
    json={"name": "My Resource"},
)
response.raise_for_status()
print(response.json())
```

### JavaScript

```javascript
const response = await fetch("https://api.example.com/v1/resources", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ name: "My Resource" }),
});
const data = await response.json();
```

## Webhooks

{{WEBHOOKS}}

Webhooks are signed with HMAC-SHA256:

```
X-Signature: sha256={{SIGNATURE}}
```

## SDKs & Libraries

{{SDKS}}

- Python: `pip install {{PYTHON_SDK}}`
- JavaScript: `npm install {{JS_SDK}}`
- Go: `go get {{GO_SDK}}`

## Changelog

{{CHANGELOG}}

- **v1.0.0** — Initial release
- **v1.1.0** — Added X endpoint
- **v2.0.0** — Breaking change in Y
