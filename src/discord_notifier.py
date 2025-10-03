async def send_discord_notification(
    webhook_url: Optional[str],
    # ... other parameters
) -> bool:
    
    if not webhook_url:
        logger.warning("No Discord webhook URL provided, skipping notification")
        return False
    
    # ADD THIS DEBUG LINE
    logger.info(f"Attempting to send to webhook: {webhook_url[:50]}...")  # Log first 50 chars
    
    # ... rest of the function
    
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
                    # ADD THIS
                    logger.error(f"Webhook URL used: {webhook_url[:50]}...")
                    logger.error(f"Payload sent: {payload}")
                    return False