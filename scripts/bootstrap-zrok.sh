#!/usr/bin/env bash
# Enable a zrok environment in a temp ZROK2_HOME and print it as one base64 string for a GitHub secret.
# Usage: bootstrap-zrok.sh <account-token> [env-description]
# Your real ~/.zrok2 is never read or changed.
set -euo pipefail

token="${1:?usage: bootstrap-zrok.sh <account-token> [env-description]}"
desc="${2:-ziti-hook github action}"
command -v zrok2 >/dev/null || { echo "zrok2 is not on PATH" >&2; exit 1; }

home="$(mktemp -d)"
trap 'rm -rf "$home"' EXIT
export ZROK2_HOME="$home"

zrok2 enable --headless -d "$desc" "$token" >&2

# Flat tarball of the files zrok wrote, so the action can lay them down in its own temp home.
files=()
for f in "$home"/*; do [ -f "$f" ] && files+=("$(basename "$f")"); done
[ "${#files[@]}" -gt 0 ] || { echo "zrok2 enable wrote no files to $home" >&2; exit 1; }
blob="$(tar -czf - -C "$home" "${files[@]}" | base64 | tr -d '\n')"

cat >&2 <<EOF

Next steps
1. Add the string printed below to your repo as the secret ZROK_ENV (Settings, Secrets and variables, Actions).
   It grants the access of this environment. Treat it like a password.
2. Create the private share on the machine that runs the receiver, then add its token as the secret ZROK_SHARE_TOKEN.
3. Use the action with transport: zrok, zrok-env: \${{ secrets.ZROK_ENV }}, zrok-share-token: \${{ secrets.ZROK_SHARE_TOKEN }}.
4. To revoke, run "zrok2 disable" for this environment or regenerate the account token.

EOF
printf '%s\n' "$blob"
