"""
eBay scraper — searches completed and active listings to find deals.
Uses eBay's public search pages (no API key required).
"""

import re
import logging
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SEARCH_URL = (
    "https://www.ebay.com/sch/i.html?"
    "_nkw={query}&_udhi={max_price}&LH_BIN=1&_sop=10&rt=nc"
)


def scrape(query, config):
    """
    Return a list of listing dicts from eBay.
    Each dict: {title, price, url, source, original_price, location}
    """
    max_price = config.get("max_price", 500)
    url = SEARCH_URL.format(query=quote_plus(query), max_price=max_price)

    listings = []
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.select(".s-item")

        for item in items[:20]:
            listing = _parse_item(item)
            if listing:
                listings.append(listing)

        logger.info("eBay: found %d listings for '%s'", len(listings), query)
    except requests.RequestException as e:
        logger.warning("eBay request failed: %s", e)

    return listings


def _parse_item(item):
    """Parse a single eBay search result element."""
    try:
        title_el = item.select_one(".s-item__title")
        price_el = item.select_one(".s-item__price")
        link_el = item.select_one(".s-item__link")
        orig_price_el = item.select_one(".STRIKETHROUGH")

        if not title_el or not price_el:
            return None

        title = title_el.get_text(strip=True)
        if title.lower() in ("shop on ebay", ""):
            return None

        price = _extract_price(price_el.get_text(strip=True))
        url = link_el["href"] if link_el else ""
        original_price = (
            _extract_price(orig_price_el.get_text(strip=True))
            if orig_price_el
            else None
        )

        return {
            "title": title,
            "price": price,
            "url": url.split("?")[0] if url else "",
            "source": "ebay",
            "original_price": original_price,
            "location": "online",
        }
    except (AttributeError, KeyError, TypeError):
        return None


def _extract_price(text):
    """Pull a numeric price from text like '$45.00' or '$1,200.00'."""
    match = re.search(r"\$?([\d,]+(?:\.\d{2})?)", text)
    if match:
        return float(match.group(1).replace(",", ""))
    return None
