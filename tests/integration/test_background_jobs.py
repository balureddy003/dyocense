#!/usr/bin/env python3
"""
Quick test to verify the accounts service starts and background jobs initialize.
"""

import sys
import time
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_service_health():
    """Test that the service starts and reports healthy."""
    print("Testing accounts service health...")
    
    try:
        response = requests.get("http://127.0.0.1:8001/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Service healthy: {data}")
            
            # Check background jobs
            if "background_jobs" in data:
                jobs = data["background_jobs"]
                if "trial_enforcement" in jobs:
                    job_status = jobs["trial_enforcement"]
                    print(f"✅ Trial enforcement job: running={job_status.get('running')}, interval={job_status.get('interval')}")
                    return True
            print("⚠️  Background jobs not reported in health check")
            return False
        else:
            print(f"❌ Service returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to service at http://127.0.0.1:8001")
        print("   Make sure the service is running:")
        print("   uvicorn services.accounts.main:app --reload --port 8001")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_service_health()
    sys.exit(0 if success else 1)
