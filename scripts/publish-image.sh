#!/usr/bin/env bash
# Build the action image and push it to GHCR. Runs the same way on a laptop and in CI.
# Usage: publish-image.sh <owner> <registry-user> <token> <git-sha> [extra-tag...]
# Tags pushed: main, <short sha>, and any extra tags. The token needs packages:write.
set -euo pipefail

owner="${1:?usage: publish-image.sh <owner> <registry-user> <token> <git-sha> [extra-tag...]}"
user="${2:?registry user}"
token="${3:?token}"
sha="${4:?git sha}"
shift 4

image="ghcr.io/${owner,,}/ziti-hook"
tags=(main "${sha:0:7}" "$@")

printf '%s' "$token" | docker login ghcr.io -u "$user" --password-stdin
docker build -t "$image:main" "$(dirname "$0")/.."
for t in "${tags[@]}"; do
    docker tag "$image:main" "$image:$t"
    docker push "$image:$t"
done
echo "pushed $image: ${tags[*]}"
