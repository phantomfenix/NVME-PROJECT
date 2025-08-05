import sys
from test_manager import TestManager
from tests.admin_passthru_test import AdminPassthruTest
from tests.example_test import ExampleTest

# Puedes seguir agregando más pruebas aquí
# from tests.otra_prueba import OtraPrueba

def main():
    serial = "12345678"  # Reemplaza con el serial real del drive
    tests_to_run = [
        ("AdminPassthruTest", AdminPassthruTest),
        ("ExampleTest", ExampleTest),
        # ("OtraPrueba", OtraPrueba),
    ]

    for testname, test_class in tests_to_run:
        test_manager = TestManager(
            serial_number=serial,
            testname=testname,
            test_class=test_class
        )

        try:
            test_manager.drive_check(discovery=True)
            test_manager.run()
            test_manager.set_final_result()
            test_manager.drive_check(discovery=False)
        except Exception as e:
            test_manager.logger.error(f"[{testname}] Test aborted: {e}")
            sys.exit(1)  # O cambia a continue si quieres seguir con el siguiente test

if __name__ == "__main__":
    main()
