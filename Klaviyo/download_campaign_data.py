#!/usr/bin/env python3
"""
Download Klaviyo email campaign data: recipients with per-recipient opens and clicks.

Uses the Klaviyo API to fetch:
- Recipient lists (email) per campaign
- Per-recipient opens and clicks from the Events API

Usage:
    python download_campaign_data.py N "search string"
    python download_campaign_data.py 5 "TSC Newsletter"

Finds the N most recent sent campaigns whose name contains the search string,
aggregates opens and clicks across all of them, outputs one row per email.

Requires KLAVIYO_API_KEY in environment or config.env.
"""

import os
import sys
import csv
import argparse
import time
from datetime import datetime, timedelta
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
API_EVENTS = f"{KLAVIYO_BASE}/api/events/"
API_METRICS = f"{KLAVIYO_BASE}/api/metrics"
API_REVISION = "2024-10-15"
EVENTS_REVISION = "2024-02-15"


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


def get_campaigns(api_key, channel="email", name_filter=None):
    """Fetch campaigns. If name_filter given, filter by name contains."""
    campaigns = []
    url = API_CAMPAIGNS
    flt = f"equals(messages.channel,'{channel}')"
    if name_filter:
        flt = f"and({flt},contains(name,\"{name_filter}\"))"
    params = {"filter": flt, "fields[campaign]": "name,status,send_time,created_at"}
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
                "send_time": attrs.get("send_time"),
                "created_at": attrs.get("created_at"),
            })
        url = data.get("links", {}).get("next")
        if not url:
            break
        params = {}
        time.sleep(0.2)
    return campaigns


