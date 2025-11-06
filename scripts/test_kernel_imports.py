#!/usr/bin/env python3
"""Quick test to verify kernel service imports correctly."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    print("Testing kernel service imports...")
    from services.kernel.main import app
    print("✅ Kernel imports successfully")
    print(f"✅ Service title: {app.title}")
    print(f"✅ Service version: {app.version}")
    
    # Check if chat service is included
    routes = [route.path for route in app.routes]
    if "/v1/chat" in routes:
        print("✅ Chat endpoint registered")
    else:
        print("⚠️  Chat endpoint not found in routes")
        
    print("\n✅ All imports successful! Backend is ready to start.")
    sys.exit(0)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
