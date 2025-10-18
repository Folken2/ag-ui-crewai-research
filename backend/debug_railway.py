#!/usr/bin/env python3
"""
Railway Backend Debug Script
Run this to test if your Railway backend is working correctly
Usage: python debug_railway.py <backend_url>
"""

import requests
import json
import os
import sys

def test_backend(backend_url):
    if not backend_url:
        print("❌ No backend URL provided")
        return
    
    print(f"🔍 Testing backend at: {backend_url}")
    
    # Test 1: Health check
    print("\n1️⃣ Testing health endpoint...")
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    # Test 2: Root endpoint
    print("\n2️⃣ Testing root endpoint...")
    try:
        response = requests.get(f"{backend_url}/", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:100]}...")
    except Exception as e:
        print(f"   ❌ Root endpoint error: {e}")
    
    # Test 3: Token endpoint
    print("\n3️⃣ Testing token endpoint...")
    try:
        response = requests.post(
            f"{backend_url}/token",
            data={"username": "admin", "password": "secret"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            token_data = response.json()
            print("   ✅ Token generation successful")
            token = token_data.get("access_token")
            if token:
                print(f"   Token: {token[:20]}...")
                return token
        else:
            print(f"   ❌ Token generation failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Token endpoint error: {e}")
    
    return None

def test_agent_endpoint(backend_url, token):
    if not token:
        print("\n❌ No token available, skipping agent test")
        return
    
    print("\n4️⃣ Testing agent endpoint...")
    try:
        response = requests.post(
            f"{backend_url}/agent",
            json={"messages": [{"content": "Hello, test message"}]},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Agent endpoint working")
        else:
            print(f"   ❌ Agent endpoint failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Agent endpoint error: {e}")

if __name__ == "__main__":
    print("🚀 Railway Backend Debug Tool")
    print("=" * 50)
    
    if len(sys.argv) != 2:
        print("Usage: python debug_railway.py <backend_url>")
        print("Example: python debug_railway.py https://ag-ui-crewai-research.railway.app")
        exit(1)
    
    backend_url = sys.argv[1].strip()
    if not backend_url:
        print("❌ No backend URL provided")
        exit(1)
    
    token = test_backend(backend_url)
    test_agent_endpoint(backend_url, token)
    
    print("\n" + "=" * 50)
    print("🔧 Troubleshooting Tips:")
    print("1. Check Railway logs for errors")
    print("2. Verify all environment variables are set")
    print("3. Ensure OPENROUTER_API_KEY is valid")
    print("4. Check if EXA_API_KEY and SERPER_API_KEY are set")
    print("5. Verify SECRET_KEY is set for JWT")
