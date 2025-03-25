import os
import platform
import sys


def test_print_system_info():
    """Print information about the system."""
    print("\n----- SYSTEM INFORMATION -----")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.architecture()}")
    print(f"Processor: {platform.processor()}")
    print(f"Machine: {platform.machine()}")
    assert True, "This test always passes"


def test_print_environment():
    """Print environment variables."""
    print("\n----- ENVIRONMENT VARIABLES -----")
    print(
        f"Path: {os.environ.get('PATH', 'Not found')[:50]}..."
    )  # Only print first 50 characters
    print(f"HOME: {os.environ.get('HOME', 'Not found')}")
    print(f"USER: {os.environ.get('USER', 'Not found')}")
    print(f"LANG: {os.environ.get('LANG', 'Not found')}")

    # Print number of environment variables
    print(f"Total environment variables: {len(os.environ)}")
    assert True, "This test always passes"
