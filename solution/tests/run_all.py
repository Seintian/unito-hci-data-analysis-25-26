"""
Unified Test Runner for Pre-Cleaning Analysis Package.

This script acts as the entry point for the test suite. It performs two key functions:
1.  **Environment Setup**: Injects the `solution/notebooks` directory into `sys.path`,
    ensuring that tests can import the `nb_00_pre_cleaning_analysis` package without
    requiring manual `PYTHONPATH` configuration.
2.  **Test Discovery & Execution**: Auto-discovers all `test_*.py` files in subdirectories
    and interprets them using a custom `PrettyTestRunner` for enhanced readability.

Usage:
    python solution/tests/run_all.py
"""

import unittest
import os
import sys
import io
import time
import textwrap

class PrettyTestResult(unittest.TestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.stream = stream
        self.captured_stdout = io.StringIO()
        self.captured_stderr = io.StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def startTest(self, test):
        super().startTest(test)
        # Capture output during test
        self.captured_stdout = io.StringIO()
        self.captured_stderr = io.StringIO()
        sys.stdout = self.captured_stdout
        sys.stderr = self.captured_stderr

    def stopTest(self, test):
        # Restore output
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        super().stopTest(test)

    def _get_description(self, test):
        doc_first_line = test.shortDescription()
        test_id = str(test).split()[0] # e.g. test_something

        # Clean up test id: extract just the method name if possible
        if '(' in str(test):
            # Format: test_name (module.class.TestClass)
            test_id = str(test).split()[0]

        desc = test_id
        if doc_first_line:
            desc = f"{test_id}: {doc_first_line}"

        # Truncate if too long
        if len(desc) > 70:
            desc = desc[:67] + "..."
        return desc.ljust(75)

    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.write(f"{self._get_description(test)} \033[92m[PASS] \u2705\033[0m\n")
        self.stream.flush()

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.write(f"{self._get_description(test)} \033[91m[FAIL] \u274C\033[0m\n")
        self._print_captured_output()
        self.stream.flush()

    def addError(self, test, err):
        super().addError(test, err)
        self.stream.write(f"{self._get_description(test)} \033[91m[ERROR] \u26A0\ufe0f\033[0m\n")
        self._print_captured_output()
        self.stream.flush()

    def _print_captured_output(self):
        out = self.captured_stdout.getvalue()
        err = self.captured_stderr.getvalue()
        if out:
            self.stream.write(textwrap.indent(f"--- Stdout ---\n{out}", "    "))
        if err:
            self.stream.write(textwrap.indent(f"--- Stderr ---\n{err}", "    "))


class PrettyTestRunner(unittest.TextTestRunner):
    def _makeResult(self):
        return PrettyTestResult(self.stream, self.descriptions, self.verbosity)

    def run(self, test):
        "Run the given test case or test suite."
        result = self._makeResult()
        # unittest.registerResult(result) # Optional

        start_time = time.time()
        test(result)
        stop_time = time.time()

        # Custom Summary (No duplicate footer)
        time_taken = stop_time - start_time

        print("\n" + "=" * 85)
        print(f"Test Run Summary - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 85)

        print(f"Ran {result.testsRun} tests in {time_taken:.3f}s\n")

        if result.wasSuccessful():
            print(f"\033[92mCOMPLETE: ALL TESTS PASSED \u2705\033[0m")

        else:
            print(f"\033[91mCOMPLETE: {len(result.failures)} FAILURES, {len(result.errors)} ERRORS \u274C\033[0m")

            # Print details for failures
            if result.failures:
                print("\n\033[1mFailures:\033[0m")
                for test, trace in result.failures:
                    print(f"- {test}")
                    print(textwrap.indent(trace, "  "))
            if result.errors:
                print("\n\033[1mErrors:\033[0m")
                for test, trace in result.errors:
                    print(f"- {test}")
                    print(textwrap.indent(trace, "  "))

        return result


def run_tests():
    # 1. Determine Paths
    test_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.abspath(os.path.join(test_dir, "../notebooks"))

    # 2. Inject Source Path
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    # print(f"\n\033[1m[TEST RUNNER]\033[0m Added to sys.path: {src_dir}\n")

    # 3. Discover and Run Tests
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=test_dir, pattern='test_*.py')

    # Use our custom runner
    runner = PrettyTestRunner(verbosity=0)
    result = runner.run(suite)

    sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    run_tests()
