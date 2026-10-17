"""POST a payload to a webhook receiver that has no public endpoint, over OpenZiti or a zrok private share."""
import base64
import io
import json
import os
import posixpath
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request


def inp(name, default=""):
    return os.environ.get("INPUT_" + name.upper().replace("-", "_"), default).strip()


def build_payload():
    """Return (body bytes, content type). The default body is the raw GitHub event JSON."""
    body = inp("payload")
    ctype = inp("content-type", "application/json")
    if body:
        return body.encode(), ctype
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if event_path and os.path.exists(event_path):
        with open(event_path, "rb") as f:
            return f.read(), "application/json"
    return json.dumps({"event": os.environ.get("GITHUB_EVENT_NAME", "")}).encode(), "application/json"


def oidc_token(audience):
    """Mint a GitHub OIDC token. Return "" when the workflow lacks `id-token: write`."""
    url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL")
    tok = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    if not url or not tok:
        return ""
    if audience:
        url += "&audience=" + urllib.parse.quote(audience)
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + tok})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["value"]


def build_headers(ctype, audience):
    headers = {"Content-Type": ctype, "User-Agent": "ziti-hook"}
    for line in inp("headers").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip()] = v.strip()
    secret = inp("secret")
    if secret:
        headers[inp("secret-header", "X-Ziti-Hook-Secret")] = secret
    token = oidc_token(audience)
    if token:
        headers["Authorization"] = "Bearer " + token
    else:
        print("ziti-hook: no OIDC token available (grant `id-token: write` to send one)")
    return headers


def write_secret(path, text):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(text)


def post_ziti(url, body, headers):
    import openziti

    identity = inp("ziti-identity")
    if not identity:
        sys.exit("ziti-hook: input ziti-identity is required for transport ziti")
    path = os.path.join(tempfile.mkdtemp(prefix="ziti-hook-"), "identity.json")
    write_secret(path, identity)
    _, err = openziti.load(path)
    if err:
        sys.exit("ziti-hook: could not load the ziti identity, error %s" % err)
    try:
        with openziti.monkeypatch():
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=int(inp("timeout", "30"))) as r:
                return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    finally:
        os.remove(path)


def lay_down_zrok_env(blob):
    """Unpack the bootstrap tarball to <tmp>/.zrok2 and point HOME there, where the zrok SDK looks for it."""
    home = tempfile.mkdtemp(prefix="zrok2-")
    root = os.path.join(home, ".zrok2")
    with tarfile.open(fileobj=io.BytesIO(base64.b64decode(blob)), mode="r:gz") as t:
        for m in t.getmembers():
            name = posixpath.normpath(m.name)
            if m.isdir():
                continue
            if not m.isfile() or name.startswith(("/", "..")):
                sys.exit("ziti-hook: unexpected entry in zrok-env: " + m.name)
            dest = os.path.join(root, *name.split("/"))
            os.makedirs(os.path.dirname(dest), mode=0o700, exist_ok=True)
            write_secret(dest, t.extractfile(m).read().decode())
    os.environ["HOME"] = os.environ["USERPROFILE"] = home
    return home


def post_zrok(url, body, headers):
    blob = inp("zrok-env")
    token = inp("zrok-share-token")
    if not blob or not token:
        sys.exit("ziti-hook: inputs zrok-env and zrok-share-token are required for transport zrok")
    lay_down_zrok_env(blob)
    import zrok2.dialer as zdial
    from zrok2 import model
    from zrok2.access import Access
    from zrok2.environment.root import Load

    u = urllib.parse.urlsplit(url)
    path = (u.path or "/") + ("?" + u.query if u.query else "")
    head = "POST %s HTTP/1.1\r\nHost: %s\r\nContent-Length: %d\r\nConnection: close\r\n" % (path, u.netloc, len(body))
    head += "".join("%s: %s\r\n" % kv for kv in headers.items()) + "\r\n"
    root = Load()
    with Access(root, model.AccessRequest(ShareToken=token)):
        conn = zdial.Dialer(token, root)
        conn.sendall(head.encode() + body)
        raw = b""
        while True:
            chunk = conn.recv(65536)
            if not chunk:
                break
            raw += chunk
        conn.close()
    status_line, _, rest = raw.partition(b"\r\n")
    return int(status_line.split()[1]), rest.partition(b"\r\n\r\n")[2]


def main():
    transport = inp("transport", "ziti")
    url = inp("url")
    if not url:
        sys.exit("ziti-hook: input url is required")
    body, ctype = build_payload()
    headers = build_headers(ctype, inp("audience"))
    if transport == "ziti":
        status, resp = post_ziti(url, body, headers)
    elif transport == "zrok":
        status, resp = post_zrok(url, body, headers)
    else:
        sys.exit("ziti-hook: transport must be ziti or zrok, got " + transport)
    print("ziti-hook: %s -> HTTP %d" % (transport, status))
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write("status=%d\n" % status)
    if status >= 300:
        print(resp.decode(errors="replace")[:2000])
        sys.exit(1)


if __name__ == "__main__":
    main()
