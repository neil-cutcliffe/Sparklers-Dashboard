#!/usr/bin/env python3
"""
Download Klaviyo email campaign data: recipients, opens, and clicks.

Uses the Klaviyo API to fetch:
- Recipient lists (email, customer_id, status) per campaign
- Campaign-level opens and clicks from the Reporting API

Usage:
    python download_campaign_data.py [--all | CAMPAIGN_ID ...]
    python download_campaign_data.py --all
    python download_campaign_data.py 01GMRWDSA0ARTAKE1SFX8JGXAY XyZ123

Requires KLAVIYO_API_KEY in environment or config.env.
"""

import os
import sys
import csv
import argparse
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests package required. Run: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

# API endpoints
KLAVIYO_BASE = "https://a.klaviyo.com"
V1_CAMPAIGNS = f"{KLAVIYO_BASE}/api/v1/campaigns"
V1_RECIPIENTS = f"{KLAVIYO_BASE}/api/v1/campaign/{{campaign_id}}/recipients"
REPORTING_CAMPAIGN_VALUES = f"{KLAVIYO_BASE}/api/campaign-values-reports/"
REPORTING_REVISION = "2024-10-15"


def load_config():
    """Load API key from environment or config.env."""
    api_key = os.environ.get("KLAVIYO_API_KEY")
    if api_key:
        return api_key

    config_path = Path(__file__).parent / "config.env"
    if config_path.exists():
        with open(config_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    if key.strip() == "KLAVIYO_API_KEY":
                        return value.strip()

    return None


def get_v1_campaigns(api_key):
    """Fetch all campaigns using v1 API."""
    campaigns = []
    page = 0
    while True:
        resp = requests.get(
            V1_CAMPAIGNS,
            params={"api_key": api_key, "page": page, "count": 100},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        campaigns.extend(data.get("data", []))
        if page * data.get("page_size", 0) + len(data.get("data", [])) >= data.get("total", 0):
            break
        page += 1
        time.sleep(0.5)  # Rate limit
    return campaigns


def get_campaign_recipients(api_key, campaign_id):
    """Fetch all recipients for a campaign (paginated)."""
    recipients = []
    offset = None
    url = V1_RECIPIENTS.format(campaign_id=campaign_id)

    while True:
        params = {"api_key": api_key, "count": 25000, "sort": "asc"}
        if offset:
            params["offset"] = offset

        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        recipients.extend(data.get("data", []))
        offset = data.get("next_offset")
        if not offset:
            break
        time.sleep(0.5)

    return recipients


def get_campaign_stats(api_key, campaign_id, conversion_metric_id="RESQ6t"):
    """Fetch campaign opens/clicks from Reporting API."""
    # Reporting API uses newer ID format; v1 IDs may differ
    payload = {
        "data": {
            "type": "campaign-values-report",
            "attributes": {
                "timeframe": {"key": "last_12_months"},
                "conversion_metric_id": conversion_metric_id,
                "filter": f'equals(campaign_id,"{campaign_id}")',
                "statistics": [
                    "recipients",
                    "delivered",
                    "opens",
                    "opens_unique",
                    "open_rate",
                    "clicks",
                    "clicks_unique",
                    "click_rate",
                ],
                "group_by": ["campaign_id", "campaign_message_id", "send_channel"],
            },
        }
    }

    resp = requests.post(
        REPORTING_CAMPAIGN_VALUES,
        headers={
            "Authorization": f"Klaviyo-API-Key {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "revision": REPORTING_REVISION,
        },
        json=payload,
        timeout=30,
    )

    if resp.status_code == 404 or (resp.status_code == 400 and "campaign" in resp.text.lower()):
        return None  # Campaign not found or wrong ID format for Reporting API

    resp.raise_for_status()
    data = resp.json()

    results = data.get("data", {}).get("attributes", {}).get("results", [])
    if not results:
        return None

    # Sum counts across variations; use first result for rates
    totals = {"recipients": 0, "delivered": 0, "opens": 0, "opens_unique": 0, "clicks": 0, "clicks_unique": 0}
    open_rate = click_rate = None
    for r in results:
        s = r.get("statistics", {})
        for k in ("recipients", "delivered", "opens", "opens_unique", "clicks", "clicks_unique"):
            totals[k] += s.get(k) or 0
        if open_rate is None:
            open_rate = s.get("open_rate")
        if click_rate is None:
            click_rate = s.get("click_rate")
    totals["open_rate"] = open_rate
    totals["click_rate"] = click_rate
    return totals


def write_recipients_csv(recipients, stats, campaign_name, campaign_id, output_path):
    """Write combined CSV: recipients with campaign-level stats."""
    fieldnames = [
        "campaign_id",
        "campaign_name",
        "email",
        "customer_id",
        "status",
        "campaign_opens",
        "campaign_clicks",
        "campaign_open_rate",
        "campaign_click_rate",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        opens = stats.get("opens", 0) if stats else ""
        clicks = stats.get("clicks", 0) if stats else ""
        open_rate = stats.get("open_rate", "") if stats else ""
        click_rate = stats.get("click_rate", "") if stats else ""
        for r in recipients:
            writer.writerow({
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "email": r.get("email", ""),
                "customer_id": r.get("customer_id", ""),
                "status": r.get("status", ""),
                "campaign_opens": opens,
                "campaign_clicks": clicks,
                "campaign_open_rate": open_rate,
                "campaign_click_rate": click_rate,
            })


def main():
    parser = argparse.ArgumentParser(
        description="Download Klaviyo campaign recipients, opens, and clicks."
    )
    parser.add_argument(
        "campaign_ids",
        nargs="*",
        help="Campaign IDs to fetch. Omit if using --all.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Fetch all sent campaigns from the account.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="Output directory for CSV files (default: current directory).",
    )
    parser.add_argument(
        "--conversion-metric",
        default=os.environ.get("CONVERSION_METRIC_ID", "RESQ6t"),
        help="Conversion metric ID for Reporting API.",
    )
    args = parser.parse_args()

    api_key = load_config()
    if not api_key:
        print(
            "Error: KLAVIYO_API_KEY not set. Set it in your environment or create config.env from config.example.",
            file=sys.stderr,
        )
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.all:
        print("Fetching campaign list...")
        campaigns = get_v1_campaigns(api_key)
        # Only include sent campaigns
        campaign_ids = [
            c["id"]
            for c in campaigns
            if c.get("status") == "sent" and c.get("message_type") == "email"
        ]
        if not campaign_ids:
            print("No sent email campaigns found.")
            return
        print(f"Found {len(campaign_ids)} sent email campaign(s).")
    else:
        if not args.campaign_ids:
            parser.error("Provide campaign IDs or use --all")
        campaign_ids = args.campaign_ids
        campaigns = {c["id"]: c for c in get_v1_campaigns(api_key)}

    for campaign_id in campaign_ids:
        campaign_name = "Unknown"
        if args.all and campaign_id in campaigns:
            campaign_name = campaigns[campaign_id].get("name", campaign_id)
        elif not args.all and campaigns:
            campaign_name = campaigns.get(campaign_id, {}).get("name", campaign_id)

        print(f"Fetching campaign: {campaign_name} ({campaign_id})...")

        try:
            recipients = get_campaign_recipients(api_key, campaign_id)
            print(f"  Recipients: {len(recipients)}")
        except requests.HTTPError as e:
            print(f"  Error fetching recipients: {e}", file=sys.stderr)
            continue

        stats = None
        try:
            stats = get_campaign_stats(api_key, campaign_id, args.conversion_metric)
            if stats:
                print(f"  Opens: {stats.get('opens', 'N/A')}, Clicks: {stats.get('clicks', 'N/A')}")
            else:
                print("  (Campaign stats not available - ID may use different format for Reporting API)")
        except requests.HTTPError as e:
            print(f"  Note: Could not fetch campaign stats: {e}", file=sys.stderr)

        safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in campaign_name)[:50]
        output_path = output_dir / f"klaviyo_{campaign_id}_{safe_name}.csv"
        write_recipients_csv(recipients, stats, campaign_name, campaign_id, output_path)
        print(f"  Wrote: {output_path}")

        time.sleep(1)  # Reporting API rate limit: 2/min

    print("Done.")


if __name__ == "__main__":
    main()
