from test_manager import TestManager
from tests.admin_passthru_test import AdminPassthruTest
from tests.example_test import ExampleTest

if __name__ == "__main__":
    tm = TestManager()

    # Register tests
    tm.add_test("Admin Passthru Test", AdminPassthruTest)
    tm.add_test("Example Test", ExampleTest)

    # Execute all registered tests
    tm.run_all()