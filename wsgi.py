"""
Production WSGI server configuration for SAT Report Generator
"""
import os
import sys
from waitress import serve
from app import create_app

# Create the Flask application
app = create_app('production')

def run_production_server():
    """Run the application with Waitress production server"""
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    
    print(f"Starting SAT Report Generator on {host}:{port}")
    print("Using Waitress production server for better performance")
    
    # Configure Waitress with optimized settings
    serve(
        app,
        host=host,
        port=port,
        threads=4,  # Number of worker threads
        connection_limit=100,  # Maximum connections
        cleanup_interval=30,  # Cleanup idle connections every 30 seconds
        channel_timeout=120,  # Timeout for idle connections
        ident='SAT-Report-Generator',  # Server identification
        asyncore_use_poll=True,  # Use poll() instead of select() for better performance
    )

if __name__ == '__main__':
    # Run production server
    run_production_server()