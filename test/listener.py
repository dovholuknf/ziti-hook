"""Test receiver. Binds the ziti-hook service with an identity, prints what it gets and checks the shared secret."""
import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


def make_handler(secret, header, log):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            if secret and self.headers.get(header) != secret:
                self.send_response(401)
                self.end_headers()
                return
            log.append({"path": self.path, "headers": dict(self.headers), "body": body.decode(errors="replace")})
            print("received %d bytes on %s, bearer=%s" % (len(body), self.path, "Authorization" in self.headers),
                  flush=True)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *a):
            pass

    return Handler


def serve_ziti(identity, service, handler):
    """Bind `service` with the identity and serve HTTP on it."""
    import openziti

    ztx, err = openziti.load(identity)
    if err:
        sys.exit("load failed: %s" % err)
    with openziti.monkeypatch(bindings={("0.0.0.0", 80): {"ztx": ztx, "service": service}}):
        srv = HTTPServer(("0.0.0.0", 80), handler)
    print("bound service %s" % service, flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--identity", help="bind identity JSON (omit to listen on localhost)")
    ap.add_argument("--service", default="ziti-hook")
    ap.add_argument("--secret", default="")
    ap.add_argument("--secret-header", default="X-Ziti-Hook-Secret")
    ap.add_argument("--port", type=int, default=8080)
    a = ap.parse_args()
    handler = make_handler(a.secret, a.secret_header, [])
    if a.identity:
        serve_ziti(a.identity, a.service, handler)
    else:
        HTTPServer(("127.0.0.1", a.port), handler).serve_forever()
