# ziti-hook design

A GitHub Action that POSTs an arbitrary payload to a webhook receiver with no public endpoint. The receiver is
generic and is not tied to atrium. Two transports: a zrok private share, and pure OpenZiti.

Repo name: `ziti-hook`, used as `uses: dovholuknf/ziti-hook@main`.

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

## Delivered to a new user

- Two short numbered guides, one per transport.
- A bootstrap script for Windows, Linux and macOS that sets the zrok home to a temp folder, enables, collects the
  files and prints the next steps.
- A static setup SPA on GitHub Pages that walks through both transports and prints the commands and the workflow
  snippet. It runs client side and never sees a credential.

## Open

- Receiver authentication: shared secret header first, OIDC after the ziti-py question is answered.
- Live ziti test needs a throwaway listener bound as `sg4-admin`, which needs a bind policy tweak.
