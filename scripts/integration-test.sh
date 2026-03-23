#!/bin/bash
set -e

STAGE=""
PROFILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stage)
      STAGE="$2"
      shift 2
      ;;
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$STAGE" ]]; then
  echo "Usage: $0 --stage staging|production [--profile <profile>]" >&2
  exit 1
fi

if [[ "$STAGE" == "staging" ]]; then
  BASE_URL="https://spellcheck.kiyanaw.dev"
elif [[ "$STAGE" == "production" ]]; then
  BASE_URL="https://spellcheck.kiyanaw.net"
else
  echo "Invalid stage: $STAGE. Must be 'staging' or 'production'." >&2
  exit 1
fi

AWS_ARGS=()
if [[ -n "$PROFILE" ]]; then
  AWS_ARGS+=(--profile "$PROFILE")
fi

echo "Fetching API key for integration-test-${STAGE}..."
API_KEY=$(aws apigateway get-api-keys \
  --name-query "integration-test-${STAGE}" \
  --include-values \
  --query 'items[0].value' \
  --output text \
  "${AWS_ARGS[@]}")

if [[ -z "$API_KEY" || "$API_KEY" == "None" ]]; then
  echo "No API key found for 'integration-test-${STAGE}'." >&2
  echo "Create one with: node scripts/create-api-key.js --name integration-test --stage ${STAGE} [--profile <profile>]" >&2
  exit 1
fi

export SPELLCHECK_API_URL="$BASE_URL"
export SPELLCHECK_API_KEY="$API_KEY"

echo "Running integration tests against $BASE_URL..."
python -m pytest src/test/integration/ -v
