#!/usr/bin/env python3
import secrets
import string

def generate_key(length=50, safe=True):
    """
    Generate a cryptographically secure random key.
    If safe=True, avoids quotes and backslashes for easier use in configs.
    """
    chars = string.ascii_letters + string.digits + string.punctuation
    if safe:
        chars = chars.replace('"', '').replace("'", '').replace('\\', '')
    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_django_secret_key():
    """Generate Django SECRET_KEY (default 50 chars)."""
    return generate_key(50, safe=True)


def generate_jwt_secret(length=64):
    """Generate JWT Secret (longer key, default 64 chars)."""
    return secrets.token_hex(length)  # hex encoding -> safe for env files


if __name__ == "__main__":
    print("\n🔑 Generated Security Keys:\n")
    print(f"Django SECRET_KEY:\n{generate_django_secret_key()}\n")
    print(f"JWT_SECRET:\n{generate_jwt_secret()}\n")
