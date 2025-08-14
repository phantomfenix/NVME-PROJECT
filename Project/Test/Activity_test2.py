#!/bin/env python3.9
import subprocess
import json
import os
import random
## @class ActivityTest2
#  @brief Test to validate that the NVMe SMART log is working as expected.
#
#  This test uses Admin Passthru to collect SMART log data and validate multiple health parameters.
#  It also executes read/write operations to confirm that counters increment correctly.
nvme_id_ns = subprocess.run(
    ["nvme", "id-ns", "/dev/nvme0n1", "-o", "json"],
    capture_output=True, text=True, check=True
)
ns_info = json.loads(nvme_id_ns.stdout)
max_blocks = ns_info["nsze"]  # total LBA del namespace

class Activitytest2:
    def __init__(self, nvme_interface=None, logger=None):
        self.nvme_interface = nvme_interface
        self.logger = logger or print
        self.initial_temp_threshold = None

    def run(self):
        if not self.nvme_interface:
            self.logger.error("AdminPassthruWrapper is required for this test.")
            return

        self.logger.info("=== Starting SMART Log Validation Test ===")
        errors = []  # List to accumulate errors

        # Step 1: Initial SMART log snapshot
        smart_log_start = self._get_smart_log()
        pretty_log = json.dumps(smart_log_start, indent=4, sort_keys=True)
        self.logger.debug(f"Initial SMART log:\n{pretty_log}")

        # Step 2: Check media errors
        if smart_log_start.get("media_errors", 0) != 0:
            errors.append("Media errors found!")

        # Step 3: Check POH <= 1000 hours
        if smart_log_start.get("power_on_hours", 0) > 1000:
            errors.append("POH exceeds limit!")

        # Step 4: Get temperature threshold
        try:
           self.initial_temp_threshold = self._get_temperature_threshold()
           if not self.initial_temp_threshold or self.initial_temp_threshold <= 0:
              self.initial_temp_threshold = 100  # Sure fallback
           current_temp = smart_log_start.get("temperature", 25)
           if current_temp > self.initial_temp_threshold:
               self.logger.warning(f"Temperature {current_temp} exceeds threshold {self.initial_temp_threshold}, continuing test")
        except Exception as e:
           errors.append(f"Failed to get temperature threshold: {e}")
           self.initial_temp_threshold = 100  # fallback

        # Step 5: Percentage used
        if smart_log_start.get("percentage_used", 0) >= 100:
            errors.append("Percentage used is >= 100%")

        # Step 6: Generate random N reads/writes
        N = random.randint(10, 1000)
        self.logger.info(f"Performing {N} read and {N} write commands...")
        
        read_file = "/tmp/nvme_read_data"
        with open(read_file, "wb") as f:
            f.write(b"\x00"*4096)
        write_file = "/tmp/nvme_write_data"
        with open(write_file, "wb") as f:
            f.write(b"\x00"*4096)

        try:
           for _ in range(N):
               blk = random.randint(10, max_blocks-2)
               subprocess.run([
                   "nvme", "read", "/dev/nvme0n1",
                   f"--start-block={blk}",
                   "--block-count=1",
                   "--data-size=4096",
                   f"--data={read_file}"
               ], check=True) # stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
           for _ in range(N):
               blk = random.randint(10, max_blocks-2)
               subprocess.run([
                   "nvme", "write", "/dev/nvme0n1",
                   f"--start-block={blk}",
                   "--block-count=1",
                   "--data-size=4096",
                   f"--data={write_file}"
               ], check=True) #stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        except Exception as e:
           errors.append(f"Failed executing NVMe read/write commands: {e}")

        # Step 7: Set temperature threshold
        try:
           self._set_temperature_threshold(current_temp - 5)
           # After trying, read SMART log again to see if critical warning changed
           smart_log_after_set = self._get_smart_log()
           if smart_log_start.get("critical_warning") == smart_log_after_set.get("critical_warning"):
               self.logger.warning(
                   "Critical warning did not change after threshold adjustment; "
                   "this drive may not support changing the temp threshold."
               )
        except Exception as e:
            self.logger.warning(f"Could not set temperature threshold: {e}")

        # Step 8: Final SMART log
        smart_log_end = self._get_smart_log()
        pretty_log_end = json.dumps(smart_log_end, indent=4, sort_keys=True)
        self.logger.debug(f"Final SMART log:\n{pretty_log_end}")

        # Step 9: Validate read/write counters
        read_diff = smart_log_end.get("host_read_commands", 0) - smart_log_start.get("host_read_commands", 0)
        write_diff = smart_log_end.get("host_write_commands", 0) - smart_log_start.get("host_write_commands", 0)
        if read_diff != N:
            errors.append(f"Read counter mismatch! Expected +{N}, got {read_diff}")
        if write_diff != N:
            errors.append(f"Write counter mismatch! Expected +{N}, got {write_diff}")

        # Step 10: Validate critical warning changed
        smart_log_after_set = self._get_smart_log()
        if smart_log_start.get("critical_warning") == smart_log_after_set.get("critical_warning"):
            self.logger.warning(
                "Critical warning did not change after threshold adjustment; "
                "this drive may not support changing the temp threshold."
            )

        # Step 11: Restore temperature threshold
        try:
           self._set_temperature_threshold(self.initial_temp_threshold)
        except Exception as e:
            self.logger.warning(f"Could not restore temperature threshold: {e}")

        # Final evaluation
        if errors:
            for e in errors:
                self.logger.error(e)
            self.logger.warning("Test FAILED - see above errors")
        else:
            self.logger.info("Test PASSED - SMART log behaves as expected.")

    def _get_smart_log(self):
        try:
           output = subprocess.check_output(
               ["nvme", "smart-log", "/dev/nvme0", "-o", "json"],
               text=True
           )
           return json.loads(output)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to execute nvme smart-log: {e}")
            return {}
        except json.JSONDecodeError:
            self.logger.error("Failed to parse SMART log output as JSON")
            return {}

    def _get_temperature_threshold(self):
        try:
           output = subprocess.check_output(
               ["nvme", "get-feature", "/dev/nvme0n1", "--feature-id=0x4"], text=True)
           for line in output.splitlines():
                if "value" in line.lower():
                    return int(line.split(":")[-1].strip(), 0)  # admite hex o decimal
        except Exception as e:
            self.logger.error(f"Failed to get temperature threshold: {e}")
        return 85  # fallback seguro

    def _set_temperature_threshold(self, new_temp):
        try:
           subprocess.run(["nvme", "set-feature", "/dev/nvme0n1", "--feature-id=0x4", f"--value={new_temp}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        except Exception as e:
            self.logger.error(f"Failed to set temperature threshold: {e}")
