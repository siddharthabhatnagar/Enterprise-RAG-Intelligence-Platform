import sys
from pathlib import Path

# Add project root to sys.path for Vercel Serverless environment
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app
