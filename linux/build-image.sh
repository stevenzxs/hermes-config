#!/usr/bin/env bash
set -euo pipefail
# Execute in WSL. The context is a git archive, never the user's working tree.
source_repo=${1:?source repository}
delivery=${2:?delivery directory}
source_sha=3b421578588243f920886e6fe79a6faa87ea026e
config_repo=$(cd "$(dirname "$0")/.." && pwd)
config_sha=$(git -C "$config_repo" rev-parse HEAD)
image=ghcr.io/stevenzxs/hermes-agent:src-${source_sha:0:12}-cfg-${config_sha:0:12}
test -z "$(git -C "$config_repo" status --porcelain)" || { echo 'Configuration worktree must be clean'; exit 1; }
test "$(git -C "$source_repo" rev-parse HEAD)" = "$source_sha"
test ! -e "$delivery"
free_kb=$(df -Pk /mnt/d | awk 'NR==2 {print $4}')
test "$free_kb" -gt 41943040 || { echo 'At least 40 GiB D: free required before build'; exit 1; }
mkdir -p "$delivery/context"
git -C "$source_repo" archive "$source_sha" | tar -x -C "$delivery/context"
printf '%s\n' "$image" > "$delivery/image.txt"
printf '{"sourceCommit":"%s","configCommit":"%s","image":"%s","platform":"linux/amd64"}\n' "$source_sha" "$config_sha" "$image" > "$delivery/build-record.json"
docker build --platform linux/amd64 --progress plain \
  --label "org.opencontainers.image.revision=$source_sha" \
  --label 'org.opencontainers.image.source=https://github.com/stevenzxs/hermes-agent' \
  --label "io.stevenzxs.hermes.config-revision=$config_sha" \
  -t "$image" "$delivery/context" 2>&1 | tee "$delivery/build.log"
docker image inspect "$image" > "$delivery/image-inspect.json"
docker run --rm --network none "$image" --version 2>&1 | tee "$delivery/version-check.log"
echo 'BUILD AND VERSION CHECK COMPLETE; publish requires verified result'
