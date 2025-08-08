#!/bin/env python3.9
import subprocess

def AdminPassthruTest(logger):
    """
    Executes an NVMe Admin Passthru command to test low-level NVMe functionality.
    """
    nvme_device = "/dev/nvme0n1"
    opcode = "0x06"  # Identify Controller
    cdw10 = "0"
    cdw11 = "0"
    cdw12 = "0"
    data_len = "4096"
    namespace_id = "1"

    cmd = [
        "nvme", "admin-passthru", nvme_device,
        f"--opcode={opcode}",
        f"--cdw10={cdw10}",
        f"--cdw11={cdw11}",
        f"--cdw12={cdw12}",
        f"--namespace-id={namespace_id}",
        f"--data-len={data_len}",
        "--read"
    ]

    logger.debug(f"Parameters: opcode={opcode}, cdw10={cdw10}, cdw11={cdw11}, cdw12={cdw12}, data_len={data_len}")
    logger.info(f"Sending command: {' '.join(cmd)}")

    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        logger.debug(f"Command output:\n{output}")
        return "Command executed successfully"
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing command: {e}")
        logger.debug(f"Error output:\n{e.output}")
        raise