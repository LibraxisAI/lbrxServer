"""Main entry point for supervisor module."""

import asyncio
import sys
from .supervisor import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Supervisor failed: {e}")
        sys.exit(1)