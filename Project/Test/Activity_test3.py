#!/bin/env python3.9
import struct
import json
import subprocess
import tempfile
import os
from datetime import datetime
from Test.admin_passthru_wrapper import AdminPassthruWrapper

class Activitytest3:
    def __init__(self, nvme_interface, logger):
        self.nvme_interface = nvme_interface
        self.logger = logger
        self.result = "NOT RUN"

    def parse_identify_namespace(self, data_bytes):
        """Parses Identify Namespace data structure from NVMe spec."""
        nsize = struct.unpack_from("<Q", data_bytes, 0)[0]    # bytes 0-7
        ncap = struct.unpack_from("<Q", data_bytes, 8)[0]     # bytes 8-15
        nuse = struct.unpack_from("<Q", data_bytes, 16)[0]    # bytes 16-23
        flbas = data_bytes[26]                                # byte 26
        dps = data_bytes[30]                                  # byte 30
        lbaf = flbas & 0x0F                                   # bits 0-3 de flbas
        return {
            "nsize": nsize,
            "ncap": ncap,
            "nuse": nuse,
            "flbas": flbas,
            "lbaf": lbaf,
            "dps": dps
        }

    def run(self):
        self.logger.info("Starting Activitytest3 with Admin Passthru...")

        drive = "/dev/nvme0"
        ns_id = "1"  # namespace ID
        delete_all = "0xFFFFFFFF"
        # Definiciones esperadas
        nsize_expected = 4096  # en LBAs
        ncap_expected = 4096
        lbaf_expected = 0      # formato index 0 para 4KiB
        dps_expected = 0       # sin protección

        # --- Paso 1: ID-NS inicial vía Admin Passthru ---
        try:
            self.logger.debug("Getting initial Identify Namespace via Admin Passthru...")
            id_ns_before_bytes = self.nvme_interface.send_passthru_cmd(
                opcode='0x06',
                data_len=4096,
                nsid=int(ns_id)
            )
            with open("id_ns_before.bin", "wb") as f:
                f.write(id_ns_before_bytes)
            id_ns_before = self.parse_identify_namespace(id_ns_before_bytes)
            self.logger.info(f"Initial ID-NS: {id_ns_before}")
        except Exception as e:
            self.logger.exception(f"Error getting initial ID-NS: {e}")
            self.result = "FAILED"
            return

        # --- Paso 2: Smart-log inicial ---
        status_before = "statusAntes.json"
        self.logger.info("[Paso 2] Smart-log inicial")
        subprocess.run(["nvme", "smart-log", drive, "-o", "json"], stdout=open(status_before, "w"), check=True)

        # --- Paso 3: Eliminar namespace ---
        self.logger.info("[Paso 3] Eliminando namespace")
        subprocess.run(["nvme", "delete-ns", drive, "-n", delete_all], check=True)

        # --- Paso 4: Crear namespace ---
        self.logger.info("[Paso 4] Creando namespace")
        subprocess.run([
            "nvme", "create-ns", drive,
            "-s", str(nsize_expected),
            "-c", str(ncap_expected),
            "-f", str(lbaf_expected)
        ], check=True)

        # --- Paso 5: Adjuntar namespace ---
        self.logger.info("[Paso 5] Adjuntando namespace")
        subprocess.run(["nvme", "attach-ns", drive, "-n", ns_id, "-c", "0"], check=True)

        # --- Paso 6: Cambiar block size (Format) ---
        self.logger.info("[Paso 6] Cambiando block size con nvme format")
        subprocess.run([
            "nvme", "format", f"{drive}n{ns_id}",
            "-l", str(lbaf_expected),
            "-f", "0"
        ], check=True)

        # --- Paso 7: Ejecutar escritura para cambiar nuse ---
        self.logger.info("[Paso 7] Ejecutando nvme write para modificar nuse")
        
        tmp = tempfile.NamedTemporaryFile(delete=False)
        try:
           tmp.write(b'\x00' * 8192)  # 8 KiB de ceros
           tmp.flush()
           tmp.close()  # cerrar antes de pasar al comando
           subprocess.run([
               "nvme", "write", f"{drive}n{ns_id}",
               "-s", "0",                # primer bloque
               "-c", "2",                # escribir 1 bloque de 4KiB
               "-d", tmp.name,
               "-z", "8192"
           ], check=True)
        finally:
           os.unlink(tmp.name)

        # --- Paso 8: Smart-log final ---
        status_after = "statusDespues.json"
        self.logger.info("[Paso 8] Smart-log final")
        subprocess.run(["nvme", "smart-log", drive, "-o", "json"], stdout=open(status_after, "w"), check=True)

        # --- Paso 9: ID-NS final vía Admin Passthru ---
        try:
            self.logger.debug("Getting final Identify Namespace via Admin Passthru...")
            id_ns_after_bytes = self.nvme_interface.send_passthru_cmd(
                opcode='0x06',
                data_len=4096,
                nsid=int(ns_id)
            )
            with open("id_ns_after.bin", "wb") as f:
                f.write(id_ns_after_bytes)
            id_ns_after = self.parse_identify_namespace(id_ns_after_bytes)
            self.logger.info(f"Final ID-NS: {id_ns_after}")
        except Exception as e:
            self.logger.exception(f"Error getting final ID-NS: {e}")
            self.result = "FAILED"
            return

        # --- Paso 10: Validaciones ---
        self.logger.info("[Paso 10] Validando resultados")

        # Validación block size (lbaf y dps)
        blocksize_ok = (
            id_ns_after["lbaf"] == lbaf_expected and
            id_ns_after["dps"] == dps_expected
        )

        # Validación nuse (debe aumentar)
        nuse_ok = id_ns_after["nuse"] > id_ns_before["nuse"]

        # Validación nsize y ncap
        nsize_ok = id_ns_after["nsize"] == nsize_expected
        ncap_ok = id_ns_after["ncap"] == ncap_expected

        if blocksize_ok and nuse_ok and nsize_ok and ncap_ok:
            self.result = "PASSED"
            self.logger.info("Test PASSED")
        else:
            self.result = "FAILED"
            self.logger.error(f"Test FAILED - blocksize_ok={blocksize_ok}, nuse_ok={nuse_ok}, nsize_ok={nsize_ok}, ncap_ok={ncap_ok}")
