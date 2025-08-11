#!/bin/env python3.9
import fcntl
import struct
import os
import logging

# Constants for NVMe Admin Passthru
NVME_IOCTL_ADMIN_CMD = 0xC0484E41  # IOCTL code for admin commands (from nvme-cli headers)
## @class AdminPassthruWrapper
#  @brief Encapsulates the sending of NVMe Admin Passthru commands to an NVMe device.
#
#  This class provides a Python interface for sending NVMe administration commands
#  directly to the device using ioctl calls, replicating the behavior of the
#  "nvme_admin_cmd" structure from the nvme-cli package.
class AdminPassthruWrapper:
    ## @brief Class constructor.
    #  @param device_path NVMe device path (e.g., /dev/nvme0).
    #  @param logger Logger instance for logging information and debugging.
    
    def __init__(self, device_path, logger=None):
        self.device_path = device_path
        self.logger = logger or logging.getLogger(__name__)
## @brief Send an NVMe Admin Passthru command to the specified device.
    #
    #  @details
    #  This function packs the parameters into the `nvme_admin_cmd` structure according to
    #  the C format expected by the NVMe driver in Linux and then sends it via `ioctl`.
    #
    #  The command can be used for operations such as:
    #  - Identify Controller (`opcode = 0x06`)
    #  - Identify Namespace
    #  - Other supported NVMe administrative commands
    #
    #  @param opcode NVMe Admin operation code (int or hex string, e.g. `“0x06”`).
    #  @param data_len Expected data buffer size (default 4096 bytes).
    #  @param nsid NVMe namespace ID (0 for controller-level operations).
    #  @return Buffer in bytes with the command response, or None in case of error.
    #
    #  @exception Exception If a failure occurs in the execution of the ioctl.
    #
    #  @code
    #  wrapper = AdminPassthruWrapper(“/dev/nvme0”)
    #  data = wrapper.send_passthru_cmd(0x06)
    #  if data:
    #      print(“Command executed successfully”)
    #  @endcode
    def send_passthru_cmd(self, opcode, data_len=4096, nsid=0):
        """
        Enviar comando NVMe Admin Passthru al dispositivo.
        """
        if isinstance(opcode, str):
            opcode = int(opcode, 16)

        self.logger.debug(f"Opening device {self.device_path} for passthru command...")
        fd = os.open(self.device_path, os.O_RDWR)

        # Allocate buffer
        #! Data buffer to receive the command response
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
#! NVMe Admin Passthru structure based on nvme-cli
        #! @note The structure must be aligned according to the C layout for ioctl.
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