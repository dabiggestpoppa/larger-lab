#!/bin/sh
# Install the pinned Gitleaks release binary into a runner tool path.
#
# B4-CXR7U9R24: replaces the inline `wget --max-redirect=0 <release asset>`
# steps, which could not work -- GitHub serves release assets through a
# redirect to the objects host, so wget aborted with exit code 8 before
# anything was installed (run 35169053088).
#
# The digest constant below is the trust anchor: it is checked before any
# extraction or execution, and nothing is fetched from the network to
# establish trust. The archive is unpacked outside the repository so the
# release's own README/LICENSE cannot dirty the checkout.
#
# Usage: install-gitleaks.sh [install-dir]     (default: /usr/local/bin)

set -eu

GITLEAKS_VERSION=8.18.1
GITLEAKS_ASSET="gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz"
GITLEAKS_URL="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/${GITLEAKS_ASSET}"
# Independently verified against the upstream release asset on 2026-09-16.
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
