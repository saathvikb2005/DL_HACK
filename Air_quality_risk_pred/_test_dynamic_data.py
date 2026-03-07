"""Test script to verify dynamic data from APIs."""

import asyncio
from app.services.waqi_service import fetch_aqi_by_city
from app.services.weather_service import fetch_weather


async def test_dynamic_inputs():
    """Verify that different cities return different data."""
    
    cities = ["Mumbai", "London", "Tokyo", "Los Angeles"]
    
    print("=" * 70)
    print("TESTING DYNAMIC API DATA FETCHING")
    print("=" * 70)
    
    for city in cities:
        print(f"\n{'='*70}")
        print(f"City: {city}")
        print(f"{'='*70}")
        
        # Fetch WAQI data with error handling
        try:
            waqi = await fetch_aqi_by_city(city)
        except Exception as e:
            print(f"✗ WAQI Data FAILED: {e}")
            waqi = None
        
        if waqi:
            print(f"✓ WAQI Data Retrieved:")
            print(f"  Current AQI: {waqi.get('aqi')}")
            print(f"  City Name: {waqi.get('city_name')}")
            print(f"  Coordinates: ({waqi.get('latitude')}, {waqi.get('longitude')})")
            
            pollutants = waqi.get("pollutants", {})
            print(f"  Pollutants:")
            print(f"    PM2.5: {pollutants.get('pm25')}")
            print(f"    PM10: {pollutants.get('pm10')}")
            print(f"    NO2: {pollutants.get('no2')}")
            print(f"    O3: {pollutants.get('o3')}")
            print(f"    SO2: {pollutants.get('so2')}")
            print(f"    CO: {pollutants.get('co')}")
        else:
            print(f"✗ WAQI Data FAILED")
        
        # Fetch weather data with error handling
        try:
            weather = await fetch_weather(city)
        except Exception as e:
            print(f"✗ Weather Data FAILED: {e}")
            weather = None
        
        if weather:
            print(f"✓ Weather Data Retrieved:")
            print(f"  Temperature: {weather.get('temperature')}°C")
            print(f"  Humidity: {weather.get('humidity')}%")
            print(f"  Wind Speed: {weather.get('wind_speed')} km/h")
            print(f"  Pressure: {weather.get('pressure')} hPa")
            print(f"  Precipitation: {weather.get('precipitation')} mm")
        else:
            print(f"✗ Weather Data FAILED")
    
    print("\n" + "=" * 70)
    print("CONCLUSION:")
    print("If all values above are DIFFERENT for each city,")
    print("then the API data fetching is DYNAMIC (not hardcoded).")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_dynamic_inputs())
