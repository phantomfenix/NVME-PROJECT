#!/bin/env python3.9

import logging
import sys

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
    def __init__(self, admin_wrapper=None):
        self.logger = setup_logger()
        self.admin_wrapper = admin_wrapper
        self.tests = []

    def add_test(self, name, test_class):
        """Registrar un test con su nombre y clase"""
        self.tests.append((name, test_class))

    def run_all(self):
        """Ejecutar todos los tests registrados"""
        self.logger.info("Starting Test Manager...")
        for name, test_class in self.tests:
            self.logger.info(f"Running test: {name}")
            test_instance = test_class(self.admin_wrapper, logger=self.logger)
            test_instance.run()
        self.logger.info("Test Manager finished.")