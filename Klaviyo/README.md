# Klaviyo Campaign Data

Download email recipient lists, opens, and clicks for Klaviyo campaigns.

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API access**
   - Copy `config.example` to `config.env`
   - Add your Klaviyo Private API Key to `config.env`
   - Or set `KLAVIYO_API_KEY` in your environment

3. **API key scopes**
   Your Klaviyo Private API key needs:
   - `campaigns:read` – list campaigns and recipients
   - `events:read` – (optional, for future per-recipient events)
   - `metrics:read` – (optional, for conversion metric)

   Create keys at: https://www.klaviyo.com/account#api-keys

## Usage

**Download all sent email campaigns:**
```bash
./download_campaign_data.sh --all
```

**Download specific campaigns by ID:**
```bash
./download_campaign_data.sh CAMPAIGN_ID1 CAMPAIGN_ID2
```

**Output directory:**
```bash
./download_campaign_data.sh --all -o ./output
```

## Output

For each campaign, the script writes a CSV with:

| Column           | Description                                      |
|------------------|--------------------------------------------------|
| campaign_id      | Klaviyo campaign ID                              |
| campaign_name    | Campaign name                                   |
| email            | Recipient email                                 |
| customer_id      | Klaviyo profile/customer ID                     |
| status           | Delivery status (e.g. Sent)                      |
| campaign_opens   | Total opens for the campaign (aggregate)         |
| campaign_clicks  | Total clicks for the campaign (aggregate)        |
| campaign_open_rate | Campaign open rate (0–1)                      |
| campaign_click_rate | Campaign click rate (0–1)                    |

**Note:** Opens and clicks are campaign-level aggregates. Per-recipient open/click data is not provided by the Klaviyo Reporting API. To get per-recipient engagement, you would need to use the Events API and correlate events by profile and campaign.

## What You Need to Provide

1. **Klaviyo Private API Key** – Required. Create one in your Klaviyo account with `campaigns:read` scope.

2. **Campaign IDs** (if not using `--all`) – You can find these in the Klaviyo UI when viewing a campaign (in the URL or campaign settings).

3. **Conversion metric ID** (optional) – The Reporting API requires a conversion metric. The default `RESQ6t` is a common placeholder. If you see errors, look up your "Placed Order" or similar metric ID in Klaviyo and set `CONVERSION_METRIC_ID` in config.env.
