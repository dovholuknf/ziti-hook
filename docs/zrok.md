# Send a webhook over a zrok private share

The receiver has no public endpoint. The workflow dials a zrok private share with a copied zrok environment.

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
     - uses: dovholuknf/ziti-hook@v1
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
