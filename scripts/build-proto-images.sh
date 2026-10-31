#!/usr/bin/env bash
# Builds the Go and C ziti-hook prototype images and prints the size of each.
# Usage: scripts/build-proto-images.sh [summary-file]
set -euo pipefail
cd "$(dirname "$0")/.."
summary="${1:-/dev/stdout}"

build() {
    local name="$1" dir="$2" bytes
    docker build -t "ziti-hook-$name:proto" "$dir"
    bytes=$(docker image inspect "ziti-hook-$name:proto" --format '{{.Size}}')
    printf '| %s | %s |\n' "$name" "$(numfmt --to=iec "$bytes")" >>"$summary"
}

printf '| client | image size |\n|---|---|\n' >"$summary"
build go proto
build c proto-c
[ "$summary" = /dev/stdout ] || cat "$summary"
