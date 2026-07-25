---
name: "api-design-review"
description: "Design and review REST and GraphQL APIs and generate OpenAPI specs. Use when the user asks to design endpoints for a feature, review an API surface for consistency, name routes, pick status codes, version an API, paginate a list endpoint, or produce an openapi.yaml from existing routes. Trigger on REST, endpoint, OpenAPI, swagger, GraphQL schema, status code, versioning, or webhook design."
---

# API Design Review

Design new HTTP APIs, review existing ones, and produce OpenAPI documents.

## Not in scope

Client SDK generation tooling, API gateway/infra configuration, auth protocol implementation details (OAuth flows have their own docs), and gRPC/protobuf design. Security review of an implementation belongs to the security skills; this covers the design surface.

## REST design ground rules

- **Nouns for resources, plural, no verbs in paths.** `POST /orders`, not `POST /createOrder`. Actions that don't map to CRUD become sub-resources: `POST /orders/{id}/cancellation`.
- **Nesting max one level.** `/customers/{id}/orders` is fine; three levels deep means the child should be a top-level resource filtered by query param.
- **Status codes that mean what they say:** 200 read/update, 201 create (with `Location`), 204 delete, 400 malformed, 401 unauthenticated, 403 unauthorized, 404 not found, 409 conflict (duplicate, version clash), 422 valid JSON but failed domain validation, 429 rate limited. Don't return 200 with `{"error": ...}` in the body.
- **Errors are a contract too.** One error envelope everywhere, machine-readable code plus human message. RFC 9457 problem+json is a good default:
  ```json
  { "type": "https://api.example.com/errors/insufficient-funds", "title": "Insufficient funds", "status": 422, "detail": "Balance is 30 credits, transfer needs 50.", "instance": "/transfers/abc123" }
  ```
- **Pagination from day one** on every list endpoint. Cursor-based (`?cursor=...&limit=...` returning `next_cursor`) beats offset for anything that grows. Never return an unbounded list.
- **Idempotency:** PUT and DELETE are idempotent by definition; make POST safe to retry with an `Idempotency-Key` header where money or side effects are involved.
- **Timestamps** ISO 8601 UTC. IDs opaque strings (prefixed IDs like `ord_abc123` age well). Field naming one convention everywhere (pick snake_case or camelCase and stop).
- **Versioning:** path prefix `/v1/` is the boring, visible, cache-friendly default. Add fields freely (additive is not breaking); removing or changing a field's meaning requires a new version. Sunset headers and a dated deprecation policy beat surprise removals.

## Review checklist for an existing API

1. Consistency first: same resource named the same way in every path, same envelope, same pagination shape, same error format. Inconsistency costs integrators more than any single bad choice.
2. Can every list grow unbounded? Find endpoints without pagination.
3. Grep for verbs in paths and 200-with-error responses.
4. Anything returning different shapes for the same resource in different endpoints?
5. Are write endpoints safe to retry? What happens on double-submit?
6. Does the API leak internals (database column names, incrementing integer IDs, stack traces in errors)?
7. Breaking-change audit: would renaming/removing anything here break a client silently?

## GraphQL notes

- Schema is the contract; design types from the client's screens, not the database.
- Every list field takes `first`/`after` (Relay-style connections) from the start.
- Mutations return the mutated object plus a `userErrors` field; don't throw for domain validation.
- N+1 resolvers are the default failure mode; require a dataloader/batching story before shipping.
- Deprecate with `@deprecated(reason:)`; never repurpose a field's meaning.

## Producing an OpenAPI spec

Work from the routes actually registered in the code, not from memory. For each: method, path, params, request body schema, response schemas per status code, and the error envelope. Mark auth via `securitySchemes` once and reference it. Validate the result (`npx @redocly/cli lint openapi.yaml` or `swagger-cli validate`) before handing it over, and keep examples in the spec for every non-obvious body.
