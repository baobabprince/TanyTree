import os
import sys

# Add the project root to sys.path to allow tests to import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
