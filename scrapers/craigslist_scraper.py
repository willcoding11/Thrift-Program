"""
Craigslist scraper — searches the 'for sale' section via HTML scraping.
"""

import re
import logging
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://{city}.craigslist.org/search/sss?query={query}&max_price={max_price}&sort=date"


def scrape(query, config):
    """
    Return a list of listing dicts from Craigslist.
    Each dict: {title, price, url, source, location}
    """
    city = config["locations"]["craigslist_city"]
    max_price = config.get("max_price", 500)
    url = BASE_URL.format(
        city=quote_plus(city),
        query=quote_plus(query),
        max_price=max_price,
    )

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

        results = soup.select("li.cl-static-search-result")
        if not results:
            # Fallback: try older Craigslist markup
            results = soup.select(".result-row")

        for item in results[:20]:  # cap per query
            listing = _parse_listing(item, city)
            if listing:
                listings.append(listing)

        logger.info("Craigslist: found %d listings for '%s'", len(listings), query)
    except requests.RequestException as e:
        logger.warning("Craigslist request failed: %s", e)

    return listings


def _parse_listing(item, city):
    """Extract a single listing from a BeautifulSoup element."""
    try:
        # New-style Craigslist markup
        link = item.select_one("a")
        title_el = item.select_one(".title") or item.select_one("a")
        price_el = item.select_one(".price")

        if not title_el:
            return None

        title = title_el.get_text(strip=True)
        url = link["href"] if link else ""
        if url and not url.startswith("http"):
            url = f"https://{city}.craigslist.org{url}"

        price = _extract_price(price_el.get_text(strip=True)) if price_el else None

        return {
            "title": title,
            "price": price,
            "url": url,
            "source": "craigslist",
            "location": city,
        }
    except (AttributeError, KeyError, TypeError):
        return None


def _extract_price(text):
    """Pull a numeric price from a string like '$45' or '$1,200'."""
    match = re.search(r"\$?([\d,]+(?:\.\d{2})?)", text)
    if match:
        return float(match.group(1).replace(",", ""))
    return None
