#!/usr/bin/env python3
"""
Setup script for the AI & Data Science Assessment Platform
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def check_dependencies():
    """Check if all dependencies are installed"""
    required_packages = ["streamlit", "pandas", "plotly", "bcrypt"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        return False
    else:
        print("✅ All dependencies are installed!")
        return True

def main():
    """Main setup function"""
    print("🧠 AI & Data Science Assessment Platform Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("app.py"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("\n📦 Installing missing dependencies...")
        if not install_dependencies():
            print("❌ Failed to install dependencies")
            sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Run the application: python run.py")
    print("2. Or use: streamlit run app.py")
    print("3. Open your browser to the URL shown")
    print("4. Login with admin/admin123")
    
    print("\n🔐 Default admin credentials:")
    print("   Username: admin")
    print("   Password: admin123")

if __name__ == "__main__":
    main()
