#!/bin/env python3.9

import logging
import sys
from example_test import ExampleTest
from admin_passthru_wrapper import AdminPassthruWrapper

def setup_logger(name='test_manager_logger', log_file='test_manager.log', level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    # File Handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(ch)
        logger.addHandler(fh)

    return logger


class TestManager:
    def __init__(self):
        self.logger = setup_logger()

    def run(self):
        self.logger.info("Starting Test Manager...")

        # Ask user if they want to use Admin Passthru
        use_passthru = input("Do you want to use Admin Passthru? (y/n): ").strip().lower()
        if use_passthru == 'y':
            self.logger.info("Using Admin Passthru Wrapper")
            nvme_interface = AdminPassthruWrapper('/dev/nvme0')
        else:
            self.logger.info("Using standard NVMe CLI commands")
            nvme_interface = None  # Standard mode (no passthru)

        # Run the Example Test
        test = ExampleTest(nvme_interface, logger=self.logger)
        test.run()

        self.logger.info("Test Manager finished.")


if __name__ == '__main__':
    manager = TestManager()
    manager.run()