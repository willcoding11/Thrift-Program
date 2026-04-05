"""
Notification system — sends deal alerts via desktop notifications and/or email.
Auto-detects headless environments (like PythonAnywhere) and skips desktop.
"""

import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def _has_display():
    """Check if a desktop display is available (False on servers/PythonAnywhere)."""
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def notify(deals, config):
    """Send notifications for a list of deals based on config settings."""
    if not deals:
        return

    notif_config = config.get("notifications", {})
    message = _build_message(deals)

    if notif_config.get("desktop", True):
        if _has_display():
            send_desktop(deals)
        else:
            logger.info("No display detected (server/PythonAnywhere) — skipping desktop notifications")
            _print_deals(deals)

    email_cfg = notif_config.get("email", {})
    if email_cfg.get("enabled", False):
        send_email(message, email_cfg)


def send_desktop(deals):
    """Send a desktop notification for each deal (up to 5)."""
    try:
        from plyer import notification as desktop_notif
    except ImportError:
        logger.warning(
            "Desktop notifications require 'plyer'. "
            "Install with: pip install plyer"
        )
        # Fallback: just print to terminal
        _print_deals(deals)
        return

    for deal in deals[:5]:
        price_str = f"${deal['price']:.2f}" if deal.get("price") else "No price"
        try:
            desktop_notif.notify(
                title=f"Deal Found on {deal['source'].title()}!",
                message=f"{deal['title']}\n{price_str}",
                app_name="Thrift Deal Notifier",
                timeout=10,
            )
        except Exception as e:
            logger.warning("Desktop notification failed: %s", e)
            _print_deals([deal])

    if len(deals) > 5:
        try:
            desktop_notif.notify(
                title="More Deals Available",
                message=f"...and {len(deals) - 5} more deals found!",
                app_name="Thrift Deal Notifier",
                timeout=10,
            )
        except Exception:
            pass


def send_email(message, email_cfg):
    """Send a deal alert email via SMTP."""
    sender = email_cfg.get("sender_email", "")
    password = email_cfg.get("sender_password", "")
    recipient = email_cfg.get("recipient_email", "")
    smtp_server = email_cfg.get("smtp_server", "smtp.gmail.com")
    smtp_port = email_cfg.get("smtp_port", 587)

    if not all([sender, password, recipient]):
        logger.warning("Email not configured — skipping email notification.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Thrift Deal Alert - New Deals Found!"
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(message, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        logger.info("Deal alert email sent to %s", recipient)
    except Exception as e:
        logger.error("Failed to send email: %s", e)


def _build_message(deals):
    """Build a plain-text summary of deals."""
    from deal_analyzer import format_deal

    lines = ["=== Thrift Deal Alert ===\n"]
    lines.append(f"Found {len(deals)} deal(s):\n")
    for deal in deals:
        lines.append(format_deal(deal))
    lines.append("Happy thrifting!")
    return "\n".join(lines)


def _print_deals(deals):
    """Fallback: print deals to the terminal."""
    from deal_analyzer import format_deal

    print("\n" + "=" * 50)
    print("  NEW DEALS FOUND!")
    print("=" * 50)
    for deal in deals:
        print(format_deal(deal))
    print("=" * 50 + "\n")
