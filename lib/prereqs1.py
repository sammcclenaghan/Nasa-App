import os
from pathlib import Path
from getpass import getpass

# Get credentials safely (prefer environment variables)
username = os.getenv("EARTHDATA_USERNAME") or input("Enter your Earthdata username: ")
password = os.getenv("EARTHDATA_PASSWORD") or getpass("Enter your Earthdata password: ")

home = Path.home()

# 1. Create .netrc
netrc_path = home / ".netrc"
netrc_content = f"""machine urs.earthdata.nasa.gov
login {username}
password {password}
"""
netrc_path.write_text(netrc_content)
netrc_path.chmod(0o600)

# 2. Create .dodsrc
dodsrc_path = home / ".dodsrc"
dodsrc_content = f"""HTTP.COOKIEJAR={home}/.urs_cookies
HTTP.NETRC={netrc_path}
"""
dodsrc_path.write_text(dodsrc_content)

print("✅ .netrc and .dodsrc files created successfully.")
print("You can now use Earthdata APIs or netCDF/OPeNDAP tools.")
