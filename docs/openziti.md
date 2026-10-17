# Send a webhook over OpenZiti

The receiver has no public endpoint. The workflow dials it through your Ziti network with an enrolled identity.

1. Ask the network admin for three things: a service for the receiver, a dial policy for a new identity, and the
   enrollment JWT of that identity. In this deployment the service is `ziti-hook`, reached at `http://ziti-hook.ziti/`.
2. Enroll the identity once on your machine:

   ```
   ziti edge enroll --jwt ziti-hook-gh.jwt --out ziti-hook-gh.json
   ```

3. Store the full contents of `ziti-hook-gh.json` as the repository secret `ZITI_IDENTITY`. Delete the local file and
   never commit it. Anyone holding it can dial the service.
4. Pick a shared secret for the receiver and store it as `HOOK_SECRET`. Configure the same value on the receiver.
5. Add the step to a workflow:

   ```yaml
   permissions:
     id-token: write   # optional, sends a GitHub OIDC token as a bearer
   steps:
     - uses: dovholuknf/ziti-hook@main
       with:
         transport: ziti
         url: http://ziti-hook.ziti/
         ziti-identity: ${{ secrets.ZITI_IDENTITY }}
         secret: ${{ secrets.HOOK_SECRET }}
   ```

   Without `payload` the action sends the raw GitHub event JSON. Set `payload` and `content-type` to send your own.

To revoke access, delete the identity or its dial policy on the controller.
