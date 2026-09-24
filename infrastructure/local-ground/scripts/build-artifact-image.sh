#!/usr/bin/env bash
# Build the OCE-owned artifact-store image from checksum-verified official MinIO
# source. No registry credential, private repository, floating tag, or MinIO
# release binary is involved.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$BASE_DIR/compose/artifact-store"
LOCK="$BUILD_DIR/source-lock.json"
EVIDENCE="$BASE_DIR/var/artifact-store-build.json"

for tool in docker git python3; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "BLOCKED: artifact image build requires $tool" >&2
    exit 3
  }
done

python3 - "$LOCK" <<'PY'
import json, sys
lock = json.load(open(sys.argv[1], encoding="utf-8"))
required = ("repository", "release_tag", "peeled_commit", "source_url",
            "source_sha256", "go_builder", "runtime_base", "image")
missing = [key for key in required if not lock.get(key)]
if missing:
    raise SystemExit("artifact source lock missing: " + ",".join(missing))
if lock["peeled_commit"] != "f79a4ef4d0dc3e6562cad0d1d1db674bc8c75531":
    raise SystemExit("unexpected MinIO source commit")
if lock["release_tag"] != "RELEASE.2024-05-28T17-19-04Z":
    raise SystemExit("unexpected MinIO release tag")
for value in lock.values():
    if isinstance(value, str) and "latest" in value.lower():
        raise SystemExit("floating latest forbidden in source lock")
PY

lock_value() {
  python3 - "$LOCK" "$1" <<'PY'
import json, sys
lock = json.load(open(sys.argv[1], encoding="utf-8"))
value = lock[sys.argv[2]]
if not isinstance(value, str):
    raise SystemExit("artifact source lock value is not text")
print(value, end="")
PY
}

# Values are populated through the validating accessor above.
# shellcheck disable=SC2034
LOCK_REPOSITORY="$(lock_value repository)"
LOCK_RELEASE_TAG="$(lock_value release_tag)"
# shellcheck disable=SC2034
LOCK_PEELED_COMMIT="$(lock_value peeled_commit)"
LOCK_SOURCE_URL="$(lock_value source_url)"
LOCK_SOURCE_SHA256="$(lock_value source_sha256)"
LOCK_GO_BUILDER="$(lock_value go_builder)"
LOCK_RUNTIME_BASE="$(lock_value runtime_base)"
LOCK_IMAGE="$(lock_value image)"

REMOTE="$(git ls-remote "$LOCK_REPOSITORY" \
  "refs/tags/$LOCK_RELEASE_TAG" "refs/tags/$LOCK_RELEASE_TAG^{}")"
PEELED="$(printf '%s\n' "$REMOTE" | awk '/\^\{\}$/{print $1}')"
# The lock value is assigned above; ShellCheck cannot infer the accessor result.
# shellcheck disable=SC2153
if [[ "$PEELED" != "$LOCK_PEELED_COMMIT" ]]; then
  echo "BLOCKED: MinIO tag $LOCK_RELEASE_TAG peels to $PEELED, expected $LOCK_PEELED_COMMIT" >&2
  exit 4
fi

if docker image inspect "$LOCK_IMAGE" \
    --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' \
    2>/dev/null | grep -Fx "$LOCK_PEELED_COMMIT" >/dev/null; then
  echo "artifact-store image already verified: $LOCK_IMAGE"
else
  docker build --pull=false --tag "$LOCK_IMAGE" "$BUILD_DIR"
fi

VERSION="$(docker run --rm --entrypoint /usr/bin/minio "$LOCK_IMAGE" --version)"
REVISION="$(docker image inspect "$LOCK_IMAGE" \
  --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}')"
if [[ "$VERSION" != *"$LOCK_RELEASE_TAG"* || "$REVISION" != "$LOCK_PEELED_COMMIT" ]]; then
  echo "BLOCKED: built MinIO identity mismatch: version=$VERSION revision=$REVISION" >&2
  exit 5
fi

mkdir -p "$(dirname "$EVIDENCE")"
python3 - "$EVIDENCE" "$LOCK_IMAGE" "$LOCK_RELEASE_TAG" "$LOCK_PEELED_COMMIT" \
  "$LOCK_SOURCE_SHA256" "$LOCK_SOURCE_URL" "$LOCK_GO_BUILDER" \
  "$LOCK_RUNTIME_BASE" "$VERSION" <<'PY'
import json, sys
path, image, tag, commit, source_sha, source_url, builder, runtime, version = sys.argv[1:]
json.dump({
    "format": "oce-artifact-store-build-evidence-v1",
    "image": image,
    "source_repository": "https://github.com/minio/minio",
    "source_release_tag": tag,
    "source_commit": commit,
    "source_archive_sha256": source_sha,
    "source_url": source_url,
    "go_builder": builder,
    "runtime_base": runtime,
    "reported_version": version,
    "external_minio_image_pull_required": False,
}, open(path, "w", encoding="utf-8"), indent=2, sort_keys=True)
PY
echo "artifact-store image -> $LOCK_IMAGE"
