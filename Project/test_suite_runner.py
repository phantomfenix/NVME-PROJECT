#!/bin/env python3.9
## @file main.py
#  @brief Main entry point for the NVMe testing system.
#
#  This script initializes the Test Manager (**TestManager**), asks
#  the user if they want to use **Admin Passthru**, registers the available tests
#  and runs them.
#
#  @details
#  - The default device path is '/dev/nvme0'.
#  - Root privileges are required for **Admin Passthru** mode.
#  - If **Admin Passthru** is not used, NVMe CLI commands are executed directly.
#
#  @note
#  Example usage:
#  @code
#  $ python main.py
#  Do you want to use Admin Passthru? (y/n): y
#  @endcode

from test_manager import TestManager
from Test.admin_passthru_wrapper import AdminPassthruWrapper
from Test.example_test import ExampleTest


if __name__ == "__main__":
    ## @brief Ask user whether to enable Admin Passthru.
    #  @return Boolean indicating if Admin Passthru should be enabled.
    use_passthru = input("Do you want to use Admin Passthru? (y/n): ").strip().lower() == 'y'
    ## @brief NVMe Admin Passthru interface wrapper instance.
    #  @details Initialized only if user chooses 'y' above.
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

    # Registrar tests
    tm.add_test("Example Test", ExampleTest)

    # Ejecutar todos los tests
    tm.run_all()
