#!/usr/bin/env python3
"""
Simple web server to test the rozitech.com button routing
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import webbrowser
import threading
import time

class RozitechHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='website_pages', **kwargs)
    
    def do_GET(self):
        # Handle root path
        if self.path == '/':
            self.path = '/index-example.html'
        
        # Serve the files
        return super().do_GET()
    
    def end_headers(self):
        # Add CORS headers for local testing
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def start_server():
    """Start the test server"""
    server_address = ('localhost', 3000)
    httpd = HTTPServer(server_address, RozitechHandler)
    
    print("🌐 Rozitech Website Test Server")
    print("=" * 50)
    print(f"📡 Server running at: http://localhost:3000")
    print()
    print("🔗 Available Routes:")
    print("   / (index)          → Main landing page")
    print("   /get-started.html  → Subscription page")
    print("   /learn-more.html   → Product information")
    print()
    print("🧪 Test Instructions:")
    print("1. Click 'Get Started' button → Should go to pricing page")
    print("2. Click 'Learn More' button → Should go to product info")
    print("3. Navigate between pages using buttons")
    print()
    print("📊 Features to Test:")
    print("   ✅ Button functionality")
    print("   ✅ Page navigation")
    print("   ✅ Responsive design")
    print("   ✅ Contact forms")
    print("   ✅ Signup workflows")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.shutdown()

def open_browser():
    """Open browser after a short delay"""
    time.sleep(1)
    webbrowser.open('http://localhost:3000')

if __name__ == '__main__':
    # Check if website_pages directory exists
    if not os.path.exists('website_pages'):
        print("❌ Error: website_pages directory not found")
        print("Please run this script from the project root directory")
        exit(1)
    
    # Check if required files exist
    required_files = [
        'website_pages/index-example.html',
        'website_pages/get-started.html',
        'website_pages/learn-more.html'
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print("❌ Missing required files:")
        for f in missing_files:
            print(f"   - {f}")
        exit(1)
    
    print("✅ All required files found")
    print("🚀 Starting test server...")
    
    # Start browser in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start the server
    start_server()