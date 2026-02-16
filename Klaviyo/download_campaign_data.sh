#!/bin/sh
#
# Download Klaviyo email campaign data: recipients, opens, and clicks.
#
# Usage:
#   ./download_campaign_data.sh --all
#   ./download_campaign_data.sh CAMPAIGN_ID1 CAMPAIGN_ID2 ...
#
# Requires: KLAVIYO_API_KEY in environment or config.env
#           Python 3 with requests (pip install -r requirements.txt)
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Load config.env if it exists
if [ -f config.env ]; then
    set -a
    . ./config.env
    set +a
fi

# Run the Python script, passing through all arguments
exec python3 download_campaign_data.py "$@"
