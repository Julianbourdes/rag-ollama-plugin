#!/bin/bash
# lint-typescript.sh - Lint TypeScript/JavaScript files after Claude Code writes/edits them
#
# This hook is triggered by PostToolUse on Write|Edit operations
# It only runs for TS/JS files and checks with eslint

FILE_PATH="$1"

# Only process TypeScript/JavaScript files
if [[ ! "$FILE_PATH" =~ \.(ts|tsx|js|jsx)$ ]]; then
    exit 0
fi

# Check if eslint is available (via npx or pnpm)
if command -v pnpm &> /dev/null; then
    RUNNER="pnpm exec"
elif command -v npx &> /dev/null; then
    RUNNER="npx"
else
    echo "Neither pnpm nor npx found, skipping TypeScript lint"
    exit 0
fi

# Run eslint with fix
echo "Linting TypeScript file: $FILE_PATH"
$RUNNER eslint "$FILE_PATH" --fix --quiet 2>/dev/null || true

# Run prettier if available
$RUNNER prettier "$FILE_PATH" --write 2>/dev/null || true

echo "TypeScript lint completed for $FILE_PATH"
