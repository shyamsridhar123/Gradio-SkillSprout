#!/usr/bin/env python3
"""
Simple test runner for SkillSprout - streamlined for hackathon
"""
import subprocess
import sys

def run_tests():
    """Run the simplified test suite"""
    print("🌱 SkillSprout - Running Tests")
    print("=" * 40)
    
    # Run the tests we actually have
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]
    
    try:
        result = subprocess.run(cmd, check=False)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print("\n⚠️  Some tests failed (this is OK for development)")
        
        return result.returncode
        
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
