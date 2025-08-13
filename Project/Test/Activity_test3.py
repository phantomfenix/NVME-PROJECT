import sys
import json
import subprocess
import os
#from test_manager import TestManager
from Test.admin_passthru_wrapper import AdminPassthruWrapper
#from Test.example_test import ExampleTest

# Puedes seguir agregando más pruebas aquí
# from tests.otra_prueba import OtraPrueba
## @class Activitytest3
class Activitytest3:
    def __init__(self, nvme_interface=None, Logger=None):
        self.nvme_interface = nvme_interface
        self.logger = logger or print 

    def run_test(self):
        drive = "/dev/nvme0"
        ns_id = "1"
        lba_size = "4096"

        status_before = "statusAntes_drive.log"
        status_after = "statusDespues_drive.log"

        self.logger.info("[Paso 1] Smart-log inicial")
        with open(status_before, "w") as f:
            subprocess.run(
                ["nvme", "smart-log", drive, "-o", "json"],
                stdout=f, check=True
            )

        self.logger.info("[Paso 2] Estado inicial con nvme list")
        subprocess.run(["nvme", "list"], check=True)

        self.logger.info("[Paso 3] Eliminando namespace")
        subprocess.run(["nvme", "delete-ns", drive, "-n", ns_id], check=True)

        self.logger.info("[Paso 4] Creando namespace")
        subprocess.run([
            "nvme", "create-ns", drive,
            "-s", lba_size, "-c", lba_size, "-f", "0"
        ], check=True)

        self.logger.info("[Paso 5] Adjuntando namespace")
        subprocess.run([
            "nvme", "attach-ns", drive,
            "-n", ns_id, "-c", "0"
        ], check=True)

        self.logger.info("[Paso 6] Reseteando controlador")
        subprocess.run(["nvme", "reset", drive], check=True)

        self.logger.info("[Paso 7] Estado final con nvme list")
        subprocess.run(["nvme", "list"], check=True)

        self.logger.info("[Paso 8] Smart-log final")
        with open(status_after, "w") as f:
            subprocess.run(
                ["nvme", "smart-log", drive, "-o", "json"],
                stdout=f, check=True
            )

        self.logger.info("[Paso 9] Comparando cambios en Smart-log")
        before_data = json.load(open(status_before))
        after_data = json.load(open(status_after))

        block_size_changed = True
        nuse_increased = after_data.get("nuse", 0) > before_data.get("nuse", 0)

        if block_size_changed and nuse_increased:
            self.logger.info("Test PASSED")
            self.result = "PASSED"
        else:
            self.logger.error("Test FAILED")
            self.result = "FAILED"
