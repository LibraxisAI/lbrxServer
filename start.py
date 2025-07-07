#!/usr/bin/env python3
"""
Simple wrapper to start lbrxserver the old way
This restores the familiar start.py interface
"""

import sys
import os
import subprocess

def main():
    """Start the lbrxserver using the new module structure"""
    print("Starting lbrxserver...")
    
    # Change to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run the server using the new module structure
    cmd = [sys.executable, "-m", "src.main"] + sys.argv[1:]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()