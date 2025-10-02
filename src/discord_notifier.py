"""
Discord Webhook Notifier
Sends formatted notifications to Discord channel
"""

import aiohttp
import asyncio
import logging
from typing import Optional, List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

async def send_discord_notification(
    webhook_url: Optional[str],
    title: str,
    description: str,
    color: int = 0x00FF00,
    fields: Optional[List[Dict]] = None,
    url: Optional[str] = None,
    timestamp: Optional[str] = None,
    footer_text: str = "ACE Parking Monitor"
) -> bool:
    """
    Send a rich embed notification to Discord
    
    Args:
        webhook_url: Discord webhook URL
        title: Embed title
        description: Embed description
        color: Embed color (hex)
        fields: List of field dictionaries with name, value, inline
        url: URL to link in the embed
        timestamp: ISO timestamp
        footer_text: Footer text for the embed
    
    Returns:
        True if successful, False otherwise
    """
    
    if not webhook_url:
        logger.warning("No Discord webhook URL provided, skipping notification")
        return False
    
    # Build embed
    embed = {
        "title": title,
        "description": description,
        "color": color,
        "footer": {"text": footer_text}
    }
    
    if url:
        embed["url"] = url
    
    if timestamp:
        embed["timestamp"] = timestamp
    
    if fields:
        embed["fields"] = fields
    
    # Prepare webhook payload
    payload = {
        "embeds": [embed],
        "username": "Parking Monitor Bot",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/3774/3774278.png"  # Car icon
    }
    
    # Send webhook
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status == 204:
                    logger.info("Discord notification sent successfully")
                    return True
                else:
                    logger.error(f"Failed to send Discord notification: {response.status}")
                    text = await response.text()
                    logger.error(f"Response: {text}")
                    return False
    except Exception as e:
        logger.error(f"Error sending Discord notification: {e}")
        return False

async def send_test_notification(webhook_url: str):
    """Send a test notification to verify webhook is working"""
    return await send_discord_notification(
        webhook_url=webhook_url,
        title="🧪 Test Notification",
        description="Parking monitor is set up and working!",
        color=0x0099FF,
        fields=[
            {"name": "Status", "value": "✅ Connected", "inline": True},
            {"name": "Time", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": True}
        ],
        timestamp=datetime.now().isoformat()
    )

if __name__ == "__main__":
    # Test the notifier
    import os
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    if webhook_url:
        asyncio.run(send_test_notification(webhook_url))
    else:
        print("Please set DISCORD_WEBHOOK_URL environment variable")