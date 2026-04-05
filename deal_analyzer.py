"""
Deal analysis engine.

Scores listings to determine if they're likely good deals based on:
  - Price relative to the max_price threshold
  - Discount from original price (eBay often shows this)
  - Keywords in the title that signal value (e.g. "OBO", "must sell", "moving")
"""

import logging
import re

logger = logging.getLogger(__name__)

# Title keywords that often indicate a motivated seller / good deal
DEAL_KEYWORDS = [
    "obo", "or best offer", "must sell", "moving", "need gone",
    "priced to sell", "make offer", "firm", "lowered", "reduced",
    "clearance", "liquidation", "estate sale", "garage sale",
    "pick up only", "free delivery", "bundle",
]

# Keywords that indicate possible junk or scam
WARN_KEYWORDS = [
    "for parts", "broken", "as-is", "as is", "not working",
    "damaged", "cracked", "salvage",
]

# Compound phrases that clearly indicate an accessory, NOT the actual item.
# These override even if the title mentions a real device name.
ACCESSORY_PHRASES = [
    "laptop case", "laptop bag", "laptop sleeve", "laptop stand",
    "laptop charger", "laptop dock", "laptop cover", "laptop skin",
    "laptop mount", "laptop tray", "laptop backpack", "laptop carry",
    "laptop briefcase", "laptop cooling", "carrying case",
    "phone case", "phone charger", "phone cord", "phone cable",
    "phone mount", "phone holder", "phone stand", "phone screen protector",
    "iphone case", "iphone charger", "iphone cord", "iphone cable",
    "iphone screen protector", "iphone cover",
    "macbook case", "macbook charger", "macbook sleeve", "macbook cover",
    "macbook skin", "macbook adapter", "macbook cable",
    "power adapter", "ac adapter", "power supply",
    "docking station", "dock station",
    "screen protector", "tempered glass",
    "printer bed", "print bed", "bed plate", "pei plate", "build plate",
    "printer nozzle", "hot end", "hotend", "extruder",
    "heat sink", "limit switch", "printer parts", "printer cable",
    "filament", "printer plate",
    "remote control", "webcam", "web camera",
    "fisher price", "toy phone", "toy laptop",
    "figurine", "poster", "magazine rack", "cushion",
    "battery for", "keyboard for",
    "laptop box", "shelf cart", "desk ", "office desk",
    "backpack", "messenger bag", "travel bag", "computer bag",
    "usb hub", "usb adapter", "usb c to", "type-c to",
    "hdmi adapter", "hdmi cable", "multiport",
    "surge protector", "power strip", "extension cord",
    "wifi card", "wireless card",
    "iphone case", "galaxy case", "samsung case",
    "otterbox", "wallet case", "wristlet",
    "charging stand", "charging pad", "charging dock",
    "cable lock", "lockable cover",
    "sleeve case", "protective cover",
    "cast iron", "trophy", "auction",
    "reprap", "controller board",
    "bolts", "screws", "fastener",
    "iphone case", " case fits", " cases total", "pro max case",
    "pro case", "ultra case", " case new", " case &",
    "pixel case", "minimalist slim",
    "galaxy buds", "pixel buds", "earbuds", "earphones",
    "galaxy watch", "smart watch", "smartwatch",
    "galaxy tab", "galaxy tablet",
    "carplay adapter", "tunecast",
    "screen replacement", "repair service",
    "cd player", "sous vide", "cooker", "bluetooth speaker",
    "modem", "router",
    "wallet tracker", "item finder", "airtag",
    "charging station", "cd slot mount",
    "misc. cable", "box of misc",
    "ender plate", "creality plate",
    "thinkpad dock", "thinkpad battery", "thinkpad thunderbolt",
    "mini dock",
    "dual 4k", "video adapter", "hdmi converter",
    "oem lenovo", "oem battery", "yoga battery",
    "wifi adapter", "wi-fi adapter", "wireless adapter",
    "usb adapter", "usb wireless",
]


def analyze(listings, config):
    """
    Score each listing and return only the ones that look like good deals.
    Returns a sorted list (best deals first) of dicts with an added 'score' key.
    """
    max_price = config.get("max_price", 500)
    min_discount = config.get("min_discount_percent", 30)
    scored = []

    for listing in listings:
        score = _score_listing(listing, max_price, min_discount)
        if score > 0:
            listing["score"] = score
            scored.append(listing)

    scored.sort(key=lambda x: x["score"], reverse=True)
    logger.info("Deal analyzer: %d/%d listings passed as deals", len(scored), len(listings))
    return scored


def _score_listing(listing, max_price, min_discount):
    """
    Return a score from 0-100. Higher = better deal. 0 = not a deal.
    """
    price = listing.get("price")
    title = (listing.get("title") or "").lower()
    score = 0

    # No price = can't evaluate
    if price is None:
        return 0

    # Penalize items flagged as broken/junk
    for kw in WARN_KEYWORDS:
        if kw in title:
            return 0

    # Filter out accessories — if the title matches a known accessory phrase,
    # it's not the actual device, just an add-on
    if any(phrase in title for phrase in ACCESSORY_PHRASES):
        return 0

    # --- Price scoring (0-50 points) ---
    if price <= 0:
        return 0
    if price <= max_price:
        # The further below max_price, the better
        price_ratio = 1 - (price / max_price)
        score += int(price_ratio * 50)

    # --- Discount scoring (0-30 points) ---
    original = listing.get("original_price")
    if original and original > 0 and price < original:
        discount_pct = ((original - price) / original) * 100
        if discount_pct >= min_discount:
            score += min(30, int(discount_pct * 0.3))

    # --- Keyword scoring (0-20 points) ---
    keyword_hits = sum(1 for kw in DEAL_KEYWORDS if kw in title)
    score += min(20, keyword_hits * 5)

    return score


def format_deal(deal):
    """Format a deal listing into a human-readable string."""
    price_str = f"${deal['price']:.2f}" if deal.get("price") else "No price"
    orig = deal.get("original_price")
    discount = ""
    if orig and deal.get("price") and orig > 0:
        pct = ((orig - deal["price"]) / orig) * 100
        discount = f" (was ${orig:.2f}, {pct:.0f}% off)"

    return (
        f"[{deal['source'].upper()}] {deal['title']}\n"
        f"  Price: {price_str}{discount}\n"
        f"  Score: {deal.get('score', '?')}/100\n"
        f"  Link:  {deal.get('url', 'N/A')}\n"
    )
