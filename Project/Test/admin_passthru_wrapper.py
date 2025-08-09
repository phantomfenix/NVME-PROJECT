#!/bin/env python3.9
import fcntl
import struct
import os
import logging

# IOCTL para comandos Admin Passthru
NVME_IOCTL_ADMIN_CMD = 0xC0484E41  # tomado de nvme-cli headers

class AdminPassthruWrapper:
    def __init__(self, device_path, logger=None):
        self.device_path = device_path
        self.logger = logger or logging.getLogger(__name__)

    def send_passthru_cmd(self, opcode, data_len=4096, nsid=0):
        """
        Enviar comando NVMe Admin Passthru al dispositivo.
        """
        if isinstance(opcode, str):
            opcode = int(opcode, 16)

        self.logger.debug(f"Opening device {self.device_path} for passthru command...")
        fd = os.open(self.device_path, os.O_RDWR)

        # Buffer de datos
        data_buf = bytearray(data_len)

        # NVMe passthru struct from nvme-cli:
        # struct nvme_admin_cmd {
        #   __u8 opcode;
        #   __u8 flags;
        #   __u16 rsvd1;
        #   __u32 nsid;
        #   __u64 cdw2;
        #   __u64 cdw3;
        #   __u64 metadata;
        #   __u64 addr;
        #   __u32 metadata_len;
        #   __u32 data_len;
        #   __u32 cdw10;
        #   __u32 cdw11;
        #   __u32 cdw12;
        #   __u32 cdw13;
        #   __u32 cdw14;
        #   __u32 cdw15;
        #   __u32 timeout_ms;
        #   __u32 result;
        # };
        # This must be packed according to C struct layout for ioctl.

        fmt = 'B B H I Q Q Q Q I I I I I I I I I I I'
        cmd_struct = struct.pack(
            fmt,
            opcode,        # opcode
            0,             # flags
            0,             # rsvd1
            nsid,          # nsid
            0, 0, 0,       # cdw2, cdw3, metadata
            id(data_buf),  # addr
            0,             # metadata_len
            data_len,      # data_len
            0, 0, 0, 0, 0, 0, 0,  # cdw10..cdw15
            0,             # timeout_ms
            0              # result
        )

        self.logger.debug(f"Sending passthru command opcode={opcode:#x} data_len={data_len} nsid={nsid}")
        try:
            fcntl.ioctl(fd, NVME_IOCTL_ADMIN_CMD, cmd_struct)
            os.close(fd)
            return bytes(data_buf)
        except Exception as e:
            self.logger.error(f"Admin passthru command failed: {e}")
            os.close(fd)
            return None