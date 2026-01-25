#!/usr/bin/env python3
"""
Generate API Key for Blog Publishing

This script generates a secure API key for the blog publishing system.
Run it once, then:
1. Add the API key to your .env file as BLOG_API_KEY
2. Run the SQL query in Hostinger's phpMyAdmin to store the hash

Usage:
    python generate_blog_api_key.py
"""

import secrets
import bcrypt


def generate_api_key():
    """Generate a cryptographically secure API key."""
    return secrets.token_urlsafe(32)


def hash_api_key(key: str) -> str:
    """Hash the API key using bcrypt (compatible with PHP's password_verify)."""
    return bcrypt.hashpw(key.encode(), bcrypt.gensalt()).decode()


def main():
    print("\n" + "=" * 60)
    print("Blog Publishing API Key Generator")
    print("=" * 60)

    # Generate key
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)

    print("\n1. Add this to your .env file:")
    print("-" * 40)
    print(f"BLOG_API_KEY={api_key}")

    print("\n2. Run this SQL in Hostinger phpMyAdmin:")
    print("-" * 40)
    print(f"""
INSERT INTO api_keys (key_name, key_hash, description, is_active)
VALUES (
    'blog_publisher',
    '{key_hash}',
    'API key for blog post publishing from Python script',
    TRUE
);
""")

    print("\n3. Test with:")
    print("-" * 40)
    print("python publish_blog.py --list")

    print("\n" + "=" * 60)
    print("Keep the API key secret! Don't commit .env to git.")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
