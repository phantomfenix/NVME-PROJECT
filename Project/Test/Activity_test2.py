#!/bin/env python3.9
import os
import json
import random
import tempfile
from Test.admin_passthru_wrapper import AdminPassthruWrapper

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
        errors = []

        # --- INITIAL SMART LOG SNAPSHOT via Admin Passthru ---
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
              self.initial_temp_threshold = 100
           current_temp = smart_log_start.get("temperature", 25)
           if current_temp > self.initial_temp_threshold:
               self.logger.warning(f"Temperature {current_temp} exceeds threshold {self.initial_temp_threshold}, continuing test")
        except Exception as e:
           errors.append(f"Failed to get temperature threshold: {e}")
           self.initial_temp_threshold = 100

        # Step 5: Percentage used
        if smart_log_start.get("percentage_used", 0) >= 100:
            errors.append("Percentage used is >= 100%")

        # Step 6: Random read/write operations (igual que antes)
        N = random.randint(10, 1000)
        self.logger.info(f"Performing {N} read and {N} write commands...")
        read_file = "/tmp/nvme_read_data"
        write_file = "/tmp/nvme_write_data"
        with open(read_file, "wb") as f: f.write(b"\x00"*4096)
        with open(write_file, "wb") as f: f.write(b"\x00"*4096)

        try:
            for _ in range(N):
                blk = random.randint(10, max_blocks-2)
                subprocess.run([
                    "nvme", "read", "/dev/nvme0n1",
                    f"--start-block={blk}",
                    "--block-count=1",
                    "--data-size=4096",
                    f"--data={read_file}"
                ], check=True)
            for _ in range(N):
                blk = random.randint(10, max_blocks-2)
                subprocess.run([
                    "nvme", "write", "/dev/nvme0n1",
                    f"--start-block={blk}",
                    "--block-count=1",
                    "--data-size=4096",
                    f"--data={write_file}"
                ], check=True)
        except Exception as e:
            errors.append(f"Failed executing NVMe read/write commands: {e}")

        # Step 7: Set temperature threshold (igual que antes)
        try:
           self._set_temperature_threshold(current_temp - 5)
           smart_log_after_set = self._get_smart_log()
           if smart_log_start.get("critical_warning") == smart_log_after_set.get("critical_warning"):
               self.logger.warning("Critical warning did not change after threshold adjustment; this drive may not support changing the temp threshold.")
        except Exception as e:
            self.logger.warning(f"Could not set temperature threshold: {e}")

        # --- FINAL SMART LOG SNAPSHOT via Admin Passthru ---
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

        # Step 10: Restore temperature threshold
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
        """
        Devuelve el SMART log usando AdminPassthru si está disponible,
        de lo contrario usa nvme smart-log por subprocess.
        """
        if self.nvme_interface:
            raw_data = self.nvme_interface.send_passthru_cmd(opcode=0x2, data_len=512, nsid=0)
            if raw_data:
                return {"raw_data": raw_data.hex()}  # simple fallback, puedes parsear más si quieres
            else:
                self.logger.error("AdminPassthruWrapper: Failed to get SMART log")
                return {}
        else:
            try:
                output = subprocess.check_output(
                    ["nvme", "smart-log", "/dev/nvme0", "-o", "json"],
                    text=True
                )
                return json.loads(output)
            except:
                self.logger.error("Failed to get SMART log via subprocess")
                return {}

    def _get_temperature_threshold(self):
        # Feature ID 0x4
        raw = self.nvme_interface.send_passthru_cmd(opcode=0x0A, nsid=0, data_len=4)
        # interpretar bytes a int
        return int.from_bytes(raw[:4], byteorder='little', signed=False)

    def _set_temperature_threshold(self, new_temp):
        # Feature ID 0x4, opcode 0x09
        value_bytes = new_temp.to_bytes(4, byteorder='little')
        self.nvme_interface.send_passthru_cmd(opcode=0x09, nsid=0, data_len=4)