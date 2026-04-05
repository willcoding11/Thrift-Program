# Thrift Deal Notifier

A Python program that continuously monitors **Craigslist**, **eBay**, and **Facebook Marketplace** for good deals and sends you notifications when it finds them.

## Features

- **Multi-platform search** — Scrapes Craigslist, eBay, and Facebook Marketplace
- **Smart deal scoring** — Analyzes price, discounts, and listing keywords to find real deals
- **Duplicate detection** — Tracks seen listings so you never get notified twice
- **Desktop notifications** — Pop-up alerts when deals are found
- **Email alerts** — Optional email notifications via SMTP
- **Configurable** — JSON config for search terms, price limits, locations, and check intervals
- **CLI overrides** — Override any config setting from the command line

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run (creates default config.json on first run)
python monitor.py

# Edit config.json with your search preferences, then restart
python monitor.py
```

## Configuration

Edit `config.json` (auto-created on first run):

```json
{
  "search_queries": ["vintage guitar", "mechanical keyboard"],
  "max_price": 100,
  "min_discount_percent": 30,
  "check_interval_minutes": 15,
  "locations": {
    "craigslist_city": "newyork",
    "ebay_country": "US",
    "facebook_city": "new york"
  },
  "notifications": {
    "desktop": true,
    "email": {
      "enabled": false,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "sender_email": "you@gmail.com",
      "sender_password": "your-app-password",
      "recipient_email": "you@gmail.com"
    }
  },
  "platforms": {
    "craigslist": true,
    "ebay": true,
    "facebook": true
  }
}
```

### Key settings

| Setting | Description |
|---|---|
| `search_queries` | List of things to search for |
| `max_price` | Maximum price to consider |
| `min_discount_percent` | Minimum discount % to flag as a deal |
| `check_interval_minutes` | How often to check (in minutes) |
| `craigslist_city` | Your Craigslist city subdomain (e.g., `sfbay`, `chicago`, `newyork`) |
| `platforms` | Enable/disable individual platforms |

## CLI Usage

```bash
# Run with defaults from config.json
python monitor.py

# Search for a specific item
python monitor.py --query "nintendo switch"

# Set max price
python monitor.py --query "bike" --max-price 200

# Run once (don't loop)
python monitor.py --once

# Check every 5 minutes
python monitor.py --interval 5

# Multiple search terms
python monitor.py -q "guitar" "amplifier" "pedals"
```

## Email Setup (Gmail)

1. Enable 2-factor auth on your Google account
2. Generate an App Password at https://myaccount.google.com/apppasswords
3. Use the app password (not your real password) in config.json

## Facebook Marketplace Note

Facebook aggressively blocks scrapers. For best results:
- Install `selenium` and Chrome/Chromium + ChromeDriver
- The program will automatically use Selenium for Facebook if available
- Falls back to HTTP requests (less reliable)

## How Deal Scoring Works

Each listing gets a score from 0-100:
- **Price score (0-50)**: How far below your max price
- **Discount score (0-30)**: Original vs. sale price (eBay often shows this)
- **Keyword score (0-20)**: Motivated-seller keywords like "must sell", "OBO", "moving"
- **Filtered out**: Items marked "broken", "as-is", "for parts"

Only listings with a score > 0 trigger notifications.
