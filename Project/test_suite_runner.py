#!/bin/env python3.9
from test_manager import TestManager
from Test.admin_passthru_wrapper import AdminPassthruWrapper
from Test.example_test import ExampleTest
## @brief Main entry point for the NVMe testing system.
#
#  This script initializes the test manager (**TestManager**), asks
#  the user if they want to use **Admin Passthru**, registers the available tests
#  and runs them.
#
#  @note
#  - The default device is '/dev/nvme0'.
#  - Root access is required to use **Admin Passthru**.
#
#  @code
#  $ python main.py
#  Do you want to use Admin Passthru? (y/n): y
#  @endcode

if __name__ == "__main__":
    use_passthru = input("Do you want to use Admin Passthru? (y/n): ").strip().lower() == 'y'
    
    admin_wrapper = None
    if use_passthru:
        admin_wrapper = AdminPassthruWrapper("/dev/nvme0")
    ## @brief Create TestManager instance with or without Admin Passthru.
    tm = TestManager(admin_wrapper=admin_wrapper)
    ## @brief Record available Test.
    # Register tests
    tm.add_test("Example Test", ExampleTest)
    ## @brief Run all registered tests.
    # Run all registered tests
    tm.run_all()
    # Reset (optional, depending on the execution flow)
    tm = TestManager(admin_wrapper=admin_wrapper)