/*
 * Prototype: POST over OpenZiti from C, authenticating to the controller with an external JWT (the GitHub OIDC token).
 * Config comes from the environment: ZITI_CTRL, ZITI_JWT, ZITI_SERVICE, HOOK_URL, HOOK_BODY, optional ZITI_SIGNER.
 * Not run against a live controller.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <uv.h>
#include <tlsuv/tlsuv.h>
#include <tlsuv/http.h>
#include <ziti/ziti.h>
#include <ziti/ziti_src.h>
#include <ziti/ziti_log.h>

static uv_loop_t *loop;
static ziti_context ziti;
static tlsuv_http_t clt;
static tlsuv_src_t zs;
static int exit_code = 1;

static const char *need(const char *name) {
    const char *v = getenv(name);
    if (!v || !*v) {
        fprintf(stderr, "ziti-hook: %s is not set\n", name);
        exit(2);
    }
    return v;
}

static void fail(const char *what, int rc) {
    fprintf(stderr, "ziti-hook: %s: %s\n", what, ziti_errorstr(rc));
    exit(1);
}

static void resp_cb(tlsuv_http_resp_t *resp, void *data) {
    (void) data;
    if (resp->code < 0) {
        fprintf(stderr, "ziti-hook: request: %s\n", uv_strerror(resp->code));
        exit(1);
    }
    printf("ziti-hook: HTTP %d\n", resp->code);
    exit_code = resp->code < 300 ? 0 : 1;
}

static void body_cb(tlsuv_http_req_t *req, char *body, ssize_t len) {
    (void) req;
    (void) body;
    if (len == UV_EOF) {
        ziti_shutdown(ziti);
    }
}

static void send_hook(ziti_context ztx) {
    const char *payload = need("HOOK_BODY");
    ziti = ztx;
    ziti_src_init(loop, &zs, need("ZITI_SERVICE"), ztx);
    tlsuv_http_init_with_src(loop, &clt, need("HOOK_URL"), (tlsuv_src_t *) &zs);
    tlsuv_http_req_t *r = tlsuv_http_req(&clt, "POST", "/", resp_cb, NULL);
    tlsuv_http_req_header(r, "Content-Type", "application/json");
    tlsuv_http_req_data(r, payload, strlen(payload), NULL);
    r->resp.body_cb = body_cb;
}

static void on_auth(ziti_context ztx, const struct ziti_auth_event *ev) {
    const char *want = getenv("ZITI_SIGNER");
    int rc;
    switch (ev->action) {
        case ziti_auth_select_external:
            if (!want && ev->providers[0]) want = ev->providers[0]->name;
            if (!want) fail("no ext-jwt signer offered", ZITI_NOT_FOUND);
            rc = ziti_use_ext_jwt_signer(ztx, want);
            if (rc != ZITI_OK) fail("select signer", rc);
            break;
        case ziti_auth_login_external:
            rc = ziti_ext_auth_token(ztx, need("ZITI_JWT"));
            if (rc != ZITI_OK) fail("submit token", rc);
            break;
        default:
            fprintf(stderr, "ziti-hook: unexpected auth action %d\n", ev->action);
            exit(1);
    }
}

static void on_event(ziti_context ztx, const ziti_event_t *ev) {
    switch (ev->type) {
        case ZitiAuthEvent:
            on_auth(ztx, &ev->auth);
            break;
        case ZitiContextEvent:
            if (ev->ctx.ctrl_status == ZITI_OK) send_hook(ztx);
            else if (ev->ctx.ctrl_status != ZITI_PARTIALLY_AUTHENTICATED && ev->ctx.ctrl_status != ZITI_WTF)
                fail("controller", ev->ctx.ctrl_status);
            break;
        default:
            break;
    }
}

/* The controller CA is private, so fetch it from the controller's EST endpoint (trust on first use). */
typedef struct {
    char *buf;
    size_t len;
    int code;
} ca_fetch_t;

static int trust_any(const struct tlsuv_certificate_s *cert, void *ctx) {
    (void) cert;
    (void) ctx;
    return 0;
}

static void ca_body_cb(tlsuv_http_req_t *r, char *body, ssize_t len) {
    ca_fetch_t *f = r->data;
    if (len > 0) {
        f->buf = realloc(f->buf, f->len + len + 1);
        memcpy(f->buf + f->len, body, len);
        f->len += len;
        f->buf[f->len] = 0;
    }
}

static void ca_resp_cb(tlsuv_http_resp_t *resp, void *data) {
    ca_fetch_t *f = data;
    f->code = resp->code;
    resp->body_cb = ca_body_cb;
}

static char *fetch_ca(const char *ctrl) {
    ca_fetch_t f = {0};
    tls_context *tls = default_tls_context();
    tls->set_cert_verify(tls, trust_any, NULL);

    tlsuv_http_t h;
    tlsuv_http_init(loop, &h, ctrl);
    tlsuv_http_set_ssl(&h, tls);
    tlsuv_http_req_t *r = tlsuv_http_req(&h, "GET", "/.well-known/est/cacerts", ca_resp_cb, &f);
    r->data = &f;
    uv_run(loop, UV_RUN_DEFAULT);
    tlsuv_http_close(&h, NULL);
    uv_run(loop, UV_RUN_DEFAULT);

    char *pem = NULL;
    if (f.code == 200 && f.buf) {
        tlsuv_certificate_t chain = NULL;
        size_t pem_len = 0;
        if (tls->parse_pkcs7_certs(&chain, f.buf, f.len) == 0) {
            chain->to_pem(chain, 1, &pem, &pem_len);
            chain->free(chain);
        }
    }
    free(f.buf);
    tls->free_ctx(tls);
    if (!pem) {
        fprintf(stderr, "ziti-hook: could not fetch the controller CA (HTTP %d)\n", f.code);
        exit(1);
    }
    return pem;
}

int main(void) {
    const char *ctrl = need("ZITI_CTRL");
    need("ZITI_JWT");
    need("ZITI_SERVICE");
    need("HOOK_URL");
    need("HOOK_BODY");

    loop = uv_default_loop();
    char *ca = fetch_ca(ctrl);

    ziti_config cfg = {.controller_url = (char *) ctrl};
    cfg.id.ca = ca;
    ziti_context ztx;
    int rc = ziti_context_init(&ztx, &cfg);
    if (rc != ZITI_OK) fail("init", rc);
    rc = ziti_context_set_options(ztx, &(ziti_options){.event_cb = on_event, .events = ZitiContextEvent | ZitiAuthEvent});
    if (rc != ZITI_OK) fail("options", rc);
    rc = ziti_context_run(ztx, loop);
    if (rc != ZITI_OK) fail("run", rc);

    uv_run(loop, UV_RUN_DEFAULT);
    return exit_code;
}
