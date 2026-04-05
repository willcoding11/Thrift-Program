"""
Configuration for the Marketplace Deal Notifier.
Edit config.json to customize your searches and notification settings.
"""

import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULT_CONFIG = {
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
        "desktop": True,
        "email": {
            "enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "",
            "sender_password": "",
            "recipient_email": ""
        }
    },
    "platforms": {
        "craigslist": True,
        "ebay": True,
        "facebook": True
    }
}


def load_config():
    """Load config from config.json, creating it with defaults if missing."""
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        print(f"Created default config at {CONFIG_PATH} — edit it with your preferences.")
        return DEFAULT_CONFIG

    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(config):
    """Write config dict to config.json."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
