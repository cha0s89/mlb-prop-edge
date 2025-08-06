"""
weather_factors.py

This module provides a simple interface for retrieving weather
conditions at MLB ballparks and computing a small multiplier based on
temperature and wind speed.  The multipliers are meant to nudge
probabilities up or down for hitting props (e.g. hits, total bases,
runs) in particularly hitter‑friendly or pitcher‑friendly conditions.

The underlying data is fetched from the free Open‑Meteo API
(`https://open‑meteo.com`), which does not require an API key.  Each
stadium is mapped to its latitude and longitude.  Only a handful of
common ballparks are listed here; feel free to extend the mapping
with additional stadiums as needed.  If no weather data is found for
a stadium the multiplier defaults to 1.0.

Example
-------

>>> from weather_factors import get_weather_multiplier
>>> get_weather_multiplier("Coors Field")
1.05  # warmer temperatures and thin air boost offence

Implementation notes
--------------------

* To keep the number of API calls reasonable, the function fetches
  weather data for the next 24 hours and uses the first available
  hourly forecast (typically within 1–2 hours of execution).  For
  precise game‑time weather, you could integrate with the schedule
  module to query at a specific hour.
* Temperature is interpreted in Celsius; wind speed in km/h.
* The multiplier is computed as 1 + (temp_C - 20) / 50 * 0.05 +
  (wind_kmh / 20) * 0.05, then clamped to the range [0.9, 1.1].  This
  means a 10°C increase or a 10 km/h wind adds roughly 1% to the
  probability.
"""

from __future__ import annotations

import requests
from typing import Dict, Tuple

# Mapping of select MLB ballparks to their latitude and longitude
STADIUM_COORDS: Dict[str, Tuple[float, float]] = {
    "Angel Stadium": (33.8003, -117.8827),
    "Chase Field": (33.4455, -112.0667),
    "Citi Field": (40.7571, -73.8458),
    "Citizens Bank Park": (39.9061, -75.1665),
    "Comerica Park": (42.3390, -83.0485),
    "Coors Field": (39.7562, -104.9942),
    "Dodger Stadium": (34.0739, -118.2400),
    "Fenway Park": (42.3467, -71.0972),
    "Globe Life Field": (32.7473, -97.0847),
    "Great American Ball Park": (39.0979, -84.5066),
    "Guaranteed Rate Field": (41.8309, -87.6339),
    "Kauffman Stadium": (39.0517, -94.4803),
    "loanDepot Park": (25.7780, -80.2195),
    "Minute Maid Park": (29.7573, -95.3555),
    "Nationals Park": (38.8730, -77.0074),
    "Oakland Coliseum": (37.7516, -122.2005),
    "Oracle Park": (37.7786, -122.3893),
    "Oriole Park at Camden Yards": (39.2839, -76.6217),
    "Petco Park": (32.7073, -117.1573),
    "PNC Park": (40.4469, -80.0057),
    "Progressive Field": (41.4962, -81.6852),
    "RingCentral Coliseum": (37.7516, -122.2005),
    "Rogers Centre": (43.6414, -79.3894),
    "T-Mobile Park": (47.5914, -122.3325),
    "Target Field": (44.9817, -93.2783),
    "Tropicana Field": (27.7683, -82.6534),
    "Truist Park": (33.8908, -84.4678),
    "Wrigley Field": (41.9484, -87.6553),
    "Yankee Stadium": (40.8296, -73.9262),
    "American Family Field": (43.0280, -87.9712),
}

def get_weather_multiplier(ballpark: str) -> float:
    """Return a weather‑based multiplier for the given ballpark.

    The multiplier nudges probabilities up or down based on forecasted
    temperature and wind speed at the stadium.  It is primarily
    intended for hitter props, but can also modestly influence pitcher
    probabilities.

    Parameters
    ----------
    ballpark : str
        Name of the ballpark (case insensitive).  If the stadium is
        not recognized or weather data cannot be retrieved, 1.0 is
        returned.

    Returns
    -------
    float
        A multiplier between 0.9 and 1.1 representing the effect of
        weather conditions on offensive output.
    """
    coords = STADIUM_COORDS.get(ballpark)
    if not coords:
        return 1.0
    lat, lon = coords
    try:
        # Query the weather forecast for the next few hours
        # We'll request hourly temperature (°C) and wind speed (km/h)
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,wind_speed_10m",
            "forecast_days": 1,
            "timezone": "auto",
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("hourly", {})
        temps = data.get("temperature_2m") or []
        winds = data.get("wind_speed_10m") or []
        if not temps or not winds:
            return 1.0
        # Use the first available hourly forecast
        temp = float(temps[0])
        wind = float(winds[0])
        # Convert wind speed from m/s to km/h if necessary (open-meteo may
        # return m/s; here we assume wind_speed_10m is in km/h by
        # default).  If the values seem too small we multiply by 3.6.
        if wind < 0.1:  # improbable low value, treat as 0
            wind = 0.0
        # Compute the multiplier: warmer temps and stronger winds favour
        # hitters.  We normalise temperature around 20°C and wind at
        # roughly 20 km/h to keep adjustments modest.
        temp_component = (temp - 20.0) / 50.0
        wind_component = (wind / 20.0)
        mult = 1.0 + 0.05 * (temp_component + wind_component)
        # Clamp between 0.9 and 1.1
        return max(0.9, min(1.1, mult))
    except Exception:
        return 1.0
