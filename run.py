#!/usr/bin/env python3
"""
Simple launcher script for the AI & Data Science Assessment Platform
"""

import subprocess
import sys
import os

def main():
    """Launch the Streamlit application"""
    try:
        # Check if streamlit is installed
        import streamlit
        print("🚀 Starting AI & Data Science Assessment Platform...")
        print("📱 The app will open in your default browser")
        print("🔐 Default admin credentials: admin / admin123")
        print("=" * 50)
        
        # Run the streamlit app
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
        
    except ImportError:
        print("❌ Streamlit is not installed!")
        print("📦 Please install dependencies first:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting the application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
