#!/bin/bash
# Project Logger Shortcut voor supplier_pricelist_sync
# Usage: ./log.sh "Your message"

LOGGER_PATH="../.dev/universal_logger.py"

if [ $# -eq 0 ]; then
    echo "Usage: ./log.sh \"Your message\""
    echo "       ./log.sh --recent [count]"
    echo "       ./log.sh --snapshot \"Description\""
    exit 1
fi

python "$LOGGER_PATH" "$@"