# NASDAQ Non-Compliant Stock Monitor

Watches every company on NASDAQ's
[non-compliant company list](https://www.nasdaq.com/market-activity/stocks/non-compliant-company-list)
and sends a **Telegram alert** whenever a stock's price moves **≥ 25%** since
the previous check. It runs **every ~16 minutes** on GitHub Actions — no server
required.

## How it works

1. Fetches the current non-compliant tickers from NASDAQ's public JSON API
   (the same endpoint the website uses).
2. Fetches each ticker's latest price.
3. Compares each price against the price stored from the previous run
   (`state.json`).
4. Sends a Telegram message for any ticker that moved past the threshold.
5. Commits the updated `state.json` back to the repo so the next run has a
   fresh baseline.

Because the comparison uses the **stored last price**, it is robust to GitHub's
imperfect cron timing — a late run just means a slightly longer interval.

## Setup

### 1. Create a Telegram bot
1. Message [@BotFather](https://t.me/BotFather), send `/newbot`, follow the
   prompts, and copy the **bot token** (looks like `123456789:AAE...`).
2. Send any message to your new bot.
3. Get your **chat ID**: open
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser and read
   `result[].message.chat.id`. (For a group/channel, add the bot there first.)

### 2. Add GitHub secrets
In your repo: **Settings → Secrets and variables → Actions → New repository secret**
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### 3. Allow the workflow to commit state
**Settings → Actions → General → Workflow permissions → Read and write permissions.**
(The `monitor.yml` workflow already requests `contents: write`.)

### 4. Push and enable
Push this repo to GitHub. The schedule starts automatically. You can also
trigger a run manually from the **Actions** tab (**Run workflow**).

## Local testing

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test without sending Telegram messages:
DRY_RUN=true python -m monitor.main

# Real send (needs the two env vars):
export TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=...
python -m monitor.main
```

Run it twice a few minutes apart to see the comparison in action (the first run
only records a baseline).

## Configuration

All optional, set as env vars (or GitHub secrets/variables):

| Variable | Default | Meaning |
|---|---|---|
| `THRESHOLD_PCT` | `25` | % move since last check that triggers an alert |
| `DIRECTION` | `up` | `up` = only rises; `any` = rises **or** falls |
| `DRY_RUN` | `false` | `true` = log alerts instead of sending them |
| `MAX_WORKERS` | `8` | Concurrent price requests |
| `STATE_FILE` | `state.json` | Where last prices are stored |

## Project layout

```
monitor/
  config.py     # env-based settings
  nasdaq.py     # fetch non-compliant list + prices
  state.py      # load/save state.json
  telegram.py   # send alerts
  main.py       # orchestration (python -m monitor.main)
.github/workflows/monitor.yml   # scheduled runner
state.json      # persisted last prices (updated each run)
```

## Notes & caveats

- NASDAQ's quote endpoints are **undocumented** and could change without
  notice; the monitor fails safe (logs and skips) if a request breaks.
- A 25% move is sizable; for these low-priced stocks it does happen, but
  expect alerts to be infrequent. Adjust `THRESHOLD_PCT` to tune sensitivity.
- Prices update during market hours; outside hours consecutive runs will show
  no change.
```
