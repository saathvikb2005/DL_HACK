"""Test AQI to concentration conversion."""

from app.utils.aqi_converter import convert_pollutants, aqi_to_pm25, aqi_to_co


if __name__ == "__main__":
    print("=" * 70)
    print("TESTING AQI TO CONCENTRATION CONVERSION")
    print("=" * 70)

# Test individual conversions
print("\nIndividual Conversions:")
print(f"PM2.5 AQI 153 → {aqi_to_pm25(153):.2f} µg/m³ (expected ~55-150 µg/m³)")
print(f"PM2.5 AQI 20 → {aqi_to_pm25(20):.2f} µg/m³ (expected ~0-12 µg/m³)")
print(f"PM2.5 AQI 88 → {aqi_to_pm25(88):.2f} µg/m³ (expected ~20-35 µg/m³)")
print(f"CO AQI 3.8 → {aqi_to_co(3.8):.2f} ppm (expected ~0-4.4 ppm)")

# Test full conversion
print("\n" + "=" * 70)
print("Full Pollutant Conversion:")
print("=" * 70)

waqi_data = {
    "pm25": 153,
    "pm10": 58,
    "no2": 2.3,
    "co": 3.8,
    "o3": 11.6,
    "so2": 14.8,
}

print(f"\nWAQI Sub-Indices (input):")
for poll, val in waqi_data.items():
    print(f"  {poll}: {val}")

converted = convert_pollutants(waqi_data)

print(f"\nRaw Concentrations (output):")
for poll, val in converted.items():
    unit = "µg/m³" if poll in ["pm25", "pm10"] else ("ppm" if poll == "co" else "ppb")
    print(f"  {poll}: {val:.2f} {unit}")

print("\n" + "=" * 70)
print("EXPECTED BEHAVIOR:")
print("=" * 70)
print("- PM2.5 AQI 153 should convert to ~55-150 µg/m³ (Unhealthy range)")
print("- PM2.5 AQI 20 should convert to ~4 µg/m³ (Good range)")
print("- PM2.5 AQI 88 should convert to ~25-30 µg/m³ (Moderate range)")
print("=" * 70)