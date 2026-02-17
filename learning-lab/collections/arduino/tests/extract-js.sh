#!/bin/bash
# Extract JavaScript code from HTML file between <script> tags
# Usage: bash extract-js.sh ../index.html

HTML_FILE="${1:-../index.html}"

if [ ! -f "$HTML_FILE" ]; then
  echo "Error: File not found: $HTML_FILE" >&2
  exit 1
fi

# Extract content between <script> and </script> tags
sed -n '/<script>/,/<\/script>/p' "$HTML_FILE" | sed '/<script>/d;/<\/script>/d'
