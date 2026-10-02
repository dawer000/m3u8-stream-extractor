import asyncio
import json
import os
from playwright.async_api import async_playwright

TARGET_URL = "https://webcric.im/frame1.htm"

async def main():
    async with async_playwright() as p:
        print("[+] Launching Headless Chromium Browser...")
        
        # Enhanced args to bypass headless/bot detection on Linux runners
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security"
            ]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.75 Mobile Safari/537.36",
            viewport={"width": 390, "height": 844},
            device_scale_factor=3,
            is_mobile=True,
            has_touch=True
        )

        page = await context.new_page()
        
        detected_data = {
            "m3u8_url": None,
            "referer": "https://webcric.im/",
            "user_agent": "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.75 Mobile Safari/537.36"
        }

        # Catch both request and response to ensure no m3u8 call is missed
        def handle_network(url):
            if ".m3u8" in url and not detected_data["m3u8_url"]:
                detected_data["m3u8_url"] = url
                print("\n==================================================")
                print("[SUCCESS] LIVE M3U8 STREAM DETECTED!")
                print(f"URL: {url}")
                print("==================================================\n")

        page.on("request", lambda req: handle_network(req.url))
        page.on("response", lambda res: handle_network(res.url))

        print(f"[+] Navigating to {TARGET_URL}...")
        try:
            await page.goto(TARGET_URL, wait_until="networkidle", timeout=35000)
            print("[+] Page loaded. Triggering user interactions...")
            
            await asyncio.sleep(3)

            # Try clicking center of screen to trigger player JS
            try:
                await page.mouse.click(195, 422)
            except Exception:
                pass

            # Wait up to 15 seconds for m3u8 requests
            for _ in range(15):
                if detected_data["m3u8_url"]:
                    break
                await asyncio.sleep(1)

        except Exception as e:
            print(f"[-] Navigation/Timeout notice: {e}")

        await browser.close()

        # Always create the output JSON file so GitHub Artifacts never fails
        if not detected_data["m3u8_url"]:
            print("[-] No active .m3u8 found. Outputting fallback status.")
            detected_data["status"] = "No m3u8 stream detected or channel offline."

        with open("extracted_stream.json", "w") as f:
            json.dump(detected_data, f, indent=4)
        print("[+] Output written to 'extracted_stream.json'")

if __name__ == "__main__":
    asyncio.run(main())