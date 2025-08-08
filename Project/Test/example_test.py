#!/bin/env python3.9
import subprocess
import json
import logging
from Test import Test

class ExampleTest(Test):
    def __init__(self, name="ExampleTest", description="NVMe id-ctrl comparison test"):
        super().__init__(name, description)
        self.ignore_fields = ["sn", "fguid", "unvmcap", "subnqn"]

    def run(self):
        logging.info("Starting NVMe id-ctrl test")

        # Ask dynamically if admin passthru should be used
        use_admin = input("Do you want to run this test using admin-passthru? (y/n): ").strip().lower() == 'y'

        try:
            # Decide which command to run
            if use_admin:
                logging.info("Running Identify via admin-passthru")
                cmd = [
                    "nvme", "admin-passthru", "/dev/nvme0",
                    "--opcode=0x06", "--namespace-id=0x1",
                    "--data-len=4096", "--read", "--output-format=json"
                ]
            else:
                logging.info("Running Identify via nvme id-ctrl")
                cmd = ["nvme", "id-ctrl", "/dev/nvme0", "--output-format=json"]

            # Execute the command
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            device_data = json.loads(result.stdout)

            # Load reference JSON
            with open("id-ctrl-main.json", "r") as f:
                reference_data = json.load(f)

            # Compare values
            errors = 0
            for key, expected_value in reference_data.items():
                if key in self.ignore_fields:
                    continue
                if device_data.get(key) != expected_value:
                    logging.error(f"Mismatch in '{key}': expected {expected_value}, got {device_data.get(key)}")
                    errors += 1
                else:
                    logging.info(f"Match: {key} = {expected_value}")

            # Result
            if errors == 0:
                logging.info("Test PASSED")
                self.passed = True
            else:
                logging.error(f"Test FAILED with {errors} mismatches")
                self.passed = False

        except subprocess.CalledProcessError as e:
            logging.error(f"Command execution failed: {e.stderr}")
            self.passed = False
        except json.JSONDecodeError:
            logging.error("Failed to parse JSON output")
            self.passed = False
        except FileNotFoundError:
            logging.error("Reference file id-ctrl-main.json not found")
            self.passed = False