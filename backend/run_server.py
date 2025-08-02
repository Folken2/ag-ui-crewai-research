#!/usr/bin/env python3
"""
Launcher script for the CrewAI chatbot server
This script properly sets up the Python path and runs the server
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
backend_dir = Path(__file__).parent
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))

# Now we can import the server
from chatbot.ag_ui_server import app

if __name__ == "__main__":
    import uvicorn
    print("Starting CrewAI Chatbot Server...")
    print("Server will be available at: http://localhost:8000")
    print("Health check: http://localhost:8000/health")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "chatbot.ag_ui_server:app",  # Use import string for reload
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )