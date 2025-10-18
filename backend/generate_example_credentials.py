#!/usr/bin/env python
"""
Generate example production credentials for Railway deployment
This creates secure credentials that you can customize
"""

import os
import binascii

def main():
    print("🔐 Production Credentials Generator")
    print("=" * 50)
    
    # Generate secret key
    secret_key = binascii.hexlify(os.urandom(32)).decode()
    
    # Use the existing hash from auth.py (password: secret)
    # You can generate new hashes using the auth system once deployed
    existing_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    
    print("\n📋 RAILWAY ENVIRONMENT VARIABLES:")
    print("=" * 50)
    print(f"SECRET_KEY={secret_key}")
    print(f"ALGORITHM=HS256")
    print(f"ADMIN_USERNAME=admin")
    print(f"ADMIN_PASSWORD_HASH={existing_hash}")
    print(f"ADMIN_EMAIL=admin@yourdomain.com")
    print(f"ADMIN_FULL_NAME=Administrator")
    print(f"USER_USERNAME=user")
    print(f"USER_PASSWORD_HASH={existing_hash}")
    print(f"USER_EMAIL=user@yourdomain.com")
    print(f"USER_FULL_NAME=Regular User")
    print("=" * 50)
    
    print("\n🔑 LOGIN CREDENTIALS:")
    print("Admin: username=admin, password=secret")
    print("User: username=user, password=secret")
    
    print("\n✅ Copy these variables to your Railway environment!")
    print("🔒 Your secret key is now secure and not visible in code!")
    print("\n💡 TIP: After deployment, you can generate new password hashes using the API!")
    print("\n🔄 TO GENERATE NEW PASSWORDS:")
    print("1. Deploy to Railway with these credentials")
    print("2. Use the /token endpoint to login")
    print("3. Generate new password hashes using Python:")
    print("   from passlib.context import CryptContext")
    print("   pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')")
    print("   new_hash = pwd_context.hash('your-new-password')")

if __name__ == "__main__":
    main()