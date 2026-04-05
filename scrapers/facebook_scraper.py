"""
Facebook Marketplace scraper.

NOTE: Facebook Marketplace aggressively blocks automated access. This module
uses their public search URL, but it will likely require a browser-based
approach (Selenium) to work reliably. If basic HTTP requests fail, the module
gracefully returns an empty list and logs a warning.

For reliable Facebook Marketplace scraping, consider:
  1. Using the Selenium-based fallback (enable in config)
  2. Using a residential proxy
  3. Running in a real browser profile
"""

import re
import logging
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SEARCH_URL = (
    "https://www.facebook.com/marketplace/search?"
    "query={query}&maxPrice={max_price}"
)


def scrape(query, config):
    """
    Attempt to scrape Facebook Marketplace listings.
    Returns a list of listing dicts, or an empty list if blocked.
    Each dict: {title, price, url, source, location}
    """
    max_price = config.get("max_price", 500)
    city = config["locations"].get("facebook_city", "")
    url = SEARCH_URL.format(query=quote_plus(query), max_price=max_price)

    listings = []

    # Try Selenium first if available
    try:
        listings = _scrape_with_selenium(query, config)
        if listings:
            return listings
    except ImportError:
        pass  # Selenium not installed, fall through to requests
    except Exception as e:
        logger.debug("Selenium Facebook scrape failed: %s", e)

    # Fallback: plain HTTP (often blocked by Facebook)
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=15)

        if resp.status_code == 200 and "marketplace" in resp.text.lower():
            soup = BeautifulSoup(resp.text, "html.parser")
            listings = _parse_html(soup, city)
            logger.info(
                "Facebook: found %d listings for '%s'", len(listings), query
            )
        else:
            logger.warning(
                "Facebook Marketplace returned status %d or login wall. "
                "Install selenium + chromedriver for better results.",
                resp.status_code,
            )
    except requests.RequestException as e:
        logger.warning("Facebook request failed: %s", e)

    return listings


def _parse_html(soup, city):
    """Best-effort parse of Facebook Marketplace HTML."""
    listings = []
    # Facebook's HTML is heavily obfuscated; target common patterns
    for card in soup.select("[data-testid='marketplace_feed_item']")[:20]:
        try:
            title_el = card.select_one("span")
            price_text = ""
            for span in card.select("span"):
                if "$" in span.get_text():
                    price_text = span.get_text(strip=True)
                    break

            link = card.select_one("a[href*='/marketplace/item/']")
            url = f"https://www.facebook.com{link['href']}" if link else ""

            title = title_el.get_text(strip=True) if title_el else "Unknown"
            price = _extract_price(price_text)

            listings.append({
                "title": title,
                "price": price,
                "url": url,
                "source": "facebook",
                "location": city,
            })
        except (AttributeError, KeyError, TypeError):
            continue
    return listings


def _scrape_with_selenium(query, config):
    """Use Selenium with a headless Chrome browser for Facebook Marketplace."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    max_price = config.get("max_price", 500)
    city = config["locations"].get("facebook_city", "")
    url = SEARCH_URL.format(query=quote_plus(query), max_price=max_price)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    listings = []
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/marketplace/item/']"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
        listings = _parse_html(soup, city)
        logger.info("Facebook (Selenium): found %d listings for '%s'", len(listings), query)
    except Exception as e:
        logger.warning("Facebook Selenium scrape failed: %s", e)
    finally:
        driver.quit()

    return listings


def _extract_price(text):
    """Pull a numeric price from text like '$45' or '$1,200'."""
    if not text:
        return None
    match = re.search(r"\$?([\d,]+(?:\.\d{2})?)", text)
    if match:
        return float(match.group(1).replace(",", ""))
    return None
