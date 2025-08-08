#!/bin/env python3.9
import subprocess
import json
class ExampleTest:
    def __init__(self, nvme_interface=None, logger=None):
        self.nvme_interface = nvme_interface  # Could be AdminPassthruWrapper or None
        self.logger = logger or print
        self.ignore_fields = {"sn", "fguid", "unvmcap", "subnqn"}

    def run(self):
        self.logger.info("Starting Example Test: Compare nvme id-ctrl output")

        # Step 1: Collect current id-ctrl data
        if self.nvme_interface:
            self.logger.debug("Collecting id-ctrl data via Admin Passthru...")
            output = self.nvme_interface.send_passthru_cmd(opcode='0x06', data_len=4096)
            # Here you would parse the binary data from passthru into JSON if needed
            raise NotImplementedError("Binary parsing for passthru not yet implemented")
        else:
            self.logger.debug("Collecting id-ctrl data via NVMe CLI...")
            output = subprocess.check_output(['nvme', 'id-ctrl', '/dev/nvme0'], text=True)
        
        # Step 2: Parse to JSON
        try:
            current_data = json.loads(output)
        except json.JSONDecodeError:
            self.logger.error("Failed to parse nvme id-ctrl output as JSON")
            return

        # Step 3: Load reference JSON
        with open('id-ctrl-main.json', 'r') as f:
            reference_data = json.load(f)

        # Step 4: Compare
        errors = 0
        for key, expected_value in reference_data.items():
            if key in self.ignore_fields:
                continue
            current_value = current_data.get(key)
            if current_value != expected_value:
                self.logger.error(f"Mismatch in '{key}': Expected {expected_value}, Found {current_value}")
                errors += 1
            else:
                self.logger.debug(f"Match in '{key}': {expected_value}")

        # Step 5: Result
        if errors == 0:
            self.logger.info("Test PASSED - All fields match.")
        else:
            self.logger.warning(f"Test FAILED - {errors} mismatches found.")