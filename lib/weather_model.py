"""Enhanced weather probability generator for NASA Space Apps with MERRA-2 data integration."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

import numpy as np
import pandas as pd
from scipy.special import softmax

# Add lib directory to path for local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from merra2_data_service import MERRA2DataService
    MERRA2_AVAILABLE = True
except ImportError as e:
    print(f"Warning: MERRA-2 service not available: {e}")
    MERRA2_AVAILABLE = False




METRICS = [
    "very hot",
    "very cold",
    "very windy",
    "very wet",
    "very uncomfortable",
]


@dataclass
class WeatherQuery:
    lat: float
    lon: float
    day_of_year: int


def get_weather_probabilities(lat: float, lon: float, day: int) -> Dict[str, object]:
    """Return weather probability data using MERRA-2 data when available, fallback to synthetic data."""
    query = WeatherQuery(lat=float(lat), lon=float(lon), day_of_year=int(day))
    validate_day_of_year(query.day_of_year)

    # Try to use MERRA-2 data if available
    if MERRA2_AVAILABLE:
        try:
            # Convert day of year to approximate date (using current year)
            from datetime import datetime, timedelta
            current_year = datetime.now().year
            target_date = datetime(current_year, 1, 1) + timedelta(days=day - 1)
            
            service = MERRA2DataService()
            result = service.get_weather_probabilities(query.lat, query.lon, target_date)
            
            # Convert probability keys to match expected format
            probabilities = {}
            for key, value in result['probabilities'].items():
                # Map MERRA-2 keys to expected format
                mapped_key = key.replace('_', ' ')
                probabilities[mapped_key] = float(value)
            
            return {
                "meta": {
                    "lat": query.lat,
                    "lon": query.lon,
                    "day_of_year": query.day_of_year,
                    "data_source": result['meta']['data_source'],
                    "date": target_date.strftime('%Y-%m-%d')
                },
                "probabilities": probabilities,
                "raw_merra2_data": result.get('raw_data', {})
            }
            
        except Exception as e:
            print(f"MERRA-2 data access failed, using synthetic data: {e}")
    
    # Fallback to synthetic deterministic data
    seed = int(abs(query.lat * 1000) + abs(query.lon * 1000) + query.day_of_year)
    rng = np.random.default_rng(seed)

    raw_scores = rng.normal(loc=0.0, scale=1.0, size=len(METRICS))
    seasonal_adjustment = seasonal_component(query.day_of_year)
    adjusted_scores = raw_scores + seasonal_adjustment

    probabilities = softmax(adjusted_scores) * 100.0
    rounded = np.round(probabilities, 2)

    series = pd.Series(data=rounded, index=METRICS)

    return {
        "meta": {
            "lat": query.lat,
            "lon": query.lon,
            "day_of_year": query.day_of_year,
            "data_source": "synthetic"
        },
        "probabilities": series.to_dict(),
    }


def seasonal_component(day_of_year: int) -> np.ndarray:
    # Model a simple cyclical seasonal pattern using sine and cosine waves.
    angle = (2 * np.pi * day_of_year) / 365.0
    seasonal = np.array(
        [
            np.sin(angle),
            np.cos(angle),
            np.sin(angle + np.pi / 4),
            np.cos(angle + np.pi / 2),
            np.sin(angle + np.pi),
        ]
    )
    return seasonal


def validate_day_of_year(day: int) -> None:
    if not 1 <= int(day) <= 366:
        raise ValueError("day must be between 1 and 366")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate weather probabilities")
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--day", type=int, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = get_weather_probabilities(args.lat, args.lon, args.day)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
