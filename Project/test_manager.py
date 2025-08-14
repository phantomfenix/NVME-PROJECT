#!/bin/env python3.9

import logging
import sys
import os
from datetime import datetime

#def setup_logger(name='test_manager_logger', log_file='test_manager.log', level=logging.DEBUG):
    
def setup_logger(name='test_manager_logger', base_dir=None, level=logging.DEBUG):
    if base_dir is None:
        base_dir = os.environ.get("NVME_PROJECT_RESULT_DIR") or os.path.join(os.path.expanduser("~"), "NVME_RESULTS")
    #Create folder with date
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    log_dir = os.path.join(base_dir, fecha_hoy)
    os.makedirs(log_dir, exist_ok=True)

    # File name with time
    log_file = os.path.join(log_dir, f'test_manager_{datetime.now().strftime("%H-%M-%S")}.log')
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
    def __init__(self, admin_wrapper=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.admin_wrapper = admin_wrapper
        self.tests = []

    def add_test(self, name, test_class):
        self.tests.append((name, test_class))

    def run_all(self):
        self.logger.info("Starting Test Manager...")
        for name, test_class in self.tests:
            self.logger.info(f"Running test: {name}")
            test_instance = test_class(self.admin_wrapper, logger=self.logger)
            test_instance.run()
        self.logger.info("Test Manager finished.")
