"""Enhanced weather probability generator for NASA Space Apps with data integration."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict
import meteostat
import numpy as np
import pandas as pd
import scipy

# Add lib directory to path for local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


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
    user_datetime: str


# Receives latitude, longitude and day of interest, returns a dataframe with all available data from nearest weatherstation
def get_meteostat_data(lat: float, lon: float):
    # Find the closest weather station and its date range
    stations = meteostat.Stations()
    stations = stations.nearby(lat, lon)
    stations_data = stations.fetch(limit=1)  # Get only the closest station

    # Get information about the closest station
    closest_station = None
    if not stations_data.empty:
        station_id, station = next(stations_data.iterrows())
        distance_km = (
            station.get("distance", 0) / 1000 if station.get("distance") else 0
        )
        closest_station = {
            "station_id": station_id,
            "name": station.get("name", "Unknown"),
            "distance_km": round(distance_km, 2),
            "start_date": station.get("daily_start").strftime("%Y-%m-%d")
            if station.get("daily_start")
            else None,
            "end_date": station.get("daily_end").strftime("%Y-%m-%d")
            if station.get("daily_end")
            else None,
        }

    if closest_station:
        # Fetch daily data only within the station's valid date range
        location = meteostat.Point(lat, lon)
        start_date = datetime.strptime(closest_station["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(closest_station["end_date"], "%Y-%m-%d")

        # Fetch data within the valid range
        data = meteostat.Daily(location, start_date, end_date)
        daily_data = data.fetch()

    else:
        print("No weather stations found near the specified coordinates.")
        daily_data = None

    return daily_data


def probability_calculator(data) -> [float]:
    probabilities = []

    # thresholds for the model
    hot_threshold = 30
    cold_threshold = 0
    windspeed_threshold = 20
    rainy_threshold = 1

    # Extract temperature data and remove NaN values
    min_temp = data["tmin"].dropna()
    max_temp = data["tmax"].dropna()
    prcp = data["prcp"].dropna()
    windspeed = data["wspd"].dropna()

    # Creating binary values for rainy days
    rainy_days = [1 if rain_amount >= rainy_threshold else 0 for rain_amount in prcp]

    # Computing normal distributions
    max_mu, max_sigma = scipy.stats.norm.fit(max_temp)
    wind_mu, wind_sigma = scipy.stats.norm.fit(windspeed)
    cold_mu, cold_sigma = scipy.stats.norm.fit(min_temp)

    # Computing Probabilities -> Could make these a for loop
    probabilities.append(
        np.around(
            np.clip(
                1 - scipy.stats.norm.cdf(hot_threshold, loc=max_mu, scale=max_sigma),
                0,
                1,
            )
            * 100,
            1,
        )
    )
    probabilities.append(
        np.around(
            np.clip(
                scipy.stats.norm.cdf(cold_threshold, loc=cold_mu, scale=cold_sigma),
                0,
                1,
            )
            * 100,
            1,
        )
    )
    probabilities.append(
        np.around(np.clip(sum(rainy_days) / len(rainy_days), 0, 1) * 100, 1)
    )
    probabilities.append(
        np.around(
            np.clip(
                1
                - scipy.stats.norm.cdf(
                    windspeed_threshold, loc=wind_mu, scale=wind_sigma
                ),
                0,
                1,
            )
            * 100,
            1,
        )
    )
    return probabilities


# Takes latitude, longitude, day of year, and returns various probabilities of interest
def get_weather_probabilities(
    lat: float, lon: float, user_datetime: str
) -> Dict[str, object]:
    query = WeatherQuery(lat=float(lat), lon=float(lon), user_datetime=user_datetime)
    validate_user_datetime(query.user_datetime)

    # Get all historical data for this location
    daily_data = get_meteostat_data(float(lat), float(lon))

    if daily_data is None or daily_data.empty:
        return {
            "meta": {
                "lat": query.lat,
                "lon": query.lon,
                "user_datetime": query.user_datetime,
                "data_source": "meteostat",
                "error": "No data available for this location",
            }
        }

    # Parse the user's target date
    target_date = datetime.strptime(query.user_datetime, "%Y-%m-%d")
    target_month = target_date.month
    target_day = target_date.day

    # Filter data for the same month and day across all years
    matching_dates = daily_data[
        (daily_data.index.month == target_month) & (daily_data.index.day == target_day)
    ]

    too_hot, too_cold, too_rainy, too_windy = probability_calculator(matching_dates)

    # TODO: probabilities to 2 decimal places

    return {
        "meta": {
            "lat": query.lat,
            "lon": query.lon,
            "user_datetime": query.user_datetime,
            "target_month": target_month,
            "target_day": target_day,
            "historical_records_found": len(matching_dates),
            "data_source": "meteostat",
            "hot_prob": too_hot,
            "cold_prob": too_cold,
            "too_rainy": too_rainy,
            "too_windy": too_windy,
        }
    }


# Ensuring user input is valid
def validate_user_datetime(user_datetime: str) -> None:
    try:
        datetime.strptime(user_datetime, "%Y-%m-%d")
    except ValueError:
        raise ValueError("datetime must be in YYYY-MM-DD format")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate weather probabilities")
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--datetime", type=str, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = get_weather_probabilities(args.lat, args.lon, args.datetime)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
