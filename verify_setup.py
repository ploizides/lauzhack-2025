"""
Setup verification script for Real-Time Podcast AI Assistant.
Checks if all dependencies are installed and configured correctly.
"""

import sys


def check_imports():
    """Check if all required packages can be imported."""
    print("Checking package imports...")
    print("=" * 50)

    packages = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "deepgram": "Deepgram SDK",
        "together": "Together AI",
        "duckduckgo_search": "DuckDuckGo Search",
        "networkx": "NetworkX",
        "aiohttp": "aiohttp",
        "pydantic": "Pydantic",
        "pydantic_settings": "Pydantic Settings",
        "dotenv": "python-dotenv",
    }

    failed = []
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError as e:
            print(f"✗ {name}: {e}")
            failed.append(name)

    print()
    return failed


def check_env_file():
    """Check if .env file exists and has required keys."""
    print("Checking environment configuration...")
    print("=" * 50)

    import os
    from pathlib import Path

    env_path = Path(".env")

    if not env_path.exists():
        print("✗ .env file not found")
        print("  Run: cp .env.example .env")
        print("  Then edit .env and add your API keys")
        return False

    print("✓ .env file found")

    # Check if keys are set
    try:
        from dotenv import load_dotenv

        load_dotenv()

        required_keys = ["DEEPGRAM_API_KEY", "TOGETHER_API_KEY"]
        missing = []

        for key in required_keys:
            value = os.getenv(key)
            if not value or value.startswith("your_"):
                print(f"✗ {key} not configured")
                missing.append(key)
            else:
                print(f"✓ {key} configured")

        print()
        return len(missing) == 0

    except Exception as e:
        print(f"✗ Error loading .env: {e}")
        return False


def check_modules():
    """Check if our custom modules can be imported."""
    print("Checking custom modules...")
    print("=" * 50)

    modules = [
        "config",
        "state_manager",
        "topic_engine",
        "fact_engine",
        "main",
    ]

    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}.py")
        except Exception as e:
            print(f"✗ {module}.py: {e}")
            failed.append(module)

    print()
    return failed


def check_deepgram_version():
    """Check Deepgram SDK version."""
    print("Checking Deepgram SDK version...")
    print("=" * 50)

    try:
        import deepgram

        # Try to get version
        if hasattr(deepgram, "__version__"):
            version = deepgram.__version__
            print(f"✓ Deepgram SDK version: {version}")

            # Check if it's 5.x
            major_version = int(version.split(".")[0])
            if major_version >= 5:
                print("✓ Version 5.x or higher (compatible)")
            else:
                print(f"✗ Version {version} detected, need 5.x or higher")
                print("  Run: pip install --upgrade deepgram-sdk")
                return False
        else:
            print("✓ Deepgram SDK installed (version check unavailable)")

        # Try to import key classes
        from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents

        print("✓ All required Deepgram classes available")
        print()
        return True

    except ImportError as e:
        print(f"✗ Deepgram SDK import failed: {e}")
        print()
        return False


def main():
    """Run all verification checks."""
    print("\n" + "=" * 50)
    print("Real-Time Podcast AI Assistant - Setup Verification")
    print("=" * 50)
    print()

    all_passed = True

    # Check imports
    failed_imports = check_imports()
    if failed_imports:
        all_passed = False
        print(f"⚠ Failed to import: {', '.join(failed_imports)}")
        print("Run: pip install -r requirements.txt")
        print()

    # Check Deepgram version
    if not check_deepgram_version():
        all_passed = False

    # Check environment
    if not check_env_file():
        all_passed = False

    # Check custom modules (only if imports succeeded)
    if not failed_imports:
        failed_modules = check_modules()
        if failed_modules:
            all_passed = False
    else:
        print("⚠ Skipping custom module checks (dependencies missing)")
        print()

    # Final summary
    print("=" * 50)
    if all_passed:
        print("✓ All checks passed!")
        print()
        print("You're ready to start the server:")
        print("  python main.py")
        print()
        print("Or run the test client:")
        print("  python test_client.py")
    else:
        print("✗ Some checks failed")
        print()
        print("Please fix the issues above before running the server.")
        sys.exit(1)

    print("=" * 50)


if __name__ == "__main__":
    main()