def get_campaign(api_key, campaign_id, include_messages=False):
    """Fetch a single campaign with audiences and optionally campaign-messages."""
    params = {}
    if include_messages:
        params["include"] = "campaign-messages"
    resp = requests.get(
        API_CAMPAIGN.format(id=campaign_id),
        params=params,
        headers=_api_headers(api_key),
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    item = data.get("data", {})
    attrs = item.get("attributes", {})
    result = {
        "id": item.get("id"),
        "name": attrs.get("name", ""),
        "status": attrs.get("status", ""),
        "audiences": attrs.get("audiences", {}).get("included", []),
        "send_time": attrs.get("send_time"),
    }
    if include_messages:
        msg_data = item.get("relationships", {}).get("campaign-messages", {}).get("data", [])
        result["message_ids"] = [m.get("id") for m in msg_data if m.get("id")]
        result["included"] = data.get("included", [])
    return result


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


def _get_metric_ids(api_key):
    """Get metric IDs for Opened Email and Clicked Email."""
    metrics = {}
    url = API_METRICS
    params = {}
    while True:
        resp = requests.get(url, params=params, headers=_api_headers(api_key), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("data", []):
            name = item.get("attributes", {}).get("name", "")
            if name == "Opened Email":
                metrics["opened"] = item.get("id")
            elif name == "Clicked Email":
                metrics["clicked"] = item.get("id")
        url = data.get("links", {}).get("next")
        if not url or (metrics.get("opened") and metrics.get("clicked")):
            break
        params = {}
        time.sleep(0.2)
    return metrics


def _get_events_for_metric(api_key, metric_id, start_dt, end_dt):
    """Fetch events for a metric in datetime range. Returns list of {profile_id, event_properties}."""
    events = []
    url = API_EVENTS
    # Datetime values must not be quoted per Klaviyo API
    flt = f"and(equals(metric_id,\"{metric_id}\"),greater-or-equal(datetime,{start_dt}),less-than(datetime,{end_dt}))"
    params = {
        "filter": flt,
        "include": "profile",
        "fields[event]": "event_properties,datetime",
        "fields[profile]": "email",
        "page[size]": 200,
        "sort": "datetime",
    }
    headers = {**_api_headers(api_key), "revision": EVENTS_REVISION}
    while True:
        resp = requests.get(url, params=params, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("data", []):
            rel = item.get("relationships", {})
            profile_data = rel.get("profile", {}).get("data", {})
            profile_id = profile_data.get("id") if profile_data else None
            props = item.get("attributes", {}).get("event_properties", {}) or {}
            events.append({"profile_id": profile_id, "event_properties": props})
        url = data.get("links", {}).get("next")
        if not url:
            break
        params = {}
        time.sleep(0.1)
    return events


def _event_matches_campaign(props, message_ids_set, campaign_name, include_all=False):
    """Check if event belongs to our campaign via message ID or Campaign Name."""
    if include_all:
        return True
    if not props:
        return False
    # Try message ID fields (exact match)
    msg_id = (
        props.get("$message")
        or props.get("$attributed_message")
        or props.get("Message ID")
        or props.get("message_id")
    )
    if msg_id and message_ids_set and msg_id in message_ids_set:
        return True
    # Fallback: match by Campaign Name (events include this)
    camp_name = props.get("Campaign Name") or props.get("Campaign Name ")
    if campaign_name and camp_name:
        cn, ev_cn = str(campaign_name), str(camp_name)
        if cn in ev_cn or ev_cn in cn:
            return True
    return False


def get_per_recipient_engagement(api_key, campaign_id, message_ids, send_time, campaign_name=None):
    """Get per-recipient open/click counts via Events API."""
    metric_ids = _get_metric_ids(api_key)
    if not metric_ids.get("opened") and not metric_ids.get("clicked"):
        return {}

    try:
        if send_time:
            st = datetime.fromisoformat(send_time.replace("Z", "+00:00"))
        else:
            st = datetime.utcnow() - timedelta(days=30)
    except Exception:
        st = datetime.utcnow() - timedelta(days=60)
    start_dt = (st - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    end_dt = (st + timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    message_ids_set = set(message_ids or []) or {campaign_id}
    engagement = {}  # profile_id -> {"opened": 0, "clicked": 0}

    for metric_key, metric_id in metric_ids.items():
        if not metric_id:
            continue
        event_type = "opened" if metric_key == "opened" else "clicked"
        events_raw = _get_events_for_metric(api_key, metric_id, start_dt, end_dt)
        matched = sum(
            1
            for ev in events_raw
            if _event_matches_campaign(
                ev.get("event_properties"), message_ids_set, campaign_name, include_all=False
            )
        )
        # If no events matched message/campaign filter, include all (fallback for API quirks)
        use_all = len(events_raw) > 0 and matched == 0
        if use_all:
            print(f"    Note: Using all {len(events_raw)} {event_type} events (message filter matched 0)")
        for ev in events_raw:
            pid = ev.get("profile_id")
            if not pid:
                continue
            if not _event_matches_campaign(
                ev.get("event_properties"), message_ids_set, campaign_name, include_all=use_all
            ):
                continue
            if pid not in engagement:
                engagement[pid] = {"opened": 0, "clicked": 0}
            engagement[pid][event_type] += 1
        time.sleep(0.2)
    return engagement


def write_aggregated_csv(aggregated, output_path):
    """Write CSV: one row per email with summed opens and clicks."""
    fieldnames = ["email", "opened", "clicked"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for email in sorted(aggregated.keys(), key=str.lower):
            eng = aggregated[email]
            writer.writerow({
                "email": email,
                "opened": eng.get("opened", 0),
                "clicked": eng.get("clicked", 0),
            })


def main():
    parser = argparse.ArgumentParser(
        description="Download Klaviyo campaign data: N most recent campaigns matching search, aggregated opens/clicks per email."
    )
    parser.add_argument(
        "num_campaigns",
        type=int,
        help="Number of most recent campaigns to process.",
    )
    parser.add_argument(
        "search_string",
        help="Search string; campaign name must contain this.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="Output directory for CSV file (default: current directory).",
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

    print(f"Finding campaigns matching '{args.search_string}'...")
    campaigns = get_campaigns(api_key, channel="email", name_filter=args.search_string)
    sent = [c for c in campaigns if c.get("status") == "Sent"]
    if not sent:
        print(f"No sent campaigns found matching '{args.search_string}'.", file=sys.stderr)
        sys.exit(1)

    # Sort by send_time (most recent first), fallback to created_at
    def sort_key(c):
        t = c.get("send_time") or c.get("created_at") or ""
        return t

    sent.sort(key=sort_key, reverse=True)
    to_process = sent[: args.num_campaigns]
    print(f"Processing {len(to_process)} most recent campaign(s):")

    aggregated = {}  # email -> {opened: sum, clicked: sum}

    for campaign in to_process:
        campaign_id = campaign["id"]
        print(f"  {campaign['name']} ({campaign_id})...")
        camp_full = get_campaign(api_key, campaign_id, include_messages=True)
        message_ids = camp_full.get("message_ids", [])
        send_time = camp_full.get("send_time")

        try:
            recipients = get_campaign_recipients(api_key, campaign_id)
            print(f"    Recipients: {len(recipients)}")
        except requests.HTTPError as e:
            print(f"    Error fetching recipients: {e}", file=sys.stderr)
            continue

        # Add all recipients to aggregated (with 0/0 if new)
        for r in recipients:
            email = (r.get("email", "") or "").lower()
            if not email:
                continue
            if email not in aggregated:
                aggregated[email] = {"opened": 0, "clicked": 0}

        print("    Fetching opens and clicks...")
        engagement = {}
        try:
            engagement = get_per_recipient_engagement(
                api_key, campaign_id, message_ids, send_time, campaign["name"]
            )
        except requests.HTTPError as e:
            print(f"    Note: Could not fetch engagement: {e}", file=sys.stderr)

        # Add engagement counts to aggregated
        pid_to_email = {r.get("customer_id", ""): (r.get("email", "") or "").lower() for r in recipients}
        for pid, eng in engagement.items():
            email = pid_to_email.get(pid, "")
            if not email:
                continue
            aggregated[email]["opened"] += eng.get("opened", 0)
            aggregated[email]["clicked"] += eng.get("clicked", 0)

        time.sleep(0.5)

    output_path = output_dir / "TSC-Newsletter-Opens.csv"
    write_aggregated_csv(aggregated, output_path)
    print(f"Wrote: {output_path} ({len(aggregated)} unique emails)")


if __name__ == "__main__":
    main()
