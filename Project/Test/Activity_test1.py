#!/bin/env python3.9
import subprocess
import json
## @class Activitytest1
#  @brief Test example to compare the output of the 'nvme id-ctrl' command with reference data.
#
#  This class runs a test that obtains information from the NVMe controller (using 'nvme-cli' or
#  a wrapper such as 'AdminPassthruWrapper'), converts it to JSON, and compares it against a reference file
#  to validate that there are no discrepancies.
class Activitytest1:
    ## @brief Class constructor.
    #  @param nvme_interface Optional interface for sending NVMe commands (e.g., AdminPassthruWrapper).
    #  @param logger Logger instance for logging information, warnings, and errors.
    def __init__(self, nvme_interface=None, logger=None):
        self.nvme_interface = nvme_interface
        self.logger = logger or print
        self.ignore_fields = {"sn", "fguid", "unvmcap", "subnqn"}
    ## @brief Runs the 'nvme id-ctrl' comparison test.
    #
    #  @details
    #  The test follows these steps:
    #  1. Obtains NVMe controller information ('id-ctrl') using:
    #     - The passthru interface if available, or
    #     - The 'nvme-cli' command if it is not.
    #  2. Converts the output to JSON format.
    #  3. Loads a reference file ('id-ctrl-main.json').
    #  4. Compares the fields, ignoring those defined in 'ignore_fields'.
    #  5. Displays the comparison result.
    #
    #  @note
    #  If 'nvme_interface' is present, it is assumed to return binary data, so a
    #  binary-to-JSON parser would need to be implemented (not yet implemented).
    #
    #  @exception NotImplementedError If attempting to use the passthru interface without a binary parser implemented.
    #  @exception json.JSONDecodeError If the output of 'nvme id-ctrl' is not valid JSON.
    #
    #  @code
    #  test = ExampleTest()
    #  test.run()
    #  @endcode

    def run(self):
        self.logger.info("Starting Example Test: Compare nvme id-ctrl output")
        # Step 1: Get id-ctrl data
        if self.nvme_interface:
            self.logger.debug("Collecting id-ctrl data via Admin Passthru...")
            output = self.nvme_interface.send_passthru_cmd(opcode='0x06', data_len=4096)
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

        # Step 3: Ask user which reference JSON to use
        json_options = [
            "id-ctrl-main_good.json",
            "id-ctrl-main_bad.json"
        ]
        self.logger.info("Available reference JSON files:")
        for i, fname in enumerate(json_options, start=1):
            print(f"{i}) {fname}")

        choice = input("Select reference file [1/2]: ").strip()
        try:
            selected_file = json_options[int(choice) - 1]
        except (ValueError, IndexError):
            self.logger.error("Invalid selection. Using default: id-ctrl-main_good.json")
            selected_file = "id-ctrl-main_good.json"

        reference_path = os.path.join(
            "/root/Team3_REPO/NVME-PROJECT/Project/Test", selected_file
        )

        if not os.path.exists(reference_path):
            self.logger.error(f"Reference file not found: {reference_path}")
            return

        with open(reference_path, 'r') as f:
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