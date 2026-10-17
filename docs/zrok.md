# Send a webhook over a zrok private share

The receiver has no public endpoint. The workflow dials a zrok private share with a copied zrok environment.

## Why a private share

A public zrok share is the easy option. You run one command and the receiver gets a public URL that GitHub can reach.
For a webhook that is often fine, but the URL is on the open internet, so anyone who finds it can send it traffic.
Your only defense is the receiver itself. That means a shared secret, basic auth or OAuth, and however well the
receiver handles a request from a stranger.

A private share has no URL. Nothing listens on the internet and nothing answers a port scan. Only an environment that
zrok has granted access to the share can reach it. A request from anyone else never arrives, so the receiver doesn't
have to survive it. The receiver also makes only outbound connections, so you don't open an inbound port and you need
no firewall rule, dynamic DNS or certificate.

The cost is a credential. A public share needs only a secret header, but a private share needs the copied zrok
environment on the runner, and that environment is a real credential. Use a dedicated zrok account so a leak exposes
only that account. You revoke it by disabling the environment. The shared secret header stays as a second check at the
receiver.

Choose public when you want the least setup and the receiver can defend itself. Choose private when the receiver
must stay off the internet.

## Set up

1. Use a dedicated zrok account for this. A leaked environment then exposes only that account.
2. Install `zrok2` and get the account token of the dedicated account.
3. Run the bootstrap script. It runs `zrok2 enable` with `HOME` pointed at a temp folder, so your own
   `~/.zrok2` is not touched, then prints the environment as one base64 string:

   ```
   ./scripts/bootstrap-zrok.sh <account-token>
   ```

   On Windows use `./scripts/bootstrap-zrok.ps1 -Token <account-token>`.
4. Store the printed string as the repository secret `ZROK_ENV`.
5. On the receiver machine create a private share and store its token as `ZROK_SHARE_TOKEN`.
6. Pick a shared secret, store it as `HOOK_SECRET` and configure the same value on the receiver.
7. Add the step to a workflow:

   ```yaml
   permissions:
     id-token: write   # optional, sends a GitHub OIDC token as a bearer
   steps:
     - uses: dovholuknf/ziti-hook@main
       with:
         transport: zrok
         url: http://hook/
         zrok-env: ${{ secrets.ZROK_ENV }}
         zrok-share-token: ${{ secrets.ZROK_SHARE_TOKEN }}
         secret: ${{ secrets.HOOK_SECRET }}
   ```

   The `url` only supplies the request path and Host header. The share token picks the destination.

To revoke access, run `zrok2 disable` for the environment or regenerate the account token.
A share token alone cannot dial. The environment is required.
