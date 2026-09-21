$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

docker run --rm `
  --volume "${projectRoot}:/workspace" `
  aquasec/trivy:0.74.0 `
  config `
  --config /workspace/trivy.yaml `
  /workspace/terraform

exit $LASTEXITCODE
