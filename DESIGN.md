# ziti-hook design

A GitHub Action that POSTs an arbitrary payload to a webhook receiver with no public endpoint. The receiver is
generic and is not tied to atrium. Two transports: a zrok private share, and pure OpenZiti.

Repo name: `ziti-hook`, used as `uses: dovholuknf/ziti-hook@v1`.

## Decisions so far

- The payload is arbitrary. The action sends the raw GitHub event JSON by default and lets the workflow supply its own
  body and content type.
- The receiver is Python, not Go. It is a proposal only, because atrium is in a code freeze.
- The receiver has two transports, OpenZiti and zrok private. Each is switchable at runtime from a settings dialog
  with no restart. It also listens on localhost. The zrok switch is available only when the hub is zrok enabled.
  No further zrok support is built in atrium for now.
- The zrok credential is a copied environment, not an account token. A bootstrap script runs `zrok enable` once with
  `ZROK2_HOME` pointed at a temp folder and collects the files from there, never from the user's real `~/.zrok2`.
  The user stores the result as a GitHub secret. The action lays the files down on the runner, so there is no
  enable or disable per run.
- The receiver also checks a shared secret header.

## OpenZiti half

Created on `ocictrl` on 2026-10-17:

| Object | Name | Notes |
| --- | --- | --- |
| intercept.v1 config | `ziti-hook.intercept` | `ziti-hook.ziti:80` |
| service | `ziti-hook` | attribute `ziti-hook-services` |
| bind policy | `ziti-hook-bind` | identities `#atrium-hubs` |
| dial policy | `ziti-hook-dial` | identities `#ziti-hook-dialers` |
| identity | `ziti-hook-gh` | attribute `ziti-hook-dialers`, enrolled, file kept out of the repo |

The action is derived from `zhook.py` in `openziti/ziti-mattermost-action-py`: write the identity secret to a file,
`openziti.load()`, then POST under `@openziti.zitify()`.

## zrok half

The Python SDK (`zrok2`) needs an enabled environment for `CreateAccess`, then `zrok2.dialer.Dialer` to connect.
A share token alone is not enough. Revoke by disabling the environment or regenerating the account token. A
dedicated zrok account limits the damage of a leak to that account.

Open: whether an account-token-free, narrower credential exists. Not verified against the controller code.

## GitHub OIDC instead of stored secrets

Idea: the runner mints a GitHub OIDC token (`permissions: id-token: write`) and that token replaces both the stored
identity and the shared secret. Claims such as `repository`, `ref` and `sub` identify the workflow.

- Ziti side: an `ext-jwt-signer` pointed at `https://token.actions.githubusercontent.com` and its JWKS, an auth
  policy allowing ext-jwt, and an identity whose external id matches the `sub` claim.
- Receiver side: verify the same token against the same JWKS and check `repository` and `sub`.

**Blocker found:** `ziti-sdk-py` has no ext-jwt authentication. It only enrolls from a one-time JWT and loads an
identity file. Options: a spike with the controller REST ext-jwt login, a different client such as
`ziti-edge-tunnel`, or keep the enrolled identity for ziti and use OIDC only on the receiver. None is verified.

For zrok, OIDC can authenticate the POST at the receiver but cannot replace the zrok environment.

### ext-jwt spike, 2026-10-30

Answer: yes in principle, not with the current Python SDK. Verified and unverified parts are separate below.

Verified:

- The `openziti` Python package installed in the action image has no ext-jwt code. A grep for `ext-jwt` and `ext_jwt`
  over the package finds nothing.
- The GitHub token has `iss` `https://token.actions.githubusercontent.com`, a settable `aud`, and a `sub` that varies
  with the trigger: `repo:ORG/REPO:ref:refs/heads/BRANCH`, `repo:ORG/REPO:pull_request`,
  `repo:ORG/REPO:environment:ENV`. It also carries `repository`, `repository_id`, `repository_owner`, `ref`,
  `workflow_ref`, `job_workflow_ref` and `run_id`. The JWKS URL is the `jwks_uri` in the discovery document at
  `/.well-known/openid-configuration`.
- A Ziti ext-jwt-signer needs `issuer` equal to the token `iss`, a non-empty `audience` equal to the token `aud`, a
  claims property that maps to the identity external id, and the JWKS endpoint.

Unverified, needs a live controller:

- The controller login. As I recall it is `POST /edge/client/v1/authenticate?method=ext-jwt` with the JWT as a bearer.
  The result is a session token, which the SDK needs to dial.
- Whether the C SDK under the Python wrapper exposes an external-JWT entry point. ziti-sdk-c has ext-jwt login work
  (see #1175 on secondary tokens), but the Python wrapper does not surface it.

Design consequences:

- Do not map `sub`. It changes per branch, PR and environment, so a single identity cannot match it. Map `repository`
  (one identity per repo) or `repository_id`, which survives a rename. Use `repository_id` if the signer can read it.
- Check `job_workflow_ref` on the receiver if the repo must run only one workflow file.
- The token lives minutes. The identity must be created in advance with an external id, not enrolled.
- Set `audience` to a value only Ziti accepts, for example `ziti-hook`, and pass it as the action `audience` input.

Recommended path: keep the enrolled identity for the ziti transport and verify the OIDC token on the receiver now.
That already replaces the shared secret. Revisit ziti-side ext-jwt when the Python SDK exposes it, or by running the
POST through `ziti-edge-tunnel` on the runner, which already supports ext-jwt signers.

## Go client instead of Python (prototype, 2026-10-30)

`proto/main.go` authenticates to the controller with the GitHub OIDC token and POSTs over a Ziti dial. It compiles
and is not run against a live controller.

- `sdk-golang` v1.9.1 has primary ext-jwt auth: `edge_apis.NewJwtCredentials(jwt)` with `AuthMethodJwtExt`, passed in
  `ziti.Config.Credentials`. This removes the Python SDK blocker for the ziti transport.
- A static `linux/amd64` build with `-trimpath -ldflags '-s -w'` is 15.1 MB. Run from `FROM scratch` plus CA
  certificates, the image is about that size. The current image is `python:3.12-slim` plus `openziti` and `zrok2`.
  I did not measure it.
- TinyGo is not installed here. I expect it not to build `sdk-golang`, which uses `net/http`, reflection and protobuf
  heavily. Not tried.
- zrok also has a Go SDK, so one Go binary could serve both transports. Not verified.
- The C SDK route (`ziti-sdk-c` plus a small libuv app) would give the smallest binary. It has ext-jwt support but no
  zrok client, and the HTTP framing and TLS wiring are hand-written. Not tried.
- The prototype does not set the controller CA. A private controller CA needs to be loaded into the credentials. Open.

Docker is not required. A composite action could download the static binary from a release, which skips the image
pull. Both are open.

## Delivered to a new user

- Two short numbered guides, one per transport.
- A bootstrap script for Windows, Linux and macOS that sets the zrok home to a temp folder, enables, collects the
  files and prints the next steps.
- A static setup SPA on GitHub Pages that walks through both transports and prints the commands and the workflow
  snippet. It runs client side and never sees a credential.

## Open

- Receiver authentication: shared secret header first, OIDC after the ziti-py question is answered.
- Live ziti test needs a throwaway listener bound as `sg4-admin`, which needs a bind policy tweak.
