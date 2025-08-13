#!/bin/env python3.9
import subprocess
import json
import os
## @class SmartLogTest
#  @brief Test to validate that the NVMe SMART log is working as expected.
#
#  This test uses Admin Passthru to collect SMART log data and validate multiple health parameters.
#  It also executes read/write operations to confirm that counters increment correctly.
class SmartLogTest:
    def __init__(self, nvme_interface=None, logger=None):
        self.nvme_interface = nvme_interface
        self.logger = logger or print
        self.initial_temp_threshold = None

    def run(self):
        if not self.nvme_interface:
            self.logger.error("AdminPassthruWrapper is required for this test.")
            return

        self.logger.info("=== Starting SMART Log Validation Test ===")

        # Step 1: Initial SMART log snapshot
        smart_log_start = self._get_smart_log()
        self.logger.debug(f"Initial SMART log: {smart_log_start}")

        # Step 2: Check media errors
        if smart_log_start.get("media_errors", 0) != 0:
            self.logger.error("Media errors found!")
            return

        # Step 3: Check POH <= 1000 hours
        if smart_log_start.get("power_on_hours", 0) > 1000:
            self.logger.error("POH exceeds limit!")
            return

        # Step 4: Get temperature threshold from NVMe Get Features (FID 0x4)
        self.initial_temp_threshold = self._get_temperature_threshold()
        current_temp = smart_log_start.get("temperature", 0)
        if current_temp > self.initial_temp_threshold:
            self.logger.error("Temperature exceeds threshold!")
            return

        # Step 5: Percentage used < 100%
        if smart_log_start.get("percentage_used", 0) >= 100:
            self.logger.error("Percentage used is >= 100%")
            return

        # Step 6: Generate random N
        N = random.randint(1, 200)
        self.logger.info(f"Performing {N} read and {N} write commands...")

        # Execute N reads
        for _ in range(N):
            subprocess.run(["nvme", "read", "/dev/nvme0", "--start-block=0", "--block-count=1"], stdout=subprocess.DEVNULL)

        # Execute N writes
        for _ in range(N):
            subprocess.run(["nvme", "write", "/dev/nvme0", "--start-block=0", "--block-count=1", "--data=/dev/zero"], stdout=subprocess.DEVNULL)

        # Step 7: Change temperature threshold to trigger critical warning
        self._set_temperature_threshold(current_temp - 5)

        # Step 8: Final SMART log snapshot
        smart_log_end = self._get_smart_log()

        # Step 9: Validate read/write counters increased by N
        read_diff = smart_log_end.get("host_read_commands", 0) - smart_log_start.get("host_read_commands", 0)
        write_diff = smart_log_end.get("host_write_commands", 0) - smart_log_start.get("host_write_commands", 0)

        if read_diff != N:
            self.logger.error(f"Read counter mismatch! Expected +{N}, got {read_diff}")
            return
        if write_diff != N:
            self.logger.error(f"Write counter mismatch! Expected +{N}, got {write_diff}")
            return

        # Step 10: Validate critical warning changed
        if smart_log_start.get("critical_warning") == smart_log_end.get("critical_warning"):
            self.logger.error("Critical warning did not change after threshold adjustment!")
            return

        # Step 11: Restore temperature threshold
        self._set_temperature_threshold(self.initial_temp_threshold)

        self.logger.info("Test PASSED - SMART log behaves as expected.")

    def _get_smart_log(self):
        output = self.nvme_interface.send_passthru_cmd(opcode="0x02", data_len=512)
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            self.logger.error("Failed to parse SMART log output as JSON")
            return {}

    def _get_temperature_threshold(self):
        output = subprocess.check_output(["nvme", "get-feature", "/dev/nvme0", "--fid=0x4"], text=True)
        # Extract numeric threshold from output
        for line in output.splitlines():
            if "value" in line.lower():
                try:
                    return int(line.split(":")[-1].strip())
                except ValueError:
                    pass
        return 0

    def _set_temperature_threshold(self, new_temp):
        subprocess.run(["nvme", "set-feature", "/dev/nvme0", "--fid=0x4", f"--value={new_temp}"])
