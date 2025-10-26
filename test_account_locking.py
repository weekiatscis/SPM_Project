#!/usr/bin/env python3
"""
Test script to demonstrate account locking mechanism
This script shows what happens when a user fails login attempts multiple times
"""

import requests
import time
from datetime import datetime

API_BASE_URL = "http://localhost:8086"

def print_separator(title):
    """Print a nice separator for sections"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def attempt_login(email, password, attempt_number=None):
    """Attempt to login and print the result"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=5
        )

        data = response.json()

        if attempt_number:
            print(f"\nAttempt #{attempt_number}:")

        print(f"  Status Code: {response.status_code}")

        if response.status_code == 200:
            print(f"  ✅ Login successful!")
            print(f"  User: {data.get('user', {}).get('name')}")
            return True
        elif response.status_code == 401:
            print(f"  ❌ Login failed: {data.get('error')}")
            return False
        elif response.status_code == 423:
            print(f"  🔒 ACCOUNT LOCKED: {data.get('error')}")
            return False
        else:
            print(f"  Error: {data.get('error')}")
            return False

    except Exception as e:
        print(f"  Error: {e}")
        return False

def check_user_status(email):
    """Check user's security status in database"""
    try:
        from dotenv import load_dotenv
        import os
        from supabase import create_client

        load_dotenv()

        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            print("  ⚠️  Cannot check database - Supabase credentials not found")
            return

        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

        # Get user data
        response = supabase.table("user").select(
            "email, name, failed_attempts, is_locked, locked_until, last_login"
        ).eq("email", email.lower().strip()).execute()

        if response.data:
            user = response.data[0]
            print(f"\n  📊 User Status in Database:")
            print(f"     Email: {user.get('email')}")
            print(f"     Name: {user.get('name')}")
            print(f"     Failed Attempts: {user.get('failed_attempts', 0)}")
            print(f"     Is Locked: {user.get('is_locked', False)}")
            if user.get('locked_until'):
                print(f"     Locked Until: {user.get('locked_until')}")

                # Calculate remaining lock time
                from datetime import datetime, timezone
                locked_until = datetime.fromisoformat(user['locked_until'].replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                remaining = (locked_until - now).total_seconds()

                if remaining > 0:
                    minutes = int(remaining // 60)
                    seconds = int(remaining % 60)
                    print(f"     Time Remaining: {minutes}m {seconds}s")
                else:
                    print(f"     Time Remaining: Lock expired (will auto-unlock on next attempt)")

            if user.get('last_login'):
                print(f"     Last Login: {user.get('last_login')}")
        else:
            print(f"  ⚠️  User not found: {email}")

    except Exception as e:
        print(f"  ⚠️  Error checking database: {e}")

def main():
    """Main test function"""
    print_separator("ACCOUNT LOCKING MECHANISM TEST")
    print("\nThis test demonstrates what happens when a user fails login multiple times.")
    print("The account will be locked after 5 failed attempts for 15 minutes.")

    # Test with a real user (you can change this to any email in your system)
    test_email = input("\n📧 Enter email to test (e.g., amandaxhia@gmail.com): ").strip()

    if not test_email:
        print("No email provided. Exiting.")
        return

    wrong_password = "WrongPassword123!"

    # Check initial status
    print_separator("Initial User Status")
    check_user_status(test_email)

    # Simulate 5 failed login attempts
    print_separator("Simulating Failed Login Attempts")
    print("\nAttempting to login with wrong password 5 times...")

    for i in range(1, 6):
        time.sleep(0.5)  # Small delay between attempts
        attempt_login(test_email, wrong_password, i)

        # Check status after each attempt
        if i == 5:
            print("\n  ⚠️  This should trigger the account lock!")

    # Check status after 5 attempts
    print_separator("User Status After 5 Failed Attempts")
    check_user_status(test_email)

    # Try logging in with correct password while locked
    print_separator("Attempting Login While Locked")
    print("\nTrying to login with the CORRECT password while account is locked...")
    print("(Note: Even correct password should fail due to lock)")

    correct_password = input("\n🔑 Enter the CORRECT password for this account: ").strip()

    if correct_password:
        attempt_login(test_email, correct_password)
        check_user_status(test_email)
    else:
        print("No password provided. Skipping correct password test.")

    # Information about unlocking
    print_separator("How to Unlock the Account")
    print("\n📋 The account can be unlocked in two ways:")
    print("\n1. ⏰ AUTOMATIC UNLOCK (after 15 minutes)")
    print("   - Wait 15 minutes from the lock time")
    print("   - Next login attempt will automatically unlock")
    print("\n2. 🔄 PASSWORD RESET")
    print("   - Request password reset via 'Forgot Password'")
    print("   - Resetting password immediately unlocks the account")
    print("\n3. 💾 MANUAL DATABASE UPDATE")
    print("   - Run SQL: UPDATE \"user\" SET is_locked = false, failed_attempts = 0")
    print("   - WHERE email = 'user@example.com';")

    print_separator("Test Complete")
    print("\nAccount locking mechanism demonstration finished.")
    print("Check the output above to see how the system handles failed login attempts.\n")

if __name__ == "__main__":
    main()
