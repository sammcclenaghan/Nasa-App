# MERRA-2 Data Login Setup Guide

This guide will help you set up authentication for accessing NASA's MERRA-2 (Modern-Era Retrospective analysis for Research and Applications, Version 2) meteorological reanalysis data.

## Prerequisites

1. **NASA Earthdata Login Account**
   - Visit https://urs.earthdata.nasa.gov/users/new
   - Create a free NASA Earthdata Login account
   - Note your username and password - you'll need these

2. **Python Dependencies**
   - The application now includes additional packages for MERRA-2 access:
     - `requests` - HTTP client for API calls
     - `netcdf4` - NetCDF file format support
     - `xarray` - Multi-dimensional array processing
     - `opendap-protocol` - OPeNDAP protocol support
     - `pydap` - Python Data Access Protocol

## Setup Steps

### 1. Install Updated Python Dependencies

```powershell
# Activate your Python virtual environment
.venv\Scripts\activate

# Install updated requirements
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Your `.env` file has been updated with NASA credentials. Update it with your actual NASA Earthdata credentials:

```env
NASA_USERNAME=your_username
NASA_PASSWORD=your_password
EARTHDATA_USERNAME=your_username
EARTHDATA_PASSWORD=your_password
PYTHON_BIN=.venv\Scripts\python.exe
```

### 3. Run Database Migrations

```powershell
# Install bcrypt gem
bundle install

# Run new migrations for user authentication
bin/rails db:migrate
```

### 4. Test MERRA-2 Access

```powershell
# Test the MERRA-2 service directly
$env:EARTHDATA_USERNAME="your_username"
$env:EARTHDATA_PASSWORD="your_password"
.venv\Scripts\python.exe lib\merra2_data_service.py --lat 28.57 --lon -80.65 --date 2024-01-15
```

### 5. Test Updated Weather Model

```powershell
# Test the updated weather model with MERRA-2 integration
$env:PYTHONPATH="lib"
.venv\Scripts\python.exe lib\weather_model.py --lat 28.57 --lon -80.65 --day 42
```

## Features Added

### User Authentication System
- User registration with NASA Earthdata credentials
- Secure credential storage (encrypted passwords)
- Session-based authentication
- User association with weather analysis requests

### MERRA-2 Data Integration
- Real-time access to NASA's MERRA-2 reanalysis data
- Automatic fallback to synthetic data if MERRA-2 is unavailable
- Weather risk calculations based on actual meteorological data
- Support for multiple atmospheric variables:
  - 2-meter air temperature (T2M)
  - 10-meter wind components (U10M, V10M)
  - Total precipitation (PRECTOT)
  - 2-meter specific humidity (QV2M)
  - Surface pressure (PS)

### Enhanced Risk Calculations
- Temperature-based risks (very hot/cold)
- Wind speed risks (very windy)
- Precipitation risks (very wet)
- Comfort index (very uncomfortable)

## Usage

### Web Interface
1. Visit the application homepage
2. Sign up for an account and provide NASA Earthdata credentials
3. Submit weather analysis requests
4. View real-time results powered by MERRA-2 data

### API Access
The weather analysis jobs now automatically use the user's NASA credentials when processing requests, enabling access to real MERRA-2 data instead of synthetic probabilities.

## Troubleshooting

### Common Issues

**MERRA-2 Access Fails**
- Verify NASA Earthdata credentials are correct
- Check internet connectivity
- Ensure .netrc file permissions are correct (600)
- System will automatically fall back to synthetic data

**Python Dependencies**
- Ensure virtual environment is activated
- Some packages require system libraries (netcdf, hdf5)
- On Windows, you may need Visual C++ build tools

**Authentication Issues**
- Clear browser cookies and try again
- Verify .env file has correct credentials
- Check Rails logs for detailed error messages

## Security Notes

- NASA Earthdata passwords are encrypted using Rails' built-in encryption
- .netrc files are created with restricted permissions (600)
- Session cookies are secure and expire automatically
- All authentication happens over HTTPS in production

## Next Steps

With MERRA-2 integration complete, you can:
1. Create analysis workflows for specific regions
2. Add historical data comparison features
3. Implement data caching for improved performance
4. Add more sophisticated weather risk models
5. Export analysis results to various formats

The system now provides a robust foundation for meteorological data analysis using NASA's premier reanalysis dataset.