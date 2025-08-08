import sys
import logging

class TestManager:
    def __init__(self, logger=None):
        self.tests = []
        self.logger = logger or self._setup_logger()

    def _setup_logger(self):
        """Configure the default logger for the Test Manager."""
        logger = logging.getLogger('TestManager')
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)  # Show all log levels in console
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(ch)
        return logger

    def add_test(self, name, func):
        """Register a test by providing a name and a function."""
        self.tests.append((name, func))

    def run_all(self):
        """Execute all registered tests."""
        for name, func in self.tests:
            self.logger.info(f"=== Running test: {name} ===")
            try:
                result = func(self.logger)  # Pass the logger to the test function
                self.logger.info(f"Result: {result}\n")
            except Exception as e:
                self.logger.error(f"Test '{name}' failed: {str(e)}\n")