#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:?Usage: $0 <version>}"
OUT_DIR="${2:-dist}"

mkdir -p "$OUT_DIR"

TARBALL="$OUT_DIR/mb-aws-helper-${VERSION}.tar.gz"

# Package only what is needed by Homebrew.
tar -czf "$TARBALL" \
  aws_helper \
  aws_tool.py \
  mb-aws-helper \
  requirements.txt \
  README.md \
  pyproject.toml

shasum -a 256 "$TARBALL" | tee "$OUT_DIR/mb-aws-helper-${VERSION}.sha256"

echo "Created: $TARBALL"
echo "SHA256 saved to: $OUT_DIR/mb-aws-helper-${VERSION}.sha256"
