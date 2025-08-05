import logging
import subprocess
import sys

# Dummy Nvme class for demonstration
class Nvme:
    def __init__(self):
        self.device_path = None

    def set_device_path(self, path):
        self.device_path = path

    def get_smart_log(self):
        try:
            cmd = ['nvme', 'smart-log', self.device_path]
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            return output
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get SMART log: {e.output}")

    def get_info(self):
        try:
            cmd = ['nvme', 'id-ctrl', self.device_path]
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            return output
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get device info: {e.output}")

# AdminPassthruWrapper class
class AdminPassthruWrapper:
    def __init__(self, nvme_device='/dev/nvme0', logger=None):
        self.nvme_device = nvme_device
        self.logger = logger or self._setup_logger()

    def _setup_logger(self):
        logger = logging.getLogger(f'AdminPassthru')
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(ch)
        return logger

    def send_passthru_cmd(self, opcode, cdw10='0', cdw11='0', cdw12='0', data_len=0, namespace_id=1):
        """
        Example passthru command wrapper.
        """
        cmd = [
            'nvme', 'admin-passthru',
            self.nvme_device,
            f'--opcode={opcode}',
            f'--cdw10={cdw10}',
            f'--cdw11={cdw11}',
            f'--cdw12={cdw12}',
            f'--namespace-id={namespace_id}',
            f'--data-len={data_len}',
            '--read'
        ]

        self.logger.info(f"Sending passthru command: {' '.join(cmd)}")

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            self.logger.info("Command executed successfully.")
            self.logger.debug(f"Command output:\n{output}")
            return output

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {e}")
            self.logger.debug(f"Error output:\n{e.output}")
            return None

# TestManager class with admin passthru integration
class TestManager:
    def __init__(self, serial_number, testname, test_class, logger=None):
        self.serial_number = serial_number
        self.testname = testname
        self.nvme = Nvme()
        self.physical_path = None
        self.logger = logger or self._setup_logger()
        self.test = test_class(self.logger, self.nvme)
        self.passthru_wrapper = AdminPassthruWrapper(nvme_device='/dev/nvme0n1', logger=self.logger)

    def _setup_logger(self):
        logger = logging.getLogger(f'TestManager_{self.testname}')
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(ch)
        return logger

    def initialize(self):
        self.logger.info(f"Initializing device with serial number: {self.serial_number}")
        self.physical_path = self.get_device_path()
        if not self.physical_path:
            raise RuntimeError(f"Device with serial {self.serial_number} not found.")
        self.nvme.set_device_path(self.physical_path)
        self.logger.info(f"Device path set to: {self.physical_path}")

    def run(self):
        self.logger.info(f"Running test: {self.testname}")
        self.test.run()

    def drive_check(self, discovery=True):
        self.logger.info("Starting drive check...")
        self.initialize()
        try:
            info = self.nvme.get_info()
            smart = self.nvme.get_smart_log()
        except RuntimeError as e:
            raise RuntimeError(f"Drive check failed: {e}")

        self.logger.debug(f"Drive Info:\n{info}")
        self.logger.debug(f"SMART Log:\n{smart}")

        if "Serial Number" not in info or self.serial_number not in info:
            raise RuntimeError("Serial number mismatch or not found.")

        if discovery:
            self.logger.info("Discovery check passed.")
        else:
            if "critical_warning" in smart and "0x0" not in smart:
                raise RuntimeError("Drive is not healthy.")
            self.logger.info("Health check passed.")

    def get_device_path(self):
        try:
            output = subprocess.check_output(['nvme', 'list'], text=True)
            for line in output.strip().split('\n'):
                if self.serial_number in line:
                    parts = line.split()
                    return parts[0]  # Device path
            return None
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get NVMe list: {e.output}")

    def set_final_result(self):
        self.logger.info("Finalizing test and saving results...")
        self.logger.info(f"Test '{self.testname}' completed successfully.")

    def send_passthru(self):
        self.logger.info("Sending admin passthru command...")
        response = self.passthru_wrapper.send_passthru_cmd(opcode='0x06', data_len=4096)
        if response:
            self.logger.info("Admin passthru command completed.")
        else:
            self.logger.warning("No response from admin passthru command.")

# Example of using TestManager
if __name__ == '__main__':
    serial = "12345678"  # Replace with your drive's real serial
    test = TestManager(serial_number=serial, testname="ExampleTest", test_class=ExampleTest)

    try:
        test.drive_check(discovery=True)
        test.run()
        test.send_passthru()  # Call the passthru method here
        test.set_final_result()
        test.drive_check(discovery=False)
    except Exception as e:
        test.logger.error(f"Test aborted: {e}")
        sys.exit(1)
