"""
Fixed ACE Parking Availability Scraper
Updated to work with the actual page structure
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import sys
import os
import re
from dotenv import load_dotenv  # ← ADD THIS LINE

# Load environment variables from .env file
load_dotenv()  # ← ADD THIS LINE

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.discord_notifier import send_discord_notification
from src.state_manager import StateManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ParkingMonitor:
    """Monitor parking availability on ACE Parking website"""
    
    def __init__(self, url: str, target_name: str = "Samuel Merritt University Fall 2025 Parking"):
        self.url = url
        self.target_name = target_name
        self.state_manager = StateManager()
        self.discord_webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
        
    async def scrape_parking_status(self) -> Tuple[bool, Optional[Dict]]:
        """
        Scrape the parking page and extract availability status
        Returns: (success, parking_data)
        """
        async with async_playwright() as p:
            browser = None
            try:
                # Launch browser with realistic settings
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                
                # Navigate to page
                logger.info(f"Navigating to {self.url}")
                await page.goto(self.url, wait_until='networkidle', timeout=30000)
                
                # Handle cookie consent if present
                try:
                    # Try to click "Use necessary cookies only" or "Allow all cookies"
                    cookie_button = await page.wait_for_selector(
                        'button:has-text("Use necessary cookies only"), button:has-text("Allow all cookies")', 
                        timeout=3000
                    )
                    if cookie_button:
                        await cookie_button.click()
                        logger.info("Handled cookie consent")
                        await asyncio.sleep(1)
                except:
                    # Cookie banner might not appear or already accepted
                    pass
                
                # Wait for content to load
                await page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(3)  # Additional wait for dynamic content
                
                # Extract parking data using the simple structure we found
                parking_data = await self._extract_parking_data(page)
                
                if parking_data:
                    logger.info(f"Successfully scraped data: {parking_data}")
                    return True, parking_data
                else:
                    logger.warning("Could not find target parking listing")
                    return False, None
                    
            except PlaywrightTimeout as e:
                logger.error(f"Timeout error while scraping: {e}")
                return False, None
            except Exception as e:
                logger.error(f"Unexpected error while scraping: {e}")
                return False, None
            finally:
                if browser:
                    await browser.close()
    
    async def _extract_parking_data(self, page) -> Optional[Dict]:
        """
        Extract parking data from the page using the actual structure
        """
        try:
            # Get the page content
            page_content = await page.content()
            
            # Check if our target parking is on the page
            if "Samuel Merritt University Fall 2025 Parking" not in page_content:
                logger.warning("Target parking not found on page")
                return None
            
            # Method 1: Look for the text directly
            parking_element = None
            
            # Try to find the element containing our parking name
            try:
                # Look for element with the exact text
                parking_element = await page.locator('text="Samuel Merritt University Fall 2025 Parking"').first
                
                if parking_element:
                    # Get the parent container that likely has all info
                    parent = parking_element
                    
                    # Try to go up to find the container with price and status
                    for _ in range(5):  # Go up max 5 levels
                        parent_element = await parent.locator('..').first
                        parent_text = await parent_element.inner_text()
                        
                        # Check if this parent has both price and status info
                        if "$67.45" in parent_text or "Sold Out" in parent_text or "sold out" in parent_text.lower():
                            parent = parent_element
                            break
                        parent = parent_element
                    
                    # Get the full text of the container
                    container_text = await parent.inner_text()
                    logger.info(f"Found container text: {container_text[:200]}")
                    
                    # Extract information
                    parking_info = self._parse_parking_info(container_text)
                    
                    if parking_info:
                        return parking_info
                        
            except Exception as e:
                logger.debug(f"Method 1 failed: {e}")
            
            # Method 2: Search in page text with regex
            # Clean the HTML to get text
            clean_text = re.sub(r'<[^>]+>', ' ', page_content)
            clean_text = re.sub(r'\s+', ' ', clean_text)
            
            # Look for our parking in the text
            pattern = r'Samuel Merritt University Fall 2025 Parking.*?\$67\.45.*?(Sold Out|Available|Add to Cart)'
            match = re.search(pattern, clean_text, re.IGNORECASE | re.DOTALL)
            
            if match:
                matched_text = match.group(0)
                logger.info(f"Found via regex: {matched_text}")
                
                # Determine status
                if "sold out" in matched_text.lower():
                    status = "sold_out"
                elif "available" in matched_text.lower() or "add to cart" in matched_text.lower():
                    status = "available"
                else:
                    status = "unknown"
                
                return {
                    'name': self.target_name,
                    'status': status,
                    'price': '$67.45',
                    'url': self.url,
                    'timestamp': datetime.now().isoformat(),
                    'has_button': status == "available"
                }
            
            # Method 3: Just check if "Sold Out" appears near our text
            if "Samuel Merritt University Fall 2025 Parking" in page_content:
                # Find the position of our text
                pos = page_content.find("Samuel Merritt University Fall 2025 Parking")
                # Check nearby text (within 500 characters)
                nearby_text = page_content[pos:pos+500].lower()
                
                if "sold out" in nearby_text:
                    status = "sold_out"
                elif "available" in nearby_text or "add to cart" in nearby_text:
                    status = "available"
                else:
                    # Default to sold_out if we can't determine
                    status = "sold_out"
                
                logger.info(f"Found parking with status: {status}")
                
                return {
                    'name': self.target_name,
                    'status': status,
                    'price': '$67.45',
                    'url': self.url,
                    'timestamp': datetime.now().isoformat(),
                    'has_button': status == "available"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting parking data: {e}")
            return None
    
    def _parse_parking_info(self, text: str) -> Optional[Dict]:
        """
        Parse parking information from text
        """
        try:
            # Check status
            if "sold out" in text.lower():
                status = "sold_out"
            elif "available" in text.lower() or "add to cart" in text.lower():
                status = "available"
            else:
                status = "unknown"
            
            # Extract price
            price_match = re.search(r'\$[\d,]+\.?\d*', text)
            price = price_match.group(0) if price_match else "$67.45"
            
            return {
                'name': self.target_name,
                'status': status,
                'price': price,
                'url': self.url,
                'timestamp': datetime.now().isoformat(),
                'has_button': status == "available"
            }
        except Exception as e:
            logger.error(f"Error parsing parking info: {e}")
            return None
    
    async def check_and_notify(self):
        """
        Main function to check parking status and send notifications if changed
        """
        logger.info(f"Starting parking monitor check at {datetime.now()}")
        
        # Get current status
        success, current_data = await self.scrape_parking_status()
        
        if not success or not current_data:
            logger.error("Failed to scrape parking status")
            # Send error notification if this persists
            error_count = self.state_manager.increment_error_count()
            if error_count >= 3:  # Alert after 3 consecutive failures
                await send_discord_notification(
                    webhook_url=self.discord_webhook_url,
                    title="⚠️ Monitoring Error",
                    description="Failed to check parking status",
                    color=0xFF0000,
                    fields=[
                        {"name": "Error Count", "value": str(error_count), "inline": True},
                        {"name": "Target", "value": self.target_name, "inline": False}
                    ]
                )
            return
        
        # Reset error count on successful scrape
        self.state_manager.reset_error_count()
        
        # Get previous state
        previous_state = self.state_manager.get_state()
        
        # Check if status changed from sold_out to available
        status_changed = False
        if previous_state:
            prev_status = previous_state.get('status')
            curr_status = current_data['status']
            
            logger.info(f"Previous status: {prev_status}, Current status: {curr_status}")
            
            if prev_status == 'sold_out' != curr_status:
                status_changed = True
                logger.info("🎉 PARKING IS NOW AVAILABLE!")
        else:
            # First run
            logger.info("First run - initializing state")
        
        # Update state
        self.state_manager.save_state(current_data)
        
        # Send notification if status changed to available
        if status_changed:
            await send_discord_notification(
                webhook_url=self.discord_webhook_url,
                title="🚗 PARKING AVAILABLE!",
                description=current_data['name'],
                color=0x00FF00,
                fields=[
                    {"name": "Price", "value": current_data.get('price', 'N/A'), "inline": True},
                    {"name": "Status", "value": "✅ AVAILABLE", "inline": True},
                    {"name": "Previous Status", "value": "❌ Sold Out", "inline": True},
                ],
                url=self.url,
                timestamp=current_data['timestamp']
            )
            logger.info("Discord notification sent successfully!")
        else:
            logger.info(f"No status change. Current status: {current_data['status']}")

async def main():
    """Main entry point"""
    # Check for Discord webhook URL
    if not os.environ.get('DISCORD_WEBHOOK_URL'):
        logger.warning("DISCORD_WEBHOOK_URL not set. Running in test mode.")
    
    # Initialize monitor
    monitor = ParkingMonitor(
        url="https://space.aceparking.com/site/reserve/4fac9ba115140ac4f1c22da82aa0bc7f",
        target_name="Samuel Merritt University Fall 2025 Parking"
    )
    
    # Run check
    await monitor.check_and_notify()
    
    logger.info("Check completed successfully")

if __name__ == "__main__":
    asyncio.run(main())