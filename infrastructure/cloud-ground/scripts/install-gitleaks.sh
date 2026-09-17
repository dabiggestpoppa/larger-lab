#!/bin/sh
# Install the pinned Gitleaks release binary into the runner's tool path.
#
# B4-CXR7U9R24.  The previous inline CI steps used
# `wget --max-redirect=0 <github release asset>`, which cannot work: GitHub
# serves release assets through a redirect to the objects host, so wget
# aborted with exit code 8 (server error) before anything was installed --
# exactly what run 35169053088 hit.  A redirect-tolerant HTTPS fetch plus an
# embedded, independently verified digest is the replacement contract.
#
# Contract, in order:
#   1. HTTPS only, redirects permitted (curl -fL).
#   2. A download failure aborts (set -e + curl -f): nothing is extracted.
#   3. The SHA-256 of the downloaded archive is compared against the constant
#      digest below BEFORE any extraction or execution.  A mismatch aborts.
#   4. The archive is unpacked in a temporary directory OUTSIDE the
#      repository, so the release's own README/LICENSE can never clobber the
#      checkout and trip the runner's clean-source check.
#   5. The trust anchor is this constant.  No checksum is fetched from the
#      network at install time.
#
# Usage: install-gitleaks.sh [install-dir]     (default: /usr/local/bin)

set -eu

GITLEAKS_VERSION=8.18.1
GITLEAKS_ASSET="gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz"
GITLEAKS_URL="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/${GITLEAKS_ASSET}"
# Verified independently against the upstream release asset on 2026-09-16:
# 2,891,432 bytes, sha256 as below.  Regenerating it requires a deliberate
# edit here, so a substituted artifact cannot pass unnoticed.
GITLEAKS_SHA256=3e157a26081e296d4cb94ef0d87441c9afc5f392cb02957656dd5cfeb7aaf6c9

INSTALL_DIR=${1:-/usr/local/bin}

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT INT TERM

echo "Downloading ${GITLEAKS_ASSET} (redirects permitted, HTTPS only)"
curl -fsSL --proto '=https' --tlsv1.2 -o "$tmp/$GITLEAKS_ASSET" "$GITLEAKS_URL"

actual=$(sha256sum "$tmp/$GITLEAKS_ASSET" | awk '{print $1}')
if [ "$actual" != "$GITLEAKS_SHA256" ]; then
    echo "ERROR: ${GITLEAKS_ASSET} checksum mismatch" >&2
    echo "  expected: $GITLEAKS_SHA256" >&2
    echo "  actual:   $actual" >&2
    echo "  Refusing to extract or execute an unverified archive." >&2
    exit 1
fi
echo "Checksum verified: ${actual}"

tar xzf "$tmp/$GITLEAKS_ASSET" -C "$tmp"

if [ -w "$INSTALL_DIR" ]; then
    mv "$tmp/gitleaks" "$INSTALL_DIR/"
else
    sudo mv "$tmp/gitleaks" "$INSTALL_DIR/"
fi
"$INSTALL_DIR/gitleaks" version
