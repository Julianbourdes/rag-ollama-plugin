#!/bin/bash
# lint-python.sh - Lint Python files after Claude Code writes/edits them
#
# This hook is triggered by PostToolUse on Write|Edit operations
# It only runs for Python files and checks with ruff

FILE_PATH="$1"

# Only process Python files
if [[ ! "$FILE_PATH" =~ \.py$ ]]; then
    exit 0
fi

# Check if ruff is available
if ! command -v ruff &> /dev/null; then
    echo "ruff not found, skipping Python lint"
    exit 0
fi

# Run ruff check
echo "Linting Python file: $FILE_PATH"
ruff check "$FILE_PATH" --fix --quiet

# Run ruff format
ruff format "$FILE_PATH" --quiet

echo "Python lint completed for $FILE_PATH"
