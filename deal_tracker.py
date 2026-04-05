"""
Simple persistent tracker to avoid sending duplicate notifications for
the same listing. Uses a local JSON file to remember seen listing URLs.
"""

import json
import os
import time
import logging

logger = logging.getLogger(__name__)

TRACKER_PATH = os.path.join(os.path.dirname(__file__), ".seen_deals.json")
MAX_AGE_DAYS = 7  # Forget deals older than this


def load_seen():
    """Load the set of previously seen deal URLs with timestamps."""
    if not os.path.exists(TRACKER_PATH):
        return {}
    try:
        with open(TRACKER_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_seen(seen):
    """Save the seen-deals dict to disk."""
    with open(TRACKER_PATH, "w") as f:
        json.dump(seen, f)


def filter_new(deals):
    """
    Return only deals we haven't notified about before.
    Also records the new deals so future calls won't re-notify.
    """
    seen = load_seen()
    now = time.time()

    # Prune old entries
    cutoff = now - (MAX_AGE_DAYS * 86400)
    seen = {url: ts for url, ts in seen.items() if ts > cutoff}

    new_deals = []
    for deal in deals:
        url = deal.get("url", "")
        if url and url not in seen:
            new_deals.append(deal)
            seen[url] = now

    save_seen(seen)
    logger.info("Tracker: %d new deals out of %d total", len(new_deals), len(deals))
    return new_deals
