# Send a webhook over OpenZiti

The receiver has no public endpoint. The workflow dials it through your Ziti network with an enrolled identity.

## Why OpenZiti

OpenZiti is an overlay network where every connection is authenticated and authorized before it exists. The receiver
binds a service, and the workflow dials that service with an identity. Nothing listens on the internet, so there is no
URL for a stranger to find, and the receiver makes only outbound connections. You don't need an inbound port, a
firewall rule, dynamic DNS or a public certificate.

The difference from a zrok private share is how narrow the credential is. A zrok environment belongs to a zrok account.
A Ziti identity can dial only what a service policy allows. Here the dial policy lets the identity reach the `ziti-hook`
service and nothing else, so a leaked identity can't be used against any other service on your network. You also revoke
it on its own by deleting the identity, and nothing else changes.

Using OpenZiti isn't free. You need a Ziti network, which means a controller and at least one router, and an admin to
create the service and the policies. If you don't run one, a zrok private share gives you the same hidden receiver
without that setup, since zrok runs the network for you. Choose OpenZiti when you already have a network or want the
narrowest credential. Choose zrok when you want to be running in minutes.

## Set up

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
