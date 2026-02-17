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

**Download N most recent campaigns matching search:**
```bash
./download_campaign_data.sh 5 "TSC Newsletter"
```

- First parameter: number of campaigns to process (e.g. 5)
- Second parameter: search string; campaign name must contain this

**Output directory:**
```bash
./download_campaign_data.sh 5 "TSC Newsletter" -o ./output
```

## Output

Writes `TSC-Newsletter-Opens.csv` with one row per unique email across all N campaigns:

| Column | Description |
|--------|-------------|
| email  | Recipient email |
| opened | Sum of opens across all N campaigns |
| clicked | Sum of clicks across all N campaigns |

## What You Need to Provide

1. **Klaviyo Private API Key** – Required. Create one in your Klaviyo account with the scopes listed above.

2. **Number of campaigns** – How many of the most recent matching campaigns to include.
3. **Search string** – Campaign name must contain this (e.g. "TSC Newsletter").
