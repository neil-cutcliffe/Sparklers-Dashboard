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

# API endpoints (new API - v1 deprecated June 2024)
KLAVIYO_BASE = "https://a.klaviyo.com"
API_CAMPAIGNS = f"{KLAVIYO_BASE}/api/campaigns"
API_CAMPAIGN = f"{KLAVIYO_BASE}/api/campaigns/{{id}}"
API_SEGMENT_PROFILES = f"{KLAVIYO_BASE}/api/segments/{{id}}/profiles/"
API_LIST_PROFILES = f"{KLAVIYO_BASE}/api/lists/{{id}}/profiles/"
REPORTING_CAMPAIGN_VALUES = f"{KLAVIYO_BASE}/api/campaign-values-reports/"
REPORTING_REVISION = "2024-10-15"
API_REVISION = "2024-10-15"


def _api_headers(api_key):
    return {
        "Authorization": f"Klaviyo-API-Key {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "revision": API_REVISION,
    }


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
                    key = key.strip().replace("export ", "")
                    if key == "KLAVIYO_API_KEY":
                        return value.strip()

    return None


def get_campaigns(api_key, channel="email"):
    """Fetch all campaigns using new API (channel filter required)."""
    campaigns = []
    url = API_CAMPAIGNS
    params = {"filter": f"equals(messages.channel,'{channel}')"}
    while True:
        resp = requests.get(url, params=params, headers=_api_headers(api_key), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("data", []):
            attrs = item.get("attributes", {})
            campaigns.append({
                "id": item.get("id"),
                "name": attrs.get("name", ""),
                "status": attrs.get("status", ""),
            })
        url = data.get("links", {}).get("next")
        if not url:
            break
        params = {}  # Next URL has params
        time.sleep(0.2)
    return campaigns


def get_campaign(api_key, campaign_id):
    """Fetch a single campaign with audiences."""
    resp = requests.get(
        API_CAMPAIGN.format(id=campaign_id),
        headers=_api_headers(api_key),
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    item = data.get("data", {})
    attrs = item.get("attributes", {})
    return {
        "id": item.get("id"),
        "name": attrs.get("name", ""),
        "status": attrs.get("status", ""),
        "audiences": attrs.get("audiences", {}).get("included", []),
    }


def _get_profiles_from_resource(api_key, resource_id, is_segment):
    """Fetch profiles from a segment or list (paginated)."""
    url = (API_SEGMENT_PROFILES if is_segment else API_LIST_PROFILES).format(id=resource_id)
    profiles = []
    params = {"page[size]": 100}
    while True:
        resp = requests.get(url, params=params, headers=_api_headers(api_key), timeout=60)
        if resp.status_code == 404:
            return None  # Wrong resource type
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("data", []):
            attrs = item.get("attributes", {})
            profiles.append({
                "email": attrs.get("email", ""),
                "customer_id": item.get("id", ""),
                "status": "Sent",  # Audience members are targeted recipients
            })
        url = data.get("links", {}).get("next")
        if not url:
            break
        params = {}
        time.sleep(0.2)
    return profiles


def get_campaign_recipients(api_key, campaign_id):
    """Fetch recipients via campaign audiences (lists/segments)."""
    campaign = get_campaign(api_key, campaign_id)
    audience_ids = campaign.get("audiences", [])
    if not audience_ids:
        return []

    seen = set()
    recipients = []
    for aud_id in audience_ids:
        profs = _get_profiles_from_resource(api_key, aud_id, is_segment=True)
        if profs is None:
            profs = _get_profiles_from_resource(api_key, aud_id, is_segment=False)
        if profs:
            for p in profs:
                key = (p.get("email", ""), p.get("customer_id", ""))
                if key not in seen and key[0]:
                    seen.add(key)
                    recipients.append(p)
        time.sleep(0.2)
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
        campaigns = get_campaigns(api_key, channel="email")
        campaign_ids = [c["id"] for c in campaigns if c.get("status") == "Sent"]
        if not campaign_ids:
            print("No sent email campaigns found.")
            return
        print(f"Found {len(campaign_ids)} sent email campaign(s).")
        campaigns_by_id = {c["id"]: c for c in campaigns}
    else:
        if not args.campaign_ids:
            parser.error("Provide campaign IDs or use --all")
        campaign_ids = args.campaign_ids
        campaigns_by_id = {}

    for campaign_id in campaign_ids:
        campaign_name = campaigns_by_id.get(campaign_id, {}).get("name", "Unknown")
        if campaign_name == "Unknown":
            try:
                camp = get_campaign(api_key, campaign_id)
                campaign_name = camp.get("name", campaign_id)
            except requests.HTTPError:
                pass

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
