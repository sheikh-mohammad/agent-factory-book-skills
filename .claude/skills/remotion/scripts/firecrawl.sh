#!/usr/bin/env bash
# firecrawl.sh - Scrape brand data from a website using Firecrawl API
# Usage: firecrawl.sh <url>
#
# Returns structured brand data: name, tagline, colors, logo, screenshot, etc.
# Requires FIRECRAWL_API_KEY in environment or .env

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
WORKSPACE_DIR="$(dirname "$(dirname "$SKILL_DIR")")"

# Load .env if exists
if [ -f "$WORKSPACE_DIR/.env" ]; then
  set -a
  source "$WORKSPACE_DIR/.env"
  set +a
fi

URL="${1:?Usage: firecrawl.sh <url>}"

if [ -z "${FIRECRAWL_API_KEY:-}" ]; then
  echo "Error: FIRECRAWL_API_KEY not set" >&2
  exit 1
fi

curl -s -X POST 'https://api.firecrawl.dev/v1/scrape' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${FIRECRAWL_API_KEY}" \
  -d "$(cat <<EOF
{
  "url": "$URL",
  "formats": ["markdown", "extract", "screenshot"],
  "extract": {
    "schema": {
      "type": "object",
      "properties": {
        "brandName": {"type": "string"},
        "tagline": {"type": "string"},
        "headline": {"type": "string"},
        "description": {"type": "string"},
        "features": {"type": "array", "items": {"type": "string"}},
        "logoUrl": {"type": "string"},
        "faviconUrl": {"type": "string"},
        "primaryColors": {"type": "array", "items": {"type": "string"}},
        "ctaText": {"type": "string"},
        "socialLinks": {"type": "object"}
      }
    }
  }
}
EOF
)"