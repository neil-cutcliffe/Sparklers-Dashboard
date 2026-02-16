# Klaviyo Campaign Data

Download email recipient lists, opens, and clicks for Klaviyo campaigns.

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
## Prefer virtual environment
 #  python3 -m venv venv
 #  source venv/bin/activate
 #  pip install -r requirements.txt --force-reinstall

2. **Configure API access**
   - Copy `config.example` to `config.env`
   - Add your Klaviyo Private API Key to `config.env`
   - Or set `KLAVIYO_API_KEY` in your environment

3. **API key scopes**
   Your Klaviyo Private API key needs:
   - `campaigns:read` – list campaigns and get audience info
   - `lists:read` and `segments:read` – fetch audience profiles (recipients)
   - `profiles:read` – required for segment/list profile endpoints
   - `events:read` – per-recipient opens and clicks
   - `metrics:read` – Opened Email and Clicked Email metric IDs

   Create keys at: https://www.klaviyo.com/account#api-keys

## Usage

**Download by campaign name:**
```bash
./download_campaign_data.sh "TSC Newsletter Feb 15"
```

**Multiple campaigns:**
```bash
./download_campaign_data.sh "Campaign 1" "Campaign 2"
```

**Output directory:**
```bash
./download_campaign_data.sh "TSC Newsletter Feb 15" -o ./output
```

## Output

For each campaign, the script writes a CSV with one row per recipient:

| Column | Description |
|--------|-------------|
| email  | Recipient email |
| opened | Number of times this recipient opened the email |
| clicked | Number of times this recipient clicked a link |

## What You Need to Provide

1. **Klaviyo Private API Key** – Required. Create one in your Klaviyo account with the scopes listed above.

2. **Campaign name** – The exact or partial campaign name (e.g. "TSC Newsletter Feb 15"). The script finds sent campaigns whose name contains the given text.
