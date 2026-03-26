"""
Test runner for CV Architecture Improvements
Runs all unit tests and generates coverage report
"""
import sys
import subprocess

def run_tests():
    """Run all tests with pytest"""
    print("=" * 70)
    print("Running CV Architecture Improvements Test Suite")
    print("=" * 70)
    print()
    
    # Run pytest with coverage
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '-v',
        '--tb=short',
        '--color=yes'
    ]
    
    # Try to add coverage if available
    try:
        import pytest_cov
        cmd.extend(['--cov=.', '--cov-report=term-missing', '--cov-report=html'])
        print("Running with coverage report...")
    except ImportError:
        print("Running without coverage (install pytest-cov for coverage reports)")
    
    print()
    result = subprocess.run(cmd)
    
    print()
    print("=" * 70)
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("=" * 70)
    
    return result.returncode

if __name__ == '__main__':
    sys.exit(run_tests())
