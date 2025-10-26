#!/usr/bin/env python3
"""
Script to check Supabase password management logs
This verifies that password reset tokens, history, and rate limits are being logged properly
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime
import json

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def print_separator(title):
    """Print a nice separator for sections"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def check_password_reset_tokens():
    """Check password reset tokens table"""
    print_separator("PASSWORD RESET TOKENS")

    try:
        # Get all password reset tokens (limit to recent 10)
        response = supabase.table("password_reset_tokens").select("*").order("created_at", desc=True).limit(10).execute()

        if response.data:
            print(f"\nFound {len(response.data)} recent password reset token(s):\n")
            for idx, token in enumerate(response.data, 1):
                print(f"{idx}. Token ID: {token.get('token_id')}")
                print(f"   User ID: {token.get('user_id')}")
                print(f"   Created: {token.get('created_at')}")
                print(f"   Expires: {token.get('expires_at')}")
                print(f"   Is Used: {token.get('is_used', False)}")
                if token.get('used_at'):
                    print(f"   Used At: {token.get('used_at')}")
                print(f"   IP Address: {token.get('ip_address', 'N/A')}")
                print(f"   User Agent: {token.get('user_agent', 'N/A')[:50]}...")
                print()
        else:
            print("\nNo password reset tokens found.")
            print("This is normal if no password resets have been requested yet.")
    except Exception as e:
        print(f"\nError checking password reset tokens: {e}")

def check_password_history():
    """Check password history table"""
    print_separator("PASSWORD HISTORY")

    try:
        # Get recent password changes (limit to 10)
        response = supabase.table("password_history").select("*").order("created_at", desc=True).limit(10).execute()

        if response.data:
            print(f"\nFound {len(response.data)} recent password change(s):\n")
            for idx, entry in enumerate(response.data, 1):
                print(f"{idx}. History ID: {entry.get('history_id')}")
                print(f"   User ID: {entry.get('user_id')}")
                print(f"   Created: {entry.get('created_at')}")
                print(f"   Password Hash: {entry.get('password_hash', '')[:20]}... (truncated)")
                print()
        else:
            print("\nNo password history found.")
            print("Passwords should be logged here when users change their passwords.")
    except Exception as e:
        print(f"\nError checking password history: {e}")

def check_password_reset_rate_limit():
    """Check password reset rate limit table"""
    print_separator("PASSWORD RESET RATE LIMITS")

    try:
        # Get all rate limit records
        response = supabase.table("password_reset_rate_limit").select("*").order("last_request_at", desc=True).execute()

        if response.data:
            print(f"\nFound {len(response.data)} rate limit record(s):\n")
            for idx, record in enumerate(response.data, 1):
                print(f"{idx}. User ID: {record.get('user_id')}")
                print(f"   Email: {record.get('email')}")
                print(f"   Request Count: {record.get('request_count')}")
                print(f"   First Request: {record.get('first_request_at')}")
                print(f"   Last Request: {record.get('last_request_at')}")

                # Calculate if rate limit is active
                from datetime import datetime, timedelta, timezone
                if record.get('first_request_at'):
                    first_request = datetime.fromisoformat(record['first_request_at'].replace('Z', '+00:00'))
                    time_since_first = datetime.now(timezone.utc) - first_request
                    rate_limit_window = timedelta(minutes=3)

                    if time_since_first < rate_limit_window:
                        print(f"   Status: ACTIVE (within 3-minute window)")
                        if record.get('request_count', 0) >= 3:
                            print(f"   ⚠️  RATE LIMITED (max 3 requests reached)")
                    else:
                        print(f"   Status: EXPIRED (outside 3-minute window)")
                print()
        else:
            print("\nNo rate limit records found.")
            print("Records are created when users request password resets.")
    except Exception as e:
        print(f"\nError checking rate limits: {e}")

def check_audit_logs():
    """Check audit logs for password-related events"""
    print_separator("AUDIT LOGS (Password-Related Events)")

    try:
        # Get audit logs related to password events
        response = supabase.table("audit_logs").select("*").or_(
            "event_type.eq.password_reset_requested,"
            "event_type.eq.password_reset_completed,"
            "event_type.eq.password_changed,"
            "event_type.eq.account_locked"
        ).order("created_at", desc=True).limit(10).execute()

        if response.data:
            print(f"\nFound {len(response.data)} password-related audit log(s):\n")
            for idx, log in enumerate(response.data, 1):
                print(f"{idx}. Event: {log.get('event_type')}")
                print(f"   User ID: {log.get('user_id')}")
                print(f"   Session ID: {log.get('session_id', 'N/A')}")
                print(f"   Created: {log.get('created_at')}")
                print(f"   Description: {log.get('event_description', 'N/A')}")
                print(f"   IP Address: {log.get('ip_address', 'N/A')}")
                if log.get('metadata'):
                    print(f"   Metadata: {json.dumps(log.get('metadata'), indent=6)}")
                print()
        else:
            print("\nNo password-related audit logs found.")
            print("Note: Audit logs may need to be manually created by the application.")
    except Exception as e:
        print(f"\nError checking audit logs: {e}")

def check_user_security_status():
    """Check users table for security-related fields"""
    print_separator("USER SECURITY STATUS")

    try:
        # Get users with failed login attempts or locked accounts
        response = supabase.table("user").select(
            "user_id, email, name, failed_attempts, is_locked, locked_until, last_login"
        ).or_(
            "failed_attempts.gt.0,"
            "is_locked.eq.true"
        ).execute()

        if response.data:
            print(f"\nFound {len(response.data)} user(s) with security events:\n")
            for idx, user in enumerate(response.data, 1):
                print(f"{idx}. Email: {user.get('email')}")
                print(f"   Name: {user.get('name')}")
                print(f"   Failed Attempts: {user.get('failed_attempts', 0)}")
                print(f"   Is Locked: {user.get('is_locked', False)}")
                if user.get('locked_until'):
                    print(f"   Locked Until: {user.get('locked_until')}")
                if user.get('last_login'):
                    print(f"   Last Login: {user.get('last_login')}")
                print()
        else:
            print("\nNo users with failed attempts or locked accounts.")
            print("This is good - means no security incidents!")
    except Exception as e:
        print(f"\nError checking user security status: {e}")

def main():
    """Main function to run all checks"""
    print("\n" + "=" * 80)
    print("  SUPABASE PASSWORD MANAGEMENT LOGS CHECK")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 80)

    # Run all checks
    check_password_reset_tokens()
    check_password_history()
    check_password_reset_rate_limit()
    check_audit_logs()
    check_user_security_status()

    print_separator("CHECK COMPLETE")
    print("\nAll password management tables have been checked.")
    print("Review the output above to verify that logging is working properly.\n")

if __name__ == "__main__":
    main()
