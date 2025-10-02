"""
Debug version of scraper to identify the correct selectors
Run this to see what's actually on the page
"""

import asyncio
from playwright.async_api import async_playwright
import json

async def debug_page_structure():
    """Debug function to understand the page structure"""
    
    url = "https://space.aceparking.com/site/reserve/4fac9ba115140ac4f1c22da82aa0bc7f"
    
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(
            headless=False,  # Set to False to see what's happening
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        try:
            print(f"Navigating to {url}")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for the page to settle
            print("Waiting for page to load completely...")
            await asyncio.sleep(5)
            
            # Take a screenshot
            await page.screenshot(path="debug_screenshot.png")
            print("Screenshot saved as debug_screenshot.png")
            
            # Try to find any elements that might be parking listings
            print("\n=== SEARCHING FOR ELEMENTS ===")
            
            # Check if page has any specific text
            page_text = await page.content()
            
            if "Samuel Merritt" in page_text:
                print("✅ Found 'Samuel Merritt' in page text")
            else:
                print("❌ 'Samuel Merritt' NOT found in page text")
                
            if "sold out" in page_text.lower():
                print("✅ Found 'sold out' indicator")
            
            # Try various selectors
            selectors_to_try = [
                "select",  # Dropdown menus
                "option",  # Dropdown options
                "[name*='permit']",
                "[id*='permit']",
                ".permit-type",
                ".product",
                ".item",
                "button",
                "[data-*='permit']",
                "input[type='radio']",
                "label",
                ".sold-out",
                ".available"
            ]
            
            for selector in selectors_to_try:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"\n✅ Found {len(elements)} elements with selector: {selector}")
                        # Get text from first few elements
                        for i, elem in enumerate(elements[:3]):
                            text = await elem.text_content()
                            if text and text.strip():
                                print(f"   Element {i+1}: {text.strip()[:100]}")
                except:
                    pass
            
            # Look for all text containing "Samuel" or "Merritt"
            print("\n=== SEARCHING FOR TARGET TEXT ===")
            all_text_elements = await page.query_selector_all("*")
            found_count = 0
            
            for elem in all_text_elements:
                try:
                    text = await elem.text_content()
                    if text and ("Samuel" in text or "Merritt" in text or "$67" in text):
                        tag = await elem.evaluate("el => el.tagName")
                        class_name = await elem.evaluate("el => el.className")
                        id_name = await elem.evaluate("el => el.id")
                        
                        if found_count < 5:  # Limit output
                            print(f"\nFound in <{tag}>")
                            if class_name:
                                print(f"  Class: {class_name}")
                            if id_name:
                                print(f"  ID: {id_name}")
                            print(f"  Text: {text.strip()[:200]}")
                            found_count += 1
                except:
                    pass
            
            # Check for iframes
            iframes = await page.query_selector_all("iframe")
            if iframes:
                print(f"\n⚠️ Found {len(iframes)} iframes - content might be in an iframe")
            
            # Check for select dropdowns specifically
            print("\n=== CHECKING FOR DROPDOWNS ===")
            selects = await page.query_selector_all("select")
            if selects:
                print(f"Found {len(selects)} dropdown menus")
                for i, select in enumerate(selects):
                    options = await select.query_selector_all("option")
                    print(f"\nDropdown {i+1} has {len(options)} options:")
                    for j, option in enumerate(options[:5]):  # Show first 5 options
                        text = await option.text_content()
                        value = await option.get_attribute("value")
                        selected = await option.get_attribute("selected")
                        print(f"  Option {j+1}: {text.strip() if text else 'No text'}")
                        if "Samuel" in (text or "") or "Merritt" in (text or ""):
                            print(f"    ⭐ THIS IS OUR TARGET! Value: {value}, Selected: {selected is not None}")
            
            # Save the page HTML for manual inspection
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(page_text)
            print("\nPage HTML saved as debug_page.html")
            
            print("\n=== WAITING FOR YOU TO INSPECT ===")
            print("Browser window is open. Inspect the page manually.")
            print("Press Enter to close the browser...")
            input()
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()

if __name__ == "__main__":
    print("Starting page structure debug...")
    asyncio.run(debug_page_structure())