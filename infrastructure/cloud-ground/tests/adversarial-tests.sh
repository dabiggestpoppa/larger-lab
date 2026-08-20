#!/usr/bin/env bash
# OCE Cloud Ground — Adversarial Integration Tests
# B1-I1R — Mutation-based tests that invoke the real validator
# Version: 2.0.0
#
# Tests INTRODUCE failures into the codebase, run the real validator,
# verify it rejects them with nonzero exit, then RESTORE originals.
# A test only passes if the real validator catches the injected defect.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
ENGINE="$BASE_DIR/scripts/validate_engine.py"
BACKUP_DIR=$(mktemp -d)

TOTAL=0
PASSED=0
FAILED=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    TOTAL=$((TOTAL + 1))
    if [ "$2" = "PASS" ]; then
        PASSED=$((PASSED + 1))
        printf "${GREEN}[PASS] %s: %s${NC}\n" "$1" "$3"
    else
        FAILED=$((FAILED + 1))
        printf "${RED}[FAIL] %s: %s${NC}\n" "$1" "$3"
    fi
}

cleanup() {
    # Restore all backed-up files
    for backup in "$BACKUP_DIR"/*.bak; do
        [ -f "$backup" ] || continue
        orig=$(basename "$backup" .bak)
        # Restore to original location (relative path encoded in filename)
        target="$BACKUP_DIR/$(basename "$backup" .bak)"
        if [ -f "$target" ]; then
            cp "$target" "$orig" 2>/dev/null || true
        fi
    done
    rm -rf "$BACKUP_DIR"
}
trap cleanup EXIT

backup_and_mutate() {
    local file="$1"
    local content="$2"
    local backup_name=$(echo "$file" | tr '/' '_')
    cp "$file" "$BACKUP_DIR/$backup_name.bak"
    cp "$file" "$BACKUP_DIR/$backup_name.orig"
    echo "$content" > "$file"
}

restore() {
    local file="$1"
    local backup_name=$(echo "$file" | tr '/' '_')
    if [ -f "$BACKUP_DIR/$backup_name.orig" ]; then
        cp "$BACKUP_DIR/$backup_name.orig" "$file"
    fi
}

validator_rejects() {
    # Run validator, capture exit code
    python3 "$ENGINE" >/dev/null 2>&1
    local exit_code=$?
    [ "$exit_code" -ne 0 ]
}

echo "=== Adversarial Integration Tests ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Engine: $ENGINE"
echo "Base: $BASE_DIR"
echo ""

# Ensure we start from a clean state
python3 "$ENGINE" >/dev/null 2>&1
BASELINE_EXIT=$?
if [ "$BASELINE_EXIT" -eq 0 ]; then
    echo "Baseline validation: PASS (good starting state)"
else
    echo "WARNING: Baseline validation returned $BASELINE_EXIT"
fi
echo ""

# === TEST 1: Published database port ===
echo "--- Test 1: Published DB port is rejected ---"
COMPOSE="$BASE_DIR/compose/compose.foundation.yml"
backup_and_mutate "$COMPOSE" "$(cat <<'MUTATION'
services:
  postgresql:
    image: postgres:16.4-alpine
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s
      timeout: 5s
      retries: 5
    security_opt:
      - no-new-privileges:true
  redis:
    image: redis:7.4-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    security_opt:
      - no-new-privileges:true
networks:
  oce_internal:
    driver: bridge
    internal: true
    name: oce_internal
volumes:
  postgres_data:
    driver: local
    name: oce_postgres_data
  redis_data:
    driver: local
    name: oce_redis_data
MUTATION
)"
if validator_rejects; then
    log "ADVERSARIAL-PORT" "PASS" "Validator rejects published DB port"
else
    log "ADVERSARIAL-PORT" "FAIL" "Validator accepted published DB port"
fi
restore "$COMPOSE"

# === TEST 2: Latest image tag ===
echo ""
echo "--- Test 2: Latest image tag is rejected ---"
backup_and_mutate "$COMPOSE" "$(cat <<'MUTATION'
services:
  postgresql:
    image: postgres:latest
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s
      timeout: 5s
      retries: 5
    security_opt:
      - no-new-privileges:true
  redis:
    image: redis:latest
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    security_opt:
      - no-new-privileges:true
networks:
  oce_internal:
    driver: bridge
    internal: true
    name: oce_internal
volumes:
  postgres_data:
    driver: local
    name: oce_postgres_data
  redis_data:
    driver: local
    name: oce_redis_data
MUTATION
)"
if validator_rejects; then
    log "ADVERSARIAL-LATEST" "PASS" "Validator rejects :latest tags"
else
    log "ADVERSARIAL-LATEST" "FAIL" "Validator accepted :latest tags"
fi
restore "$COMPOSE"

# === TEST 3: Privileged container ===
echo ""
echo "--- Test 3: Privileged container is rejected ---"
backup_and_mutate "$COMPOSE" "$(cat <<'MUTATION'
services:
  postgresql:
    image: postgres:16.4-alpine
    privileged: true
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s
      timeout: 5s
      retries: 5
  redis:
    image: redis:7.4-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    security_opt:
      - no-new-privileges:true
networks:
  oce_internal:
    driver: bridge
    internal: true
    name: oce_internal
volumes:
  postgres_data:
    driver: local
    name: oce_postgres_data
  redis_data:
    driver: local
    name: oce_redis_data
MUTATION
)"
if validator_rejects; then
    log "ADVERSARIAL-PRIV" "PASS" "Validator rejects privileged container"
else
    log "ADVERSARIAL-PRIV" "FAIL" "Validator accepted privileged container"
fi
restore "$COMPOSE"

# === TEST 4: Cost threshold deviation ===
echo ""
echo "--- Test 4: Bad cost threshold is rejected ---"
COST="$BASE_DIR/policy/cost-guardrails.yml"
backup_and_mutate "$COST" "$(cat <<'MUTATION'
thresholds:
  fixed_baseline_warning: 999
  burst_hard_stop: 50
  total_approval_gate: 100
MUTATION
)"
if validator_rejects; then
    log "ADVERSARIAL-COST" "PASS" "Validator rejects bad cost threshold"
else
    log "ADVERSARIAL-COST" "FAIL" "Validator accepted bad cost threshold"
fi
restore "$COST"

# === TEST 5: Missing health checks ===
echo ""
echo "--- Test 5: Missing health checks are detected ---"
backup_and_mutate "$COMPOSE" "$(cat <<'MUTATION'
services:
  postgresql:
    image: postgres:16.4-alpine
    security_opt:
      - no-new-privileges:true
  redis:
    image: redis:7.4-alpine
    security_opt:
      - no-new-privileges:true
networks:
  oce_internal:
    driver: bridge
    internal: true
    name: oce_internal
volumes:
  postgres_data:
    driver: local
    name: oce_postgres_data
  redis_data:
    driver: local
    name: oce_redis_data
MUTATION
)"
if validator_rejects; then
    log "ADVERSARIAL-HEALTH" "PASS" "Validator rejects missing health checks"
else
    log "ADVERSARIAL-HEALTH" "FAIL" "Validator accepted missing health checks"
fi
restore "$COMPOSE"

# === TEST 6: External network ===
echo ""
echo "--- Test 6: External network is rejected ---"
backup_and_mutate "$COMPOSE" "$(cat <<'MUTATION'
services:
  postgresql:
    image: postgres:16.4-alpine
    networks:
      - external_net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s
      timeout: 5s
      retries: 5
    security_opt:
      - no-new-privileges:true
  redis:
    image: redis:7.4-alpine
    networks:
      - external_net
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    security_opt:
      - no-new-privileges:true
networks:
  external_net:
    external: true
    name: oce_external
volumes:
  postgres_data:
    driver: local
    name: oce_postgres_data
  redis_data:
    driver: local
    name: oce_redis_data
MUTATION
)"
if validator_rejects; then
    log "ADVERSARIAL-EXTERNAL" "PASS" "Validator rejects external network"
else
    log "ADVERSARIAL-EXTERNAL" "FAIL" "Validator accepted external network"
fi
restore "$COMPOSE"

# === TEST 7: Docker socket mount ===
echo ""
echo "--- Test 7: Docker socket mount is rejected ---"
backup_and_mutate "$COMPOSE" "$(cat <<'MUTATION'
services:
  postgresql:
    image: postgres:16.4-alpine
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s
      timeout: 5s
      retries: 5
    security_opt:
      - no-new-privileges:true
  redis:
    image: redis:7.4-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    security_opt:
      - no-new-privileges:true
networks:
  oce_internal:
    driver: bridge
    internal: true
    name: oce_internal
volumes:
  postgres_data:
    driver: local
    name: oce_postgres_data
  redis_data:
    driver: local
    name: oce_redis_data
MUTATION
)"
if validator_rejects; then
    log "ADVERSARIAL-SOCKET" "PASS" "Validator rejects Docker socket mount"
else
    log "ADVERSARIAL-SOCKET" "FAIL" "Validator accepted Docker socket mount"
fi
restore "$COMPOSE"

# === TEST 8: Schema with missing required fields ===
echo ""
echo "--- Test 8: Schema fixture with missing fields is rejected ---"
SCHEMA="$BASE_DIR/contracts/worker-task-envelope.schema.json"
FIXTURE="$BASE_DIR/tests/fixtures/invalid/worker-task-envelope.invalid.missing-required.json"
if [ -f "$SCHEMA" ] && [ -f "$FIXTURE" ]; then
    SCHEMA_VALID=$(python3 -c "
import json, jsonschema
schema = json.load(open('$SCHEMA'))
instance = json.load(open('$FIXTURE'))
try:
    jsonschema.validate(instance=instance, schema=schema)
    print('ACCEPTED')
except jsonschema.ValidationError:
    print('REJECTED')
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null)
    if [ "$SCHEMA_VALID" = "REJECTED" ]; then
        log "ADVERSARIAL-SCHEMA-MISSING" "PASS" "Schema rejects instance with missing required fields"
    else
        log "ADVERSARIAL-SCHEMA-MISSING" "FAIL" "Schema accepted instance with missing fields: $SCHEMA_VALID"
    fi
else
    log "ADVERSARIAL-SCHEMA-MISSING" "BLOCKED" "Schema or fixture not found"
fi

# === TEST 9: Schema with bad enum ===
echo ""
echo "--- Test 9: Schema with bad enum value is rejected ---"
BAD_ENUM="$BASE_DIR/tests/fixtures/invalid/worker-task-envelope.invalid.bad-enum.json"
if [ -f "$SCHEMA" ] && [ -f "$BAD_ENUM" ]; then
    SCHEMA_VALID=$(python3 -c "
import json, jsonschema
schema = json.load(open('$SCHEMA'))
instance = json.load(open('$BAD_ENUM'))
try:
    jsonschema.validate(instance=instance, schema=schema)
    print('ACCEPTED')
except jsonschema.ValidationError:
    print('REJECTED')
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null)
    if [ "$SCHEMA_VALID" = "REJECTED" ]; then
        log "ADVERSARIAL-SCHEMA-ENUM" "PASS" "Schema rejects bad enum value"
    else
        log "ADVERSARIAL-SCHEMA-ENUM" "FAIL" "Schema accepted bad enum: $SCHEMA_VALID"
    fi
else
    log "ADVERSARIAL-SCHEMA-ENUM" "BLOCKED" "Schema or fixture not found"
fi

# === TEST 10: Empty compose file ===
echo ""
echo "--- Test 10: Empty compose file causes validator failure ---"
EMPTY_COMPOSE="$BASE_DIR/compose/compose.foundation.yml"
backup_and_mutate "$EMPTY_COMPOSE" "# empty compose file"
if validator_rejects; then
    log "ADVERSARIAL-EMPTY-COMPOSE" "PASS" "Validator rejects empty compose"
else
    log "ADVERSARIAL-EMPTY-COMPOSE" "FAIL" "Validator accepted empty compose"
fi
restore "$EMPTY_COMPOSE"

# === TEST 11: Worker DB access in policy ===
echo ""
echo "--- Test 11: Removing worker denials is detected ---"
POLICY="$BASE_DIR/policy/network-access.yml"
backup_and_mutate "$POLICY" "rules: []"
if validator_rejects; then
    log "ADVERSARIAL-WORKER-DENY" "PASS" "Validator detects missing worker denials"
else
    log "ADVERSARIAL-WORKER-DENY" "FAIL" "Validator accepted empty worker denials"
fi
restore "$POLICY"

# === SUMMARY ===
echo ""
echo "========================================="
echo "  Adversarial Integration Test Results"
echo "========================================="
echo "Total: $TOTAL"
echo -e "PASS:  ${GREEN}$PASSED${NC}"
echo -e "FAIL:  ${RED}$FAILED${NC}"
echo "========================================="

if [ "$FAILED" -eq 0 ] && [ "$TOTAL" -gt 0 ]; then
    echo -e "OVERALL: ${GREEN}PASS${NC}"
    exit 0
else
    echo -e "OVERALL: ${RED}FAIL${NC}"
    exit 1
fi
