#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:?Usage: $0 <version>}"

mkdir -p dist

tar -czf "dist/mb-aws-helper-${VERSION}.tar.gz" \
  aws_helper \
  aws_tool.py \
  requirements.txt \
  README.md \
  mb-aws-helper

shasum -a 256 "dist/mb-aws-helper-${VERSION}.tar.gz" > "dist/mb-aws-helper-${VERSION}.sha256"

echo "Created: dist/mb-aws-helper-${VERSION}.tar.gz"
echo "SHA256 saved to: dist/mb-aws-helper-${VERSION}.sha256"