# Send a webhook over a zrok private share

The receiver has no public endpoint. The workflow dials a zrok private share with a copied zrok environment.

## Why a private share

A zrok private share is a share that has no public URL. Only a zrok environment that has been granted access can reach
it, and the receiver behind it makes only outbound connections. A public share is easier. You run one command and GitHub
reaches the receiver at a public URL. That URL is on the open internet though, so anyone who finds it can send it
traffic. Your only defense is the receiver, and it has to cope with whatever a stranger sends.

With a private share nothing listens on the internet and nothing answers a port scan. A request from anyone else never
arrives, so the receiver doesn't have to deal with it. There is no need to open an inbound port, no need for a firewall
rule, and no need for dynamic DNS or a certificate.

Using a private share isn't free, because it costs you a credential. A public share needs only a secret header, but a
private share needs the copied zrok environment on the runner, and that environment can dial your share. You should use
a dedicated zrok account so a leak exposes only that account, and you revoke it by disabling the environment. The shared
secret header still works as a second check at the receiver.

Choose a public share when you want the least setup and the receiver can defend itself. Choose a private share when the
receiver **must** stay off the internet.

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
