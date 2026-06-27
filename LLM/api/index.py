import os
import sys

# Add the football_league folder to the system path so config/database/routes can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "football_league"))

from app import app
