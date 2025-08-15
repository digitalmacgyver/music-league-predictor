#!/usr/bin/env ./venv/bin/python3
"""
Music League Data Collection - Main Runner
Coordinates authentication and scraping
"""

import subprocess
import sys
from pathlib import Path
from config import SESSION_PATH

def check_session():
    """Check if we have a valid session file"""
    return SESSION_PATH.exists()

def run_command(command):
    """Run a shell command and return success status"""
    try:
        result = subprocess.run(command, shell=True, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

def main():
    print("="*70)
    print("MUSIC LEAGUE DATA COLLECTION")
    print("="*70)
    
    # Check if session exists
    if not check_session():
        print("No authentication session found.")
        print("Running login script first...")
        print("\n")
        
        # Run login script
        if not run_command("./login.py"):
            print("Login failed. Please check the error messages above.")
            sys.exit(1)
        
        # Verify session was created
        if not check_session():
            print("Login completed but no session file was created.")
            print("Please try running ./login.py manually.")
            sys.exit(1)
    else:
        print("Found existing session file.")
    
    print("\nRunning scraper...")
    print("="*70)
    
    # Run scraper
    if not run_command("./scraper.py"):
        print("\nScraping failed. The session may have expired.")
        print("Try running ./login.py to re-authenticate.")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("DATA COLLECTION COMPLETE!")
    print("="*70)
    print("Run ./reports.py to view your Music League data")

if __name__ == "__main__":
    main()