#!/usr/bin/env python3
"""
Development server runner for Ops Mesh Backend
Usage: python run.py
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """Run the development server with auto-reload."""

    # Check if .env file exists, if not copy from .env.example
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    if not env_file.exists() and env_example.exists():
        print("Creating .env file from .env.example...")
        env_file.write_text(env_example.read_text())
        print("Please edit .env file with your actual configuration values.")

    # Configuration for development
    config = {
        "app": "app.main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": True,
        "reload_dirs": ["app"],
        "log_level": "info",
    }

    print("Starting Ops Mesh Backend Development Server...")
    print(f"Server will be available at: http://localhost:{config['port']}")
    print(f"API Documentation: http://localhost:{config['port']}/docs")
    print(f"Alternative docs: http://localhost:{config['port']}/redoc")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)

    try:
        uvicorn.run(**config)
    except KeyboardInterrupt:
        print("\nShutting down development server...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()