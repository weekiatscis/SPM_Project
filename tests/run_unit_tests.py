#!/usr/bin/env python3
"""
Unit Test Runner for SPM Project
Runs all unit tests and generates coverage report
"""

import sys
import os
import pytest
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header():
    """Print test runner header"""
    print(f"\n{BLUE}{BOLD}{'='*70}{RESET}")
    print(f"{BLUE}{BOLD}SPM PROJECT - UNIT TEST RUNNER{RESET}")
    print(f"{BLUE}{BOLD}{'='*70}{RESET}\n")


def print_section(title):
    """Print section header"""
    print(f"\n{YELLOW}{BOLD}{title}{RESET}")
    print(f"{YELLOW}{'-'*len(title)}{RESET}")


def run_unit_tests(verbose=True, coverage=False, specific_file=None):
    """
    Run unit tests with optional coverage reporting

    Args:
        verbose: Show detailed output
        coverage: Generate coverage report
        specific_file: Run only specific test file
    """
    print_header()

    # Determine test path
    if specific_file:
        test_path = f"tests/unit/{specific_file}"
        print(f"Running tests from: {BOLD}{test_path}{RESET}\n")
    else:
        test_path = "tests/unit/"
        print(f"Running all unit tests from: {BOLD}{test_path}{RESET}\n")

    # Build pytest arguments
    args = [test_path]

    if verbose:
        args.append("-v")

    args.append("--tb=short")  # Short traceback format

    if coverage:
        args.extend([
            "--cov=src/microservices",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ])

    # Run tests
    print_section("Executing Tests")
    exit_code = pytest.main(args)

    # Print summary
    print_section("Test Summary")

    if exit_code == 0:
        print(f"{GREEN}{BOLD}✓ All tests passed!{RESET}")
        if coverage:
            print(f"\n{BLUE}Coverage report generated in: {BOLD}htmlcov/index.html{RESET}")
            print(f"Open with: {BOLD}open htmlcov/index.html{RESET}\n")
    else:
        print(f"{RED}{BOLD}✗ Some tests failed!{RESET}")
        print(f"{YELLOW}Run with -v flag for detailed output{RESET}\n")

    return exit_code


def list_test_files():
    """List all available unit test files"""
    print_header()
    print_section("Available Unit Test Files")

    unit_test_dir = Path("tests/unit")
    test_files = sorted(unit_test_dir.glob("test_*.py"))

    if test_files:
        for i, file in enumerate(test_files, 1):
            print(f"{i}. {file.name}")
    else:
        print(f"{RED}No test files found!{RESET}")

    print()


def run_quick_tests():
    """Run quick tests without coverage"""
    print_header()
    print(f"{BLUE}Running quick unit tests (no coverage)...{RESET}\n")

    args = [
        "tests/unit/",
        "-v",
        "--tb=line",  # One line per failure
        "-q"  # Quiet mode
    ]

    exit_code = pytest.main(args)

    if exit_code == 0:
        print(f"\n{GREEN}{BOLD}✓ Quick tests passed!{RESET}\n")
    else:
        print(f"\n{RED}{BOLD}✗ Some tests failed!{RESET}\n")

    return exit_code


def run_specific_service(service_name):
    """Run tests for a specific service"""
    service_map = {
        "task": "test_task_service_unit.py",
        "user": "test_user_service_unit.py",
        "project": "test_project_service_unit.py",
        "auth": "test_auth_service_unit.py",
        "notification": "test_notification_service_unit.py"
    }

    if service_name not in service_map:
        print(f"{RED}Unknown service: {service_name}{RESET}")
        print(f"Available services: {', '.join(service_map.keys())}")
        return 1

    return run_unit_tests(verbose=True, coverage=False, specific_file=service_map[service_name])


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run unit tests for SPM Project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all unit tests with coverage
  python tests/run_unit_tests.py --coverage

  # Run tests for specific service
  python tests/run_unit_tests.py --service task

  # Quick run without coverage
  python tests/run_unit_tests.py --quick

  # List available test files
  python tests/run_unit_tests.py --list

  # Run specific test file
  python tests/run_unit_tests.py --file test_task_service_unit.py
        """
    )

    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Generate coverage report"
    )

    parser.add_argument(
        "--service", "-s",
        choices=["task", "user", "project", "auth", "notification"],
        help="Run tests for specific service"
    )

    parser.add_argument(
        "--file", "-f",
        help="Run specific test file"
    )

    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Quick test run (no coverage, minimal output)"
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available test files"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=True,
        help="Verbose output (default: True)"
    )

    args = parser.parse_args()

    # Handle different modes
    if args.list:
        list_test_files()
        return 0

    if args.quick:
        return run_quick_tests()

    if args.service:
        return run_specific_service(args.service)

    if args.file:
        return run_unit_tests(
            verbose=args.verbose,
            coverage=args.coverage,
            specific_file=args.file
        )

    # Default: run all tests
    return run_unit_tests(
        verbose=args.verbose,
        coverage=args.coverage
    )


if __name__ == "__main__":
    sys.exit(main())
