// Prototype: POST over OpenZiti, authenticating the controller with an external JWT (the GitHub OIDC token).
// Compile-and-size check only. Not run against a live controller.
package main

import (
	"bytes"
	"context"
	"fmt"
	"net"
	"net/http"
	"os"

	edge_apis "github.com/openziti/sdk-golang/edge-apis"
	"github.com/openziti/sdk-golang/ziti"
)

func main() {
	ctrl := os.Getenv("ZITI_CTRL")
	pool, err := ziti.GetControllerWellKnownCaPool(ctrl)
	if err != nil {
		fmt.Fprintln(os.Stderr, "ziti-hook: controller CA:", err)
		os.Exit(1)
	}
	creds := edge_apis.NewJwtCredentials(os.Getenv("ZITI_JWT"))
	creds.CaPool = pool
	cfg := &ziti.Config{ZtAPI: ctrl, Credentials: creds}
	ctx, err := ziti.NewContext(cfg)
	if err != nil {
		fmt.Fprintln(os.Stderr, "ziti-hook:", err)
		os.Exit(1)
	}
	if err := ctx.Authenticate(); err != nil {
		fmt.Fprintln(os.Stderr, "ziti-hook: authenticate:", err)
		os.Exit(1)
	}
	svc := os.Getenv("ZITI_SERVICE")
	client := &http.Client{Transport: &http.Transport{
		DialContext: func(_ context.Context, _, _ string) (net.Conn, error) { return ctx.Dial(svc) },
	}}
	resp, err := client.Post(os.Getenv("HOOK_URL"), "application/json", bytes.NewReader([]byte(os.Getenv("HOOK_BODY"))))
	if err != nil {
		fmt.Fprintln(os.Stderr, "ziti-hook:", err)
		os.Exit(1)
	}
	fmt.Println("ziti-hook: HTTP", resp.StatusCode)
}
