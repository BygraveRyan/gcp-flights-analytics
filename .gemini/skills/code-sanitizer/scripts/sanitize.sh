#!/bin/bash

# Exit on error
set -e

FILE=$1

if [[ -z "$FILE" ]]; then
    echo "Usage: sanitize.sh <file_path>"
    exit 1
fi

if [[ "$FILE" == *.py ]]; then
    echo "Sanitizing Python file: $FILE"
    if command -v black &> /dev/null; then
        black "$FILE"
    else
        echo "Warning: 'black' not found. Skipping formatting."
    fi
    if command -v isort &> /dev/null; then
        isort "$FILE"
    else
        echo "Warning: 'isort' not found. Skipping import sorting."
    fi
elif [[ "$FILE" == *.sql ]]; then
    echo "Sanitizing SQL file: $FILE"
    if command -v sqlfluff &> /dev/null; then
        sqlfluff fix --dialect bigquery "$FILE" || echo "Warning: 'sqlfluff fix' failed or returned warnings."
    else
        echo "Warning: 'sqlfluff' not found. Skipping SQL linting."
    fi
else
    echo "Unsupported file type: $FILE"
    exit 1
fi

echo "Sanitization complete for $FILE"
