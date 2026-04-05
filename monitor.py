#!/usr/bin/env python3
"""
Thrift Deal Notifier — Main entry point.

Continuously monitors Craigslist, eBay, and Facebook Marketplace for deals
matching your search criteria and sends notifications when good deals appear.

Usage:
    python monitor.py                    # Run with config.json settings
    python monitor.py --query "guitar"   # Override search query
    python monitor.py --max-price 50     # Override max price
    python monitor.py --once             # Run once and exit (no loop)
    python monitor.py --interval 5       # Check every 5 minutes
"""

import argparse
import logging
import os
import sys
import time

from config import load_config
from scrapers import craigslist_scraper, ebay_scraper, facebook_scraper
from deal_analyzer import analyze, format_deal
from deal_tracker import filter_new
from notifications.notifier import notify

logger = logging.getLogger("monitor")


def setup_logging(log_file=None):
    """Configure logging to console and optionally to a file."""
    handlers = [logging.StreamHandler()]
    if log_file:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )

SCRAPERS = {
    "craigslist": craigslist_scraper,
    "ebay": ebay_scraper,
    "facebook": facebook_scraper,
}


def run_search(config):
    """Run one full search cycle across all enabled platforms."""
    queries = config.get("search_queries", [])
    platforms = config.get("platforms", {})
    all_deals = []

    for query in queries:
        logger.info("Searching for: '%s'", query)
        all_listings = []

        for name, scraper in SCRAPERS.items():
            if platforms.get(name, True):
                logger.info("  Checking %s...", name)
                try:
                    listings = scraper.scrape(query, config)
                    all_listings.extend(listings)
                except Exception as e:
                    logger.error("  %s scraper crashed: %s", name, e)

        # Analyze and filter
        deals = analyze(all_listings, config)
        new_deals = filter_new(deals)
        all_deals.extend(new_deals)

    if all_deals:
        logger.info("Found %d new deal(s)!", len(all_deals))
        print("\n" + "=" * 50)
        print(f"  {len(all_deals)} NEW DEAL(S) FOUND!")
        print("=" * 50)
        for deal in all_deals:
            print(format_deal(deal))
        print("=" * 50 + "\n")
        notify(all_deals, config)
    else:
        logger.info("No new deals this cycle.")

    return all_deals


def main():
    parser = argparse.ArgumentParser(
        description="Thrift Deal Notifier — find the best marketplace deals"
    )
    parser.add_argument(
        "--query", "-q", type=str, nargs="+",
        help="Search query (overrides config)"
    )
    parser.add_argument(
        "--max-price", "-p", type=float,
        help="Maximum price (overrides config)"
    )
    parser.add_argument(
        "--interval", "-i", type=int,
        help="Check interval in minutes (overrides config)"
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Run once and exit instead of looping"
    )
    parser.add_argument(
        "--log-file", type=str,
        help="Also write logs to this file (useful for PythonAnywhere/servers)"
    )
    args = parser.parse_args()

    setup_logging(args.log_file)

    config = load_config()

    # Apply CLI overrides
    if args.query:
        config["search_queries"] = args.query
    if args.max_price:
        config["max_price"] = args.max_price
    interval = args.interval or config.get("check_interval_minutes", 15)

    print(r"""
  _____ _        _  __ _     ____             _
 |_   _| |__  _ __(_)/ _| |_  |  _ \  ___  __ _| |
   | | | '_ \| '__| | |_| __| | | | |/ _ \/ _` | |
   | | | | | | |  | |  _| |_  | |_| |  __/ (_| | |
   |_| |_| |_|_|  |_|_|  \__| |____/ \___|\__,_|_|
            N O T I F I E R
    """)
    print(f"  Searching for: {', '.join(config['search_queries'])}")
    print(f"  Max price: ${config['max_price']}")
    print(f"  Platforms: {', '.join(k for k, v in config.get('platforms', {}).items() if v)}")
    print(f"  Check interval: {interval} minutes")
    print()

    if args.once:
        run_search(config)
        return

    # Continuous monitoring loop
    logger.info("Starting continuous monitoring (Ctrl+C to stop)...")
    try:
        while True:
            run_search(config)
            logger.info("Next check in %d minutes...", interval)
            time.sleep(interval * 60)
    except KeyboardInterrupt:
        print("\nStopped. Happy thrifting!")
        sys.exit(0)


if __name__ == "__main__":
    main()
