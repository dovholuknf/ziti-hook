# ziti-hook

A GitHub Action that POSTs a payload to a webhook receiver that has no public endpoint. It reaches the receiver over
OpenZiti or over a zrok private share. By default it sends the raw GitHub event JSON, and it can send any body you give
it.

```yaml
permissions:
  id-token: write   # optional, sends a GitHub OIDC token as a bearer
steps:
  - uses: dovholuknf/ziti-hook@main
    with:
      transport: ziti            # or zrok
      url: http://ziti-hook.ziti/
      ziti-identity: ${{ secrets.ZITI_IDENTITY }}
      secret: ${{ secrets.HOOK_SECRET }}
```

## Which transport

OpenZiti and a zrok private share both keep the receiver off the public internet. Nothing listens for strangers, so
only a credential holder can reach it. A public zrok share is easier but exposes a URL. See
[why a private share](docs/zrok.md#why-a-private-share) for the tradeoff.

## Set up

- [OpenZiti guide](docs/openziti.md)
- [zrok guide](docs/zrok.md)

## Inputs

| Input | Meaning |
| --- | --- |
| `transport` | `ziti` or `zrok`. Default `ziti`. |
| `url` | Receiver URL. For ziti, the intercept address. For zrok, only the path and Host header are used. |
| `payload`, `content-type` | Request body and its type. Default is the raw GitHub event JSON. |
| `headers` | Extra headers, one `Name: value` per line. |
| `secret`, `secret-header` | Shared secret and the header that carries it. Default `X-Ziti-Hook-Secret`. |
| `audience` | Audience for the GitHub OIDC token. |
| `timeout` | Request timeout in seconds. Default 30. |
| `ziti-identity` | Enrolled OpenZiti identity JSON. Transport `ziti` only. |
| `zrok-env`, `zrok-share-token` | Output of `scripts/bootstrap-zrok` and the private share token. Transport `zrok` only. |

The action sets the output `status` to the HTTP status code and fails the step on any status of 300 or more.

## Layout

- `action.yml`, `Dockerfile`, `src/ziti_hook.py`: the action
- `scripts/bootstrap-zrok.sh`, `scripts/bootstrap-zrok.ps1`: build the `zrok-env` secret in a temp home
- `test/listener.py`: a test receiver that binds the Ziti service
- `test/live-ziti.ps1`: sends through a live Ziti network to the test receiver
- `DESIGN.md`: decisions and open questions

## Security

The Ziti identity and the zrok environment are credentials. Store them only as GitHub secrets and never commit them.
