#!/usr/bin/env bash
# Deploy stock-api on the VPS: pull, rebuild, verify that /version really reports the new build.
#
# The verification is the point. /health answers "ok" no matter how old the image is, so a
# failed rebuild looks exactly like a successful one — that is how a whole day once ran on
# stale code. GIT_SHA and BUILD_TIME are build args (see docker-compose.yml); building
# without them leaves /version at "unknown", which makes the check useless.
set -euo pipefail

cd "$(dirname "$0")/.."

git pull --ff-only

GIT_SHA="$(git rev-parse --short HEAD)"
BUILD_TIME="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
export GIT_SHA BUILD_TIME
echo "==> build ${GIT_SHA} (${BUILD_TIME})"

docker compose up -d --build stock-api

echo "==> czekam na /version"
for _ in $(seq 1 30); do
    reported="$(curl -fsS --max-time 5 http://127.0.0.1:8000/version 2>/dev/null \
        | python3 -c 'import json,sys; print(json.load(sys.stdin)["git_sha"])' 2>/dev/null || true)"
    if [ "${reported}" = "${GIT_SHA}" ]; then
        echo "==> OK: API na ${GIT_SHA}"
        exit 0
    fi
    sleep 2
done

echo "==> BŁĄD: /version zgłasza '${reported:-brak odpowiedzi}', oczekiwano '${GIT_SHA}'" >&2
echo "    Kontener chodzi na starym obrazie albo nie wstał — sprawdź: docker compose logs stock-api" >&2
exit 1
