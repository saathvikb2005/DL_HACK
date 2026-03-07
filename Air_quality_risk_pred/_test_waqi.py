import asyncio
import httpx
import os

async def main():
    # Load token from environment variable
    waqi_token = os.getenv("WAQI_TOKEN")
    if not waqi_token:
        print("ERROR: WAQI_TOKEN environment variable is required")
        print("Set it with: export WAQI_TOKEN=your_token_here")
        return
    
    url = "https://api.waqi.info/feed/Delhi/"
    params = {"token": waqi_token}
    
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(url, params=params)
            r.raise_for_status()
            
            resp = r.json()
            if resp.get("status") != "ok":
                print(f"API Error: {resp.get('data', r.text)}")
                return
            
            d = resp["data"]
        iaqi = d.get("iaqi", {})
        print("WAQI iaqi values:")
        for k, v in iaqi.items():
            print(f"  {k}: {v}")
        print(f"Overall AQI: {d.get('aqi')}")

asyncio.run(main())
