"""
MERRA-2 Data Access Service for NASA Space Apps
Handles authentication and data retrieval from NASA's MERRA-2 reanalysis dataset
"""

import os
import requests
import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MERRA2DataService:
    """Service for accessing MERRA-2 meteorological reanalysis data from NASA"""
    
    BASE_URL = "https://goldsmr4.gesdisc.eosdis.nasa.gov/opendap/MERRA2"
    
    def __init__(self, username: str = None, password: str = None):
        """Initialize MERRA-2 data service with NASA Earthdata credentials"""
        self.username = username or os.getenv("EARTHDATA_USERNAME")
        self.password = password or os.getenv("EARTHDATA_PASSWORD") 
        
        if not self.username or not self.password:
            raise ValueError("NASA Earthdata credentials required. Set EARTHDATA_USERNAME and EARTHDATA_PASSWORD environment variables.")
        
        self.session = self._setup_session()
        
    def _setup_session(self) -> requests.Session:
        """Setup authenticated session for NASA Earthdata"""
        session = requests.Session()
        session.auth = (self.username, self.password)
        
        # Setup .netrc for automatic authentication
        self._setup_netrc()
        
        return session
    
    def _setup_netrc(self):
        """Create .netrc file for automatic authentication with NASA services"""
        netrc_path = Path.home() / ".netrc"
        netrc_content = f"""machine urs.earthdata.nasa.gov
login {self.username}
password {self.password}

machine goldsmr4.gesdisc.eosdis.nasa.gov
login {self.username}
password {self.password}
"""
        netrc_path.write_text(netrc_content)
        netrc_path.chmod(0o600)
        logger.info("✅ .netrc file configured for MERRA-2 access")

    def get_weather_data(self, lat: float, lon: float, date: datetime, 
                        variables: List[str] = None) -> Dict[str, float]:
        """
        Retrieve MERRA-2 weather data for specific location and date
        
        Args:
            lat: Latitude (-90 to 90)
            lon: Longitude (-180 to 180) 
            date: Target date for data retrieval
            variables: List of MERRA-2 variables to retrieve
            
        Returns:
            Dictionary containing weather data values
        """
        if variables is None:
            variables = [
                'T2M',      # 2-meter air temperature
                'U10M',     # 10-meter eastward wind
                'V10M',     # 10-meter northward wind  
                'PRECTOT',  # Total precipitation
                'QV2M',     # 2-meter specific humidity
                'PS',       # Surface pressure
                'DISPH',    # Displacement height
            ]
        
        try:
            # Get the MERRA-2 file URL for the given date
            file_url = self._build_merra2_url(date)
            
            # Open dataset using xarray with authentication
            ds = xr.open_dataset(file_url, engine='netcdf4')
            
            # Find nearest grid point to requested coordinates
            lat_idx = self._find_nearest_index(ds.lat.values, lat)
            lon_idx = self._find_nearest_index(ds.lon.values, lon)
            
            # Extract data for the location
            data = {}
            for var in variables:
                if var in ds.variables:
                    # Get the variable data at the nearest grid point
                    var_data = ds[var].isel(lat=lat_idx, lon=lon_idx)
                    # Take mean over time dimension if present
                    if 'time' in var_data.dims:
                        data[var] = float(var_data.mean().values)
                    else:
                        data[var] = float(var_data.values)
                else:
                    logger.warning(f"Variable {var} not found in dataset")
            
            ds.close()
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving MERRA-2 data: {e}")
            return {}
    
    def _build_merra2_url(self, date: datetime) -> str:
        """Build MERRA-2 OPeNDAP URL for given date"""
        year = date.year
        month = date.month
        day = date.day
        
        # MERRA-2 file naming convention
        date_str = f"{year:04d}{month:02d}{day:02d}"
        
        # Use M2T1NXSLV collection (Single-Level Diagnostics)
        collection = "M2T1NXSLV.5.12.4"
        filename = f"MERRA2_400.tavg1_2d_slv_Nx.{date_str}.nc4"
        
        url = f"{self.BASE_URL}/{collection}/{year:04d}/{month:02d}/{filename}"
        return url
    
    def _find_nearest_index(self, array: np.ndarray, value: float) -> int:
        """Find index of nearest value in array"""
        return int(np.argmin(np.abs(array - value)))
    
    def calculate_weather_risks(self, weather_data: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate weather risk probabilities from MERRA-2 data
        
        Args:
            weather_data: Dictionary of MERRA-2 variables and values
            
        Returns:
            Dictionary of risk probabilities (0-100%)
        """
        risks = {}
        
        if 'T2M' in weather_data:
            temp_k = weather_data['T2M']
            temp_c = temp_k - 273.15  # Convert Kelvin to Celsius
            
            # Temperature-based risks
            risks['very_hot'] = max(0, min(100, (temp_c - 35) * 5))  # Risk increases above 35°C
            risks['very_cold'] = max(0, min(100, (0 - temp_c) * 5))  # Risk increases below 0°C
        
        if 'U10M' in weather_data and 'V10M' in weather_data:
            # Calculate wind speed from U and V components
            wind_speed = np.sqrt(weather_data['U10M']**2 + weather_data['V10M']**2)
            risks['very_windy'] = max(0, min(100, (wind_speed - 10) * 8))  # Risk above 10 m/s
        
        if 'PRECTOT' in weather_data:
            precip = weather_data['PRECTOT'] * 3600  # Convert kg/m2/s to mm/hr
            risks['very_wet'] = max(0, min(100, precip * 20))  # Scale precipitation risk
        
        if 'QV2M' in weather_data and 'T2M' in weather_data:
            # Calculate comfort index based on humidity and temperature
            humidity = weather_data['QV2M']
            temp_c = weather_data['T2M'] - 273.15
            
            # Simple discomfort index
            discomfort = temp_c + (humidity * 1000)  # Rough approximation
            risks['very_uncomfortable'] = max(0, min(100, (discomfort - 25) * 3))
        
        # Ensure all risk categories are present
        for risk_type in ['very_hot', 'very_cold', 'very_windy', 'very_wet', 'very_uncomfortable']:
            if risk_type not in risks:
                risks[risk_type] = 0.0
        
        return risks
    
    def get_weather_probabilities(self, lat: float, lon: float, date: datetime) -> Dict[str, object]:
        """
        Main method to get weather risk probabilities for a location and date
        
        Args:
            lat: Latitude
            lon: Longitude  
            date: Target date
            
        Returns:
            Dictionary with metadata and probability data
        """
        try:
            # Get raw MERRA-2 data
            weather_data = self.get_weather_data(lat, lon, date)
            
            if not weather_data:
                logger.warning("No weather data retrieved, using fallback")
                return self._fallback_probabilities(lat, lon, date)
            
            # Calculate risk probabilities
            probabilities = self.calculate_weather_risks(weather_data)
            
            return {
                "meta": {
                    "lat": lat,
                    "lon": lon,
                    "date": date.isoformat(),
                    "data_source": "MERRA-2",
                    "variables_used": list(weather_data.keys())
                },
                "raw_data": weather_data,
                "probabilities": probabilities
            }
            
        except Exception as e:
            logger.error(f"Error in get_weather_probabilities: {e}")
            return self._fallback_probabilities(lat, lon, date)
    
    def _fallback_probabilities(self, lat: float, lon: float, date: datetime) -> Dict[str, object]:
        """Fallback to dummy data if MERRA-2 access fails"""
        logger.info("Using fallback probability calculation")
        
        # Use day of year for deterministic fallback
        day_of_year = date.timetuple().tm_yday
        
        # Seed RNG for deterministic output
        seed = int(abs(lat * 1000) + abs(lon * 1000) + day_of_year)
        rng = np.random.default_rng(seed)
        
        probabilities = {
            'very_hot': float(rng.uniform(0, 50)),
            'very_cold': float(rng.uniform(0, 50)), 
            'very_windy': float(rng.uniform(0, 40)),
            'very_wet': float(rng.uniform(0, 60)),
            'very_uncomfortable': float(rng.uniform(0, 45))
        }
        
        return {
            "meta": {
                "lat": lat,
                "lon": lon,
                "date": date.isoformat(),
                "data_source": "fallback",
                "note": "MERRA-2 data unavailable, using synthetic data"
            },
            "probabilities": probabilities
        }


def main():
    """Test the MERRA-2 service"""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Test MERRA-2 data access")
    parser.add_argument("--lat", type=float, required=True, help="Latitude")
    parser.add_argument("--lon", type=float, required=True, help="Longitude") 
    parser.add_argument("--date", type=str, help="Date (YYYY-MM-DD)", default=None)
    
    args = parser.parse_args()
    
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d")
    else:
        target_date = datetime.now()
    
    try:
        service = MERRA2DataService()
        result = service.get_weather_probabilities(args.lat, args.lon, target_date)
        
        print("MERRA-2 Analysis Results:")
        print(f"Location: {args.lat}, {args.lon}")
        print(f"Date: {target_date.strftime('%Y-%m-%d')}")
        print(f"Data Source: {result['meta']['data_source']}")
        print("\nRisk Probabilities:")
        for risk, prob in result['probabilities'].items():
            print(f"  {risk}: {prob:.2f}%")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()