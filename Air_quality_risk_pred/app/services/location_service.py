"""
Location detection service using IP geolocation.
"""

import httpx
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


async def detect_location_from_ip(client_ip: str = None) -> Optional[Dict[str, Any]]:
    """
    Detect user's location from their IP address using ip-api.com.
    
    Args:
        client_ip: Optional client IP address. If None, server IP is used.
    
    Returns:
        Dict with city, region, country, lat, lon
        None if detection fails
    """
    # Use HTTPS endpoint (requires pro plan) or alternative HTTPS service
    # For production, replace with https://pro.ip-api.com or another HTTPS service
    if client_ip:
        url = f"http://ip-api.com/json/{client_ip}"
    else:
        url = "http://ip-api.com/json/"
    params = {"fields": "status,city,regionName,country,lat,lon"}
    
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        
        if data.get("status") == "success":
            location = {
                "city": data.get("city"),
                "region": data.get("regionName"),
                "country": data.get("country"),
                "latitude": data.get("lat"),
                "longitude": data.get("lon"),
            }
            # Log only country to avoid PII exposure in production logs
            logger.debug(f"Location detected: {location['city']}, {location['region']}, {location['country']}")
            logger.info(f"Location detected: {location['country']}")
            return location
        else:
            logger.warning("IP geolocation failed")
            return None
    
    except Exception as e:
        logger.error(f"Location detection failed: {e}")
        return None
