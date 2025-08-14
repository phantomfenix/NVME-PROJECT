#!/bin/env python3.9
from ctypes import Structure, c_uint8, c_uint16, c_uint32, c_uint64
import ctypes
import struct
import fcntl
import logging

class NVMeAdminCmd(Structure):
    _fields_ = [
        ("opcode", c_uint8),
        ("flags", c_uint8),
        ("rsvd1", c_uint16),
        ("nsid", c_uint32),
        ("cdw2", c_uint32),
        ("cdw3", c_uint32),
        ("metadata", c_uint64),
        ("addr", c_uint64),
        ("metadata_len", c_uint32),
        ("data_len", c_uint32),
        ("cdw10", c_uint32),
        ("cdw11", c_uint32),
        ("cdw12", c_uint32),
        ("cdw13", c_uint32),
        ("cdw14", c_uint32),
        ("cdw15", c_uint32),
        ("timeout_ms", c_uint32),
        ("result", c_uint32),
    ]
    

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
    def send_passthru_cmd(self, opcode, data_len=4096, nsid=0, cdw10=0, cdw11=0, cdw12=0, cdw13=0, cdw14=0, cdw15=0):
        """
        Enviar comando NVMe Admin Passthru al dispositivo.
        """
        
        if isinstance(opcode, str):
            opcode = int(opcode, 16)

        
        data_buffer = ctypes.create_string_buffer(data_len)
    
        cmd = NVMeAdminCmd()
        cmd.opcode = opcode
        cmd.flags = 0
        cmd.rsvd1 = 0
        cmd.nsid = nsid
        cmd.cdw2 = 0
        cmd.cdw3 = 0
        cmd.metadata = 0
        cmd.addr = ctypes.cast(data_buffer, ctypes.c_void_p).value
        cmd.metadata_len = 0
        cmd.data_len = data_len
        cmd.cdw10 = cdw10
        cmd.cdw11 = cdw11
        cmd.cdw12 = cdw12
        cmd.cdw13 = cdw13
        cmd.cdw14 = cdw14
        cmd.cdw15 = cdw15
        cmd.timeout_ms = 0
        cmd.result = 0

        self.logger.debug(f"Sending passthru command opcode={opcode:#x} data_len={data_len} nsid={nsid}")
        try:
            with open(self.device_path, 'rb') as f:
                fcntl.ioctl(f.fileno(), NVME_IOCTL_ADMIN_CMD, cmd)
        except OSError as e:
            self.logger.error(f"Failed to send NVMe admin command: {e}")
            return None

        return data_buffer.raw
    
    def parse_smart_log(self, data):
        """Parse NVMe SMART/Health Information Log (512 bytes)"""
        
        if len(data) != 512:
            raise ValueError(f"Expected 512 bytes, got {len(data)} bytes")
        
        smart_data = {}
        
        # Byte 0: Critical Warning
        critical_warning = data[0]
        smart_data["critical_warning"] = {
            "value": critical_warning,
            "flags": {
                "spare_threshold": bool(critical_warning & 0x01),
                "temperature_threshold": bool(critical_warning & 0x02), 
                "reliability_degraded": bool(critical_warning & 0x04),
                "read_only": bool(critical_warning & 0x08),
                "volatile_memory_backup": bool(critical_warning & 0x10)
            }
        }
        
        # Bytes 1-2: Composite Temperature (Kelvin)
        comp_temp = struct.unpack('<H', data[1:3])[0]
        smart_data["composite_temperature"] = {
            "kelvin": comp_temp,
            "celsius": comp_temp - 273.15 if comp_temp != 0 else None
        }
        
        # Byte 3: Available Spare (%)
        smart_data["available_spare"] = data[3]
        
        # Byte 4: Available Spare Threshold (%)
        smart_data["available_spare_threshold"] = data[4]
        
        # Byte 5: Percentage Used (%)
        smart_data["percentage_used"] = data[5]
        
        # Bytes 6-31: Reserved
        
        # Bytes 32-47: Data Units Read
        data_units_read = struct.unpack('<Q', data[32:40])[0]
        smart_data["data_units_read"] = data_units_read
        
        # Bytes 48-63: Data Units Written
        data_units_written = struct.unpack('<Q', data[48:56])[0]
        smart_data["data_units_written"] = data_units_written
        
        # Bytes 64-79: Host Read Commands
        host_reads = struct.unpack('<Q', data[64:72])[0]
        smart_data["host_read_commands"] = host_reads
        
        # Bytes 80-95: Host Write Commands
        host_writes = struct.unpack('<Q', data[80:88])[0]
        smart_data["host_write_commands"] = host_writes
        
        # Bytes 96-111: Controller Busy Time (minutes)
        ctrl_busy = struct.unpack('<Q', data[96:104])[0]
        smart_data["controller_busy_time"] = ctrl_busy
        
        # Bytes 112-127: Power Cycles
        power_cycles = struct.unpack('<Q', data[112:120])[0]
        smart_data["power_cycles"] = power_cycles
        
        # Bytes 128-143: Power On Hours
        power_hours = struct.unpack('<Q', data[128:136])[0]
        smart_data["power_on_hours"] = power_hours
        
        # Bytes 144-159: Unsafe Shutdowns
        unsafe_shutdowns = struct.unpack('<Q', data[144:152])[0]
        smart_data["unsafe_shutdowns"] = unsafe_shutdowns
        
        # Bytes 160-175: Media and Data Integrity Errors
        media_errors = struct.unpack('<Q', data[160:168])[0]
        smart_data["media_errors"] = media_errors
        
        # Bytes 176-191: Number of Error Information Log Entries
        error_entries = struct.unpack('<Q', data[176:184])[0]
        smart_data["error_log_entries"] = error_entries
        
        # Bytes 192-195: Warning Composite Temperature Time
        warning_temp_time = struct.unpack('<I', data[192:196])[0]
        smart_data["warning_temp_time"] = warning_temp_time
        
        # Bytes 196-199: Critical Composite Temperature Time
        critical_temp_time = struct.unpack('<I', data[196:200])[0]
        smart_data["critical_temp_time"] = critical_temp_time
        
        # Bytes 200-215: Temperature Sensors 1-8 (2 bytes each)
        smart_data["temperature_sensors"] = []
        for i in range(8):
            offset = 200 + (i * 2)
            if offset + 1 < len(data):
                temp = struct.unpack('<H', data[offset:offset+2])[0]
                if temp != 0:
                    smart_data["temperature_sensors"].append({
                        f"sensor_{i+1}_kelvin": temp,
                        f"sensor_{i+1}_celsius": temp - 273.15
                    })
        
        # Bytes 216-279: Thermal Management Temperature 1 and 2
        
        # Add calculated fields
        if data_units_read > 0:
            smart_data["total_bytes_read"] = data_units_read * 1000 * 512
            smart_data["total_gb_read"] = round(smart_data["total_bytes_read"] / (1024**3), 2)
        
        if data_units_written > 0:
            smart_data["total_bytes_written"] = data_units_written * 1000 * 512
            smart_data["total_gb_written"] = round(smart_data["total_bytes_written"] / (1024**3), 2)
        
        # Add health summary
        smart_data["health_summary"] = {
            "overall_health": "GOOD" if critical_warning == 0 else "WARNING",
            "temperature_ok": comp_temp < 358 if comp_temp != 0 else None,  # 85°C = 358K
            "spare_ok": smart_data["available_spare"] >= smart_data["available_spare_threshold"],
            "wear_level_ok": smart_data["percentage_used"] < 80
        }
        
        return smart_data

