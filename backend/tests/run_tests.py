#!/usr/bin/env python
"""
Script to run the educational agent tests.
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Set environment variables for testing
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["GEMINI_API_KEY"] = "test-key"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import pytest

def run_tests():
    """Run all tests with detailed output."""
    test_args = [
        "backend/tests/test_educational_agent.py",
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "-s",  # Show print statements
        "--color=yes",  # Colored output
    ]
    
    print("=" * 60)
    print("Running Educational Agent Unit Tests")
    print("=" * 60)
    
    exit_code = pytest.main(test_args)
    
    if exit_code == 0:
        print("\n" + "=" * 60)
        print("✅ All tests passed successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Some tests failed. Check the output above.")
        print("=" * 60)
    
    return exit_code

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)