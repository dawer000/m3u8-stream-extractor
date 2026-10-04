import asyncio
import json
import time
from playwright.async_api import async_playwright

TARGETS = [
    {"id": "frame1", "url": "https://webcric.im/frame1.htm"},
    {"id": "frame2", "url": "https://webcric.im/frame2.htm"}
]

USER_AGENT = "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.75 Mobile Safari/537.36"

async def scrape_channel(browser, target):
    print(f"[{time.strftime('%H:%M:%S')}] Scraping {target['id']}...")
    
    context = await browser.new_context(
        user_agent=USER_AGENT,
        viewport={"width": 390, "height": 844},
        device_scale_factor=3,
        is_mobile=True,
        has_touch=True
    )

    page = await context.new_page()
    extracted_data = {
        "m3u8_url": None,
        "referer": target["url"],
        "user_agent": USER_AGENT,
        "updated_at": time.strftime('%Y-%m-%d %H:%M:%S')
    }

    def on_request(request):
        url = request.url
        if ".m3u8" in url and not extracted_data["m3u8_url"]:
            extracted_data["m3u8_url"] = url

    page.on("request", on_request)

    try:
        await page.goto(target["url"], wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)

        try:
            await page.mouse.click(195, 422)
        except Exception:
            pass

        for _ in range(8):
            if extracted_data["m3u8_url"]:
                break
            await asyncio.sleep(1)

    except Exception as e:
        print(f"[-] Error on {target['id']}: {e}")

    await context.close()
    return target["id"], extracted_data

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True, channel="chrome")
        except Exception:
            browser = await p.chromium.launch(headless=True)

        results = {}
        for target in TARGETS:
            channel_id, data = await scrape_channel(browser, target)
            results[channel_id] = data

        await browser.close()

        with open("streams.json", "w") as f:
            json.dump(results, f, indent=4)
        
        print("[+] 'streams.json' successfully updated!")

if __name__ == "__main__":
    asyncio.run(main())
