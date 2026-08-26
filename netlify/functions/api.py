"""
Netlify Serverless Function Handler for FastAPI via Mangum
"""

import os
import sys

# Add project root to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from mangum import Mangum
from app.main import app

handler = Mangum(app, lifespan="off")
