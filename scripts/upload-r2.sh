#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:?Usage: $0 <version>}"
R2_BUCKET="${R2_BUCKET:?R2_BUCKET not set}"
R2_ACCOUNT_ID="${R2_ACCOUNT_ID:?R2_ACCOUNT_ID not set}"
R2_PREFIX="${R2_PREFIX:-awstool}"
FILE="dist/mb-aws-helper-${VERSION}.tar.gz"

if [[ ! -f "$FILE" ]]; then
  echo "Missing release artifact: $FILE"
  exit 1
fi

aws s3 cp "$FILE" "s3://${R2_BUCKET}/${R2_PREFIX}/mb-aws-helper-${VERSION}.tar.gz" \
  --endpoint-url "https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

echo "Uploaded: s3://${R2_BUCKET}/${R2_PREFIX}/mb-aws-helper-${VERSION}.tar.gz"
