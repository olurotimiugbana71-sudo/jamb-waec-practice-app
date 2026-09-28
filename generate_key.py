"""
generate_key.py
----------------
Run this on YOUR OWN computer after a customer pays - never deploy this
file's functionality inside the live app. It produces the one genuine
license key for a given email, using your private LICENSE_SECRET.

Usage (in your terminal, inside the project folder, venv activated):
    python generate_key.py customer@email.com
"""

import sys
import os
from dotenv import load_dotenv
from license import generate_license_key

load_dotenv()


def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_key.py customer@email.com")
        sys.exit(1)

    email = sys.argv[1]
    secret = os.environ.get("LICENSE_SECRET", "")

    if not secret:
        print("LICENSE_SECRET not found in your .env file - add it first, e.g.")
        print('LICENSE_SECRET=some-long-random-private-string')
        sys.exit(1)

    key = generate_license_key(email, secret)
    print("\nSend the customer BOTH of these (they must enter the exact same email):")
    print(f"  Email:        {email}")
    print(f"  License key:  {key}\n")


if __name__ == "__main__":
    main()