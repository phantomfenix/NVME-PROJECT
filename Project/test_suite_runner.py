#!/bin/env python3.9
import logging
import os
from datetime import datetime
from test_manager import TestManager
from Test.admin_passthru_wrapper import AdminPassthruWrapper
from Test.Activity_test1 import Activitytest1
from Test.Activity_test2 import Activitytest2
from Test.Activity_test3 import Activitytest3

if __name__ == "__main__":
    # Logs config
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

    # Question if to use Admin Passthru
    use_passthru = input("Do you want to use Admin Passthru? (y/n): ").strip().lower() == 'y'
    admin_wrapper = AdminPassthruWrapper("/dev/nvme0") if use_passthru else None

    # Create an instance of the TestManager
    tm = TestManager(admin_wrapper=admin_wrapper)

    # Record all tests
    available_tests = {
        "1": ("Activity test1", Activitytest1),
        "2": ("Activity test2", Activitytest2),
        "3": ("Activity test3", Activitytest3)
    }

    # Show selection menu
    print("\nAvailable tests:")
    for key, (name, _) in available_tests.items():
        print(f"{key}) {name}")

    choice = input("Select the test to run (1-3): ").strip()

    # Validate selection
    if choice in available_tests:
        name, test_class = available_tests[choice]
        tm.add_test(name, test_class)
        tm.run_all()
    else:
        print("❌ Invalid selection. Exiting...")
