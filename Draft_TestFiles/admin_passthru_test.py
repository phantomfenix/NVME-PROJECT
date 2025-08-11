#!/bin/env python3.9
import subprocess

## @brief Executes an NVMe Admin Passthru command to test low-level NVMe functionality.
#  @param logger Logger object for logging debug messages and information.
#  @return Message indicating the success of the command execution.
#  @throws subprocess.CalledProcessError If the NVMe command fails to execute.

def AdminPassthruTest(logger):
    """
    Executes an NVMe Admin Passthru command to test low-level NVMe functionality.
@details
    This function executes an NVMe Admin Passthru command using the
    command line tool `nvme`. The command used corresponds to the
    “Identify Controller” operation (opcode 0x06) and reads 4096 bytes of data from the specified NVMe controller.
    
    The execution flow is as follows:
    - Defines the command parameters (opcode, cdw10, cdw11, cdw12, data size, etc.).
    - Build the list of arguments for the `nvme admin-passthru` command.
    - Record the parameters and the command to be executed in the logger.
    - Execute the command using `subprocess.check_output`.
    - Capture and record any errors in the execution.

    Example of generated command:
    @code
    nvme admin-passthru /dev/nvme0n1 --opcode=0x06 --cdw10=0 --cdw11=0 --cdw12=0 --namespace-id=1 --data-len=4096 --read
    @endcode
  
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