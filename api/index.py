"""
Vercel Serverless Function entry point for RailFlow Flask Application.
Routes incoming HTTP requests to Flask WSGI application.
"""

import sys
import os

# Ensure the root project directory is on sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

# Vercel looks for the WSGI application object 'app'
# This exposes the Flask app to the @vercel/python runtime.
