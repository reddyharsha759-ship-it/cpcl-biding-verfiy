"""
Vercel Serverless Entrypoint for FastAPI
"""

import os
import sys

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

# Vercel looks for the ASGI application callable 'app'
