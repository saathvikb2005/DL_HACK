"""
AQI to Concentration Converter

Converts AQI sub-indices (0-500 scale) back to raw pollutant concentrations
using EPA formulas (EPA 454/B-18-007).
"""

from typing import Optional


# EPA AQI Breakpoints for PM2.5 (µg/m³)
PM25_BREAKPOINTS = [
    (0, 50, 0.0, 12.0),      # Good
    (51, 100, 12.1, 35.4),   # Moderate
    (101, 150, 35.5, 55.4),  # USG
    (151, 200, 55.5, 150.4), # Unhealthy
    (201, 300, 150.5, 250.4),# Very Unhealthy
    (301, 500, 250.5, 500.4),# Hazardous
]

# EPA AQI Breakpoints for PM10 (µg/m³)
PM10_BREAKPOINTS = [
    (0, 50, 0, 54),
    (51, 100, 55, 154),
    (101, 150, 155, 254),
    (151, 200, 255, 354),
    (201, 300, 355, 424),
    (301, 500, 425, 604),
]

# EPA AQI Breakpoints for NO2 (ppb)
NO2_BREAKPOINTS = [
    (0, 50, 0, 53),
    (51, 100, 54, 100),
    (101, 150, 101, 360),
    (151, 200, 361, 649),
    (201, 300, 650, 1249),
    (301, 500, 1250, 2049),
]

# EPA AQI Breakpoints for O3 (ppb, 8-hour)
O3_BREAKPOINTS = [
    (0, 50, 0, 54),
    (51, 100, 55, 70),
    (101, 150, 71, 85),
    (151, 200, 86, 105),
    (201, 300, 106, 200),
]

# EPA AQI Breakpoints for SO2 (ppb, 1-hour)
SO2_BREAKPOINTS = [
    (0, 50, 0, 35),
    (51, 100, 36, 75),
    (101, 150, 76, 185),
    (151, 200, 186, 304),
    (201, 300, 305, 604),
    (301, 500, 605, 1004),
]

# EPA AQI Breakpoints for CO (ppm, 8-hour)
CO_BREAKPOINTS = [
    (0, 50, 0.0, 4.4),
    (51, 100, 4.5, 9.4),
    (101, 150, 9.5, 12.4),
    (151, 200, 12.5, 15.4),
    (201, 300, 15.5, 30.4),
    (301, 500, 30.5, 50.4),
]


def _convert_aqi_to_concentration(aqi: float, breakpoints: list) -> float:
    """
    Convert AQI sub-index to raw concentration.
    
    Formula: C = [(I - I_low) * (C_high - C_low) / (I_high - I_low)] + C_low
    
    Args:
        aqi: AQI sub-index value (0-500)
        breakpoints: List of (I_low, I_high, C_low, C_high) tuples
        
    Returns:
        Raw concentration value
    """
    if aqi <= 0:
        return 0.0
    
    # Find the correct breakpoint range (use half-open intervals except for last)
    for idx, (i_low, i_high, c_low, c_high) in enumerate(breakpoints):
        # Use half-open interval for all but the final breakpoint
        is_last = (idx == len(breakpoints) - 1)
        if is_last:
            if i_low <= aqi <= i_high:
                # Apply EPA inverse formula
                concentration = ((aqi - i_low) * (c_high - c_low) / (i_high - i_low)) + c_low
                return round(concentration, 2)
        else:
            if i_low <= aqi < i_high:
                # Apply EPA inverse formula
                concentration = ((aqi - i_low) * (c_high - c_low) / (i_high - i_low)) + c_low
                return round(concentration, 2)
    
    # If AQI > 500, extrapolate from last breakpoint
    i_low, i_high, c_low, c_high = breakpoints[-1]
    concentration = ((aqi - i_low) * (c_high - c_low) / (i_high - i_low)) + c_low
    return round(concentration, 2)


def aqi_to_pm25(aqi: Optional[float]) -> float:
    """Convert PM2.5 AQI sub-index to µg/m³."""
    if aqi is None or aqi <= 0:
        return 0.0
    return _convert_aqi_to_concentration(aqi, PM25_BREAKPOINTS)


def aqi_to_pm10(aqi: Optional[float]) -> float:
    """Convert PM10 AQI sub-index to µg/m³."""
    if aqi is None or aqi <= 0:
        return 0.0
    return _convert_aqi_to_concentration(aqi, PM10_BREAKPOINTS)


def aqi_to_no2(aqi: Optional[float]) -> float:
    """Convert NO2 AQI sub-index to ppb."""
    if aqi is None or aqi <= 0:
        return 0.0
    return _convert_aqi_to_concentration(aqi, NO2_BREAKPOINTS)


def aqi_to_o3(aqi: Optional[float]) -> float:
    """Convert O3 AQI sub-index to ppb."""
    if aqi is None or aqi <= 0:
        return 0.0
    return _convert_aqi_to_concentration(aqi, O3_BREAKPOINTS)


def aqi_to_so2(aqi: Optional[float]) -> float:
    """Convert SO2 AQI sub-index to ppb."""
    if aqi is None or aqi <= 0:
        return 0.0
    return _convert_aqi_to_concentration(aqi, SO2_BREAKPOINTS)


def aqi_to_co(aqi: Optional[float]) -> float:
    """Convert CO AQI sub-index to mg/m³ (not ppm)."""
    if aqi is None or aqi <= 0:
        return 0.0
    # First get ppm
    ppm = _convert_aqi_to_concentration(aqi, CO_BREAKPOINTS)
    # Convert ppm to mg/m³ (1 ppm CO = 1.145 mg/m³ at 25°C)
    mg_m3 = ppm * 1.145
    return round(mg_m3, 2)


def convert_pollutants(waqi_pollutants: dict) -> dict:
    """
    Convert all WAQI pollutant sub-indices to raw concentrations.
    
    Args:
        waqi_pollutants: Dict with keys like 'pm25', 'pm10', etc. containing AQI sub-indices
        
    Returns:
        Dict with same keys but converted to raw concentrations:
        - pm25, pm10: µg/m³
        - no2, o3, so2: ppb
        - co: mg/m³
    """
    return {
        "pm25": aqi_to_pm25(waqi_pollutants.get("pm25")),  # µg/m³
        "pm10": aqi_to_pm10(waqi_pollutants.get("pm10")),  # µg/m³
        "no2": aqi_to_no2(waqi_pollutants.get("no2")),     # ppb
        "o3": aqi_to_o3(waqi_pollutants.get("o3")),        # ppb
        "so2": aqi_to_so2(waqi_pollutants.get("so2")),     # ppb
        "co": aqi_to_co(waqi_pollutants.get("co")),        # mg/m³
    }
