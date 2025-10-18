#!/usr/bin/env python
"""
Generate a secure secret key for JWT authentication
Run this script to generate a new secret key for your .env file
"""

import os
import binascii

def generate_secret_key():
    """Generate a secure random secret key"""
    return binascii.hexlify(os.urandom(32)).decode()

if __name__ == "__main__":
    secret_key = generate_secret_key()
    print("Generated Secret Key:")
    print(f"SECRET_KEY={secret_key}")
    print("\nAdd this to your .env file!")
    print("Make sure to keep this secret and never commit it to version control.")
