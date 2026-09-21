#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

docker run --rm \
  --volume "${project_root}:/workspace" \
  aquasec/trivy:0.74.0 \
  config \
  --config /workspace/trivy.yaml \
  /workspace/terraform
