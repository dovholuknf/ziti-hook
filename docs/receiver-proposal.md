# ziti-hook receiver proposal

This is a proposal. Atrium is in a code freeze, so nothing here is built in atrium. The receiver is generic and is not
tied to atrium.

## Goal

A small Python service that accepts a POST from the ziti-hook action and hands the body to a handler. It has no public
listener. Callers reach it over OpenZiti or over a zrok private share.

## Transports

| Transport | How it listens | Notes |
| --- | --- | --- |
| OpenZiti | Binds the `ziti-hook` service with the receiver identity | The identity needs a bind policy. |
| zrok private | Serves a private share from an enabled zrok environment | Available only when the host is zrok enabled. |
| localhost | Plain HTTP on `127.0.0.1` | For tests and for local callers. |

Each transport is switched on or off at runtime from a settings dialog, with no restart. The zrok switch is disabled
when the host is not zrok enabled.

## Request handling

1. Read the body up to a size limit, 1 MiB by default.
2. Authenticate the request. See below.
3. Parse by content type. JSON is parsed. Anything else is passed as bytes.
4. Call the handler with the headers, the parsed body and the verified identity of the caller.
5. Return 202 once the handler accepts the work, 401 or 403 on a failed check, 413 when the body is too large.

## Authentication

Two checks, either of which can be required.

- Shared secret. The header `X-Ziti-Hook-Secret` is compared in constant time with the configured secret.
- GitHub OIDC. The `Authorization: Bearer` token is verified against the JWKS of
  `https://token.actions.githubusercontent.com`. The receiver checks `iss`, `aud`, `exp` and `nbf`, then checks
  `repository` (or `repository_id`) against an allow list. It can also check `job_workflow_ref` to pin one workflow
  file. Do not match on `sub`, which changes with the branch, pull request and environment.

The transport already restricts who can connect. These checks identify which workflow sent the request.

## Replay

Record the token `jti` for its lifetime and reject a repeat. Without OIDC, the secret header gives no replay
protection, so the receiver can also accept a `X-Ziti-Hook-Id` header and reject a repeated id inside a window.

## Configuration

One YAML file: the enabled transports, the Ziti identity path, the zrok environment path and share token, the secret,
the OIDC audience and the repository allow list. The settings dialog edits this file and applies it live.

## Out of scope

Handlers themselves, retries from the sender, and any storage of payloads.

## Open

- Which handler interface atrium needs, once the freeze lifts.
- Whether the zrok SDK in Python can serve a private share without the account token.
