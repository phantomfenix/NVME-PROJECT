#!/bin/env python3.9
import subprocess
import json
import os
import glob
## @class Activitytest1
#  @brief Test example to compare the output of the 'nvme id-ctrl' command with reference data.
#
#  This class runs a test that obtains information from the NVMe controller (using 'nvme-cli' or
#  a wrapper such as 'AdminPassthruWrapper'), converts it to JSON, and compares it against a reference file
#  to validate that there are no discrepancies.

class Activitytest1:
    def __init__(self, nvme_interface=None, logger=None):
        self.nvme_interface = nvme_interface
        self.logger = logger or print
        self.ignore_fields = {"sn", "fguid", "unvmcap", "subnqn"}

    def run(self):
        self.logger.info("Starting Example Test: Compare nvme id-ctrl output")
        # Step 1: Get id-ctrl data
        if self.nvme_interface:
            self.logger.debug("Collecting id-ctrl data via Admin Passthru...")
            output = self.nvme_interface.send_passthru_cmd(opcode='0x06', data_len=4096)
            raise NotImplementedError("Binary parsing for passthru not yet implemented")
        else:
            self.logger.debug("Collecting id-ctrl data via NVMe CLI...")
            output = subprocess.check_output(['nvme', 'id-ctrl', '/dev/nvme0', '--output-format=json'], text=True)
        # Step 2: Parse to JSON
        try:
            current_data = json.loads(output)
        except json.JSONDecodeError:
            self.logger.error("Failed to parse nvme id-ctrl output as JSON")
            return

        # Step 3: Ask user which reference JSON to use
        BASE_DIR = os.environ.get("NVME_PROJECT_DIR") or os.path.dirname(os.path.abspath(__file__))
        if os.path.basename(BASE_DIR) == "Test":
            REF_DIR = BASE_DIR
        else:
            REF_DIR = os.path.join(BASE_DIR, "Test")

        json_options = glob.glob(os.path.join(REF_DIR, "id-ctrl-main_*.json"))

        if not json_options:
            self.logger.error(f"No reference JSON files found in {REF_DIR}")
            return

        self.logger.info("Available reference JSON files:")
        for i, fname in enumerate(json_options, start=1):
            print(f"{i}) {fname}")

        choice = input("Select reference file [1/2]: ").strip()
        try:
           selected_file = json_options[int(choice) - 1]
        except (ValueError, IndexError):
            self.logger.error("Invalid selection. Using default: id-ctrl-main_good.json")
            selected_file = json_options[0]

        if not os.path.exists(selected_file):
            self.logger.error(f"Reference file not found: {selected_file}")
            return
        
        with open(selected_file, 'r') as f:
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

        # Step 5: Final result
        if errors == 0:
            self.logger.info("Test PASSED - All fields match.")
        else:
            self.logger.warning(f"Test FAILED - {errors} mismatches found.")
