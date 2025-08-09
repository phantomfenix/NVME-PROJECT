#!/bin/env python3.9
from test_manager import TestManager
from Test.admin_passthru_wrapper import AdminPassthruWrapper
from Test.example_test import ExampleTest

if __name__ == "__main__":
    use_passthru = input("Do you want to use Admin Passthru? (y/n): ").strip().lower() == 'y'
    
    admin_wrapper = None
    if use_passthru:
        admin_wrapper = AdminPassthruWrapper("/dev/nvme0")

    tm = TestManager(admin_wrapper=admin_wrapper)

    # Register tests
    tm.add_test("Example Test", ExampleTest)

    # Run all registered tests
    tm.run_all()

    tm = TestManager(admin_wrapper=admin_wrapper)