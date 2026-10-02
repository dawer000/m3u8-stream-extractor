import asyncio
import json
import re
from playwright.async_api import async_playwright

# Target streaming page
TARGET_URL = "https://webcric.im/frame1.htm"

async def main():
    async with async_playwright() as p:
        print("[+] Launching Browser...")
        
        # System me installed Chrome use hoga taake Playwright Chromium download error na aaye
        try:
            browser = await p.chromium.launch(headless=True, channel="chrome")
        except Exception:
            # Fallback to default Playwright browser
            browser = await p.chromium.launch(headless=True)

        # Mobile Device Emulation Settings
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

        # Network Traffic Listener (Stream Detector Logic)
        def on_request(request):
            url = request.url
            # Detect .m3u8 index or playlist calls
            if ".m3u8" in url and not detected_data["m3u8_url"]:
                detected_data["m3u8_url"] = url
                print("\n==================================================")
                print("[SUCCESS] LIVE M3U8 STREAM DETECTED!")
                print(f"URL: {url}")
                print("==================================================\n")

        # Network Interceptor Event Attach
        page.on("request", on_request)

        print(f"[+] Navigating to {TARGET_URL}...")
        try:
            # Load page & allow scripts to execute
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=25000)
            
            print("[+] Triggering player interactions...")
            await asyncio.sleep(2)

            # Auto-click overlay/play button if media player requires tap to stream
            try:
                await page.mouse.click(195, 422)  # Screen center click
            except Exception:
                pass

            print("[+] Waiting for network streams...")
            
            # Poll for up to 10 seconds until stream request fires
            for i in range(10):
                if detected_data["m3u8_url"]:
                    break
                await asyncio.sleep(1)

        except Exception as e:
            print(f"[-] Navigation/Timeout notice: {e}")

        await browser.close()

        # Output Results
        if detected_data["m3u8_url"]:
            # Save extracted details to a local JSON file
            with open("extracted_stream.json", "w") as f:
                json.dump(detected_data, f, indent=4)
            print("[+] Details saved to 'extracted_stream.json'")
        else:
            print("[-] No active .m3u8 request detected. Channel might be offline or stream dynamically obfuscated.")

if __name__ == "__main__":
    asyncio.run(main())
