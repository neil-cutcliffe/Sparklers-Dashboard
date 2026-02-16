#!/bin/sh
#
# Download Klaviyo email campaign data: recipients with per-recipient opens and clicks.
#
# Usage:
#   ./download_campaign_data.sh "TSC Newsletter Feb 15"
#   ./download_campaign_data.sh "Campaign 1" "Campaign 2"
#
# Requires: KLAVIYO_API_KEY in environment or config.env
#           Python 3 with requests (pip install -r requirements.txt)
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Use venv Python if it exists
if [ -f venv/bin/python ]; then
    PYTHON=./venv/bin/python
else
    PYTHON=python3
fi

# Load config.env if it exists
if [ -f config.env ]; then
    set -a
    . ./config.env
    set +a
fi

# Run the Python script, passing through all arguments
exec "$PYTHON" download_campaign_data.py "$@"
