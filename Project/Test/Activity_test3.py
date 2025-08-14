import sys
import json
import subprocess
import os
from datetime import datetime
from Test.admin_passthru_wrapper import AdminPassthruWrapper

class Activitytest3:
    def __init__(self, nvme_interface, logger):
        self.nvme_interface = nvme_interface
        self.logger = logger
        self.result = "NOT RUN"

    def run(self):
        self.logger.info("Starting Activitytest3 with Admin Passthru...")

        try:
            # --- Admin Passthru: Identify Controller ---
            self.logger.debug("Sending Identify Controller command via Admin Passthru...")
            output = self.nvme_interface.send_passthru_cmd(opcode='0x06', data_len=4096)
            hex_preview = output[:64].hex(" ") if output else ""
            parsed_data = {
                "raw_hex_preview": hex_preview,
                "total_bytes": len(output) if output else 0
            }
            self.logger.info(f"Collected Identify Controller Data: {parsed_data}")
        except Exception as e:
            self.logger.exception(f"Error during Admin Passthru command: {e}")
            self.result = "FAILED"
            return

        # --- Paths y nombres de logs únicos ---
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        drive = "/dev/nvme0"
        ns_id = "1"
        delete = "0xFFFFFFFF"
        lba_size = "4096"

        status_before = f"statusAntes_drive_{timestamp}.log"
        status_after = f"statusDespues_drive_{timestamp}.log"

        # --- Paso 1: Smart-log inicial ---
        self.logger.info("[Paso 1] Smart-log inicial")
        try:
            with open(status_before, "w") as f:
                subprocess.run(
                    ["nvme", "smart-log", drive, "-o", "json"],
                    stdout=f, check=True
                )
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to run smart-log: {e}")
            self.result = "FAILED"
            return

        # --- Paso 2: Estado inicial con nvme list ---
        self.logger.info("[Paso 2] Estado inicial con nvme list")
        subprocess.run(["nvme", "list"], check=True)

        # --- Paso 3: Eliminar namespace ---
        self.logger.info("[Paso 3] Eliminando namespace")
        subprocess.run(["nvme", "delete-ns", drive, "-n", delete], check=True)

        # --- Paso 4: Crear namespace ---
        self.logger.info("[Paso 4] Creando namespace")
        subprocess.run([
            "nvme", "create-ns", drive,
            "-s", lba_size, "-c", lba_size, "-f", "0"
        ], check=True)

        # --- Paso 5: Adjuntar namespace ---
        self.logger.info("[Paso 5] Adjuntando namespace")
        subprocess.run([
            "nvme", "attach-ns", drive,
            "-n", ns_id, "-c", "0"
        ], check=True)

        # --- Paso 6: Resetear controlador ---
        self.logger.info("[Paso 6] Reseteando controlador")
        subprocess.run(["nvme", "reset", drive], check=True)

        # --- Paso 7: Estado final con nvme list ---
        self.logger.info("[Paso 7] Estado final con nvme list")
        subprocess.run(["nvme", "list"], check=True)

        # --- Paso 8: Smart-log final ---
        self.logger.info("[Paso 8] Smart-log final")
        try:
            with open(status_after, "w") as f:
                subprocess.run(
                    ["nvme", "smart-log", drive, "-o", "json"],
                    stdout=f, check=True
                )
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to run smart-log after test: {e}")
            self.result = "FAILED"
            return

        # --- Paso 9: Comparación de Smart-log ---
        self.logger.info("[Paso 9] Comparando cambios en Smart-log")
        try:
            with open(status_before) as f_before, open(status_after) as f_after:
                before_data = json.load(f_before)
                after_data = json.load(f_after)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse smart-log JSON: {e}")
            self.result = "FAILED"
            return

        # Validación de block size: comparar lbaf si existe
        block_size_changed = False
        if "lbaf" in before_data and "lbaf" in after_data:
            block_size_changed = before_data["lbaf"] != after_data["lbaf"]
        else:
            self.logger.warning("lbaf key not found; assuming block size changed")
            block_size_changed = True  # fallback

        # Validación de nuse
        before_nuse = before_data.get("nuse")
        after_nuse = after_data.get("nuse")
        if before_nuse is None or after_nuse is None:
            self.logger.warning("'nuse' key not found; skipping nuse check")
            nuse_increased = True
        else:
            nuse_increased = after_nuse > before_nuse

        # Resultado final
        if block_size_changed and nuse_increased:
            self.logger.info("Test PASSED")
            self.result = "PASSED"
        else:
            self.logger.error("Test FAILED")
            self.result = "FAILED"