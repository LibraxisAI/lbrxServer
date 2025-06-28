#!/usr/bin/env uv run
"""
Generate secure API keys for MLX LLM Server
"""
import json
import secrets
from datetime import datetime


def generate_api_key(service_name: str) -> str:
    """Generate a secure API key for a service"""
    # Generate 32 bytes of randomness (256 bits)
    random_bytes = secrets.token_hex(32)
    
    # Service-specific prefixes for routing
    prefix_map = {
        "vista": "vista",
        "whisplbrx": "whisp",
        "forkmeASAPp": "fork",
        "fork": "fork",
        "anyDataNext": "data",
        "anydatanext": "data",
        "lbrxVoice": "voice",
        "lbrxvoice": "voice",
        "admin": "lbrx",
        "monitoring": "lbrx",
        "test": "lbrx"
    }
    
    # Get base service name (remove _prod, _dev suffixes)
    base_service = service_name.lower().replace('_prod', '').replace('_dev', '')
    prefix = prefix_map.get(base_service, "lbrx")
    
    return f"{prefix}_{random_bytes}"


def main():
    """Generate API keys for all services"""
    services = [
        "vista_prod",
        "vista_dev",
        "whisplbrx",
        "forkmeASAPp",
        "anyDataNext",
        "lbrxVoice",
        "lbrxVoicePro",
        "admin",
        "monitoring",
        "test"
    ]

    print("🔐 MLX LLM Server API Key Generator")
    print("=" * 50)

    api_keys = {}
    env_format = []

    for service in services:
        key = generate_api_key(service)
        api_keys[service] = {
            "key": key,
            "created": datetime.utcnow().isoformat(),
            "service": service
        }
        env_format.append(key)
        print(f"✅ {service}: {key}")

    # Save to file
    with open("api_keys.json", "w") as f:
        json.dump(api_keys, f, indent=2)

    print("\n" + "=" * 50)
    print("📄 Keys saved to api_keys.json")
    print("\n🔧 For .env file, use:")
    print(f"API_KEYS={','.join(env_format[:5])}")
    print("\n⚠️  Keep these keys secure and never commit them to git!")

    # Generate JWT secret
    jwt_secret = secrets.token_urlsafe(64)
    print(f"\n🔑 JWT Secret: {jwt_secret}")
    print("Add to .env: JWT_SECRET=" + jwt_secret)


if __name__ == "__main__":
    main()
