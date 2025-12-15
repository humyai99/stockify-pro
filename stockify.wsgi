import sys
import os

# Add project to path
sys.path.insert(0, '/var/www/stockify')

# Activate virtual environment
activate_this = '/var/www/stockify/venv/bin/activate_this.py'
if os.path.exists(activate_this):
    exec(open(activate_this).read(), {'__file__': activate_this})

# Import Flask app
from server import app as application